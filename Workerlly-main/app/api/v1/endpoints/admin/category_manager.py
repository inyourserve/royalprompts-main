# endpoints/admin/category_manager.py
import uuid
from datetime import datetime
from typing import Optional

from bson import ObjectId
from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    UploadFile,
    File,
    Form,
    Path,
)

from app.db.models.database import motor_db
from app.utils.admin_roles import admin_permission_required
from app.utils.mongo_encoder import convert_objectid_to_str
from app.utils.s3_manager import (
    upload_file_to_s3,
    delete_file_from_s3,
)

router = APIRouter()

# Constants for module and actions
MODULE = "categories"
ACTIONS = {"VIEW": "read", "CREATE": "create", "UPDATE": "update", "DELETE": "delete"}


@router.get("/categories")
async def get_categories(
        current_user=Depends(admin_permission_required(MODULE, ACTIONS["VIEW"]))
):
    """Fetch all categories without pagination"""
    try:
        query_filter = {"deleted_at": None}

        categories = (
            await motor_db.categories.find(query_filter)
            .sort("order", 1)
            .to_list(None)
        )

        processed_categories = []
        for cat in categories:
            processed_cat = convert_objectid_to_str(cat)
            # Only include non-deleted subcategories
            processed_cat["sub_categories"] = [
                convert_objectid_to_str(sub)
                for sub in processed_cat.get("sub_categories", [])
                if sub.get("deleted_at") is None
            ]
            processed_categories.append(processed_cat)

        return {
            "status": "success",
            "data": processed_categories,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/categories")
async def create_category(
        name: str = Form(..., min_length=2, max_length=100),
        thumbnail: UploadFile = File(...),
        description: Optional[str] = Form(None),
        current_user=Depends(admin_permission_required(MODULE, ACTIONS["CREATE"])),
):
    """Create a new category with file upload to S3"""
    try:
        # Check for existing non-deleted category with same name
        existing_category = await motor_db.categories.find_one(
            {"name": name, "deleted_at": None}
        )
        if existing_category:
            raise HTTPException(
                status_code=400, detail="Category with this name already exists"
            )

        # Generate a unique filename for S3
        filename = f"{uuid.uuid4()}-{thumbnail.filename}"

        # Upload thumbnail to S3
        s3_url = upload_file_to_s3(thumbnail.file, "public/categories", filename)
        if not s3_url:
            raise HTTPException(status_code=500, detail="Failed to upload image to S3")

        # Prepare category document with timestamps
        category = {
            "name": name,
            "description": description,
            "thumbnail": s3_url,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "deleted_at": None,
            "sub_categories": [],
            "order": await motor_db.categories.count_documents({"deleted_at": None}) + 1,
        }

        result = await motor_db.categories.insert_one(category)
        category["_id"] = str(result.inserted_id)

        return {
            "status": "success",
            "data": category,
            "message": "Category created successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/categories/{category_id}")
async def update_category(
        category_id: str = Path(..., description="The ID of the category to update"),
        order: Optional[int] = Form(None),
        name: Optional[str] = Form(None, min_length=2, max_length=100),
        thumbnail: Optional[UploadFile] = File(None),
        description: Optional[str] = Form(None),
        current_user=Depends(admin_permission_required(MODULE, ACTIONS["UPDATE"])),
):
    """Update an existing category with optional file upload"""
    try:
        if not ObjectId.is_valid(category_id):
            raise HTTPException(status_code=400, detail="Invalid category ID")

        # Check if category exists and is not deleted
        current_doc = await motor_db.categories.find_one(
            {"_id": ObjectId(category_id), "deleted_at": None}
        )
        if not current_doc:
            raise HTTPException(
                status_code=404, detail="Category not found or is deleted"
            )

        update_data = {"updated_at": datetime.utcnow()}

        if order is not None:
            update_data["order"] = int(order)

        if name is not None:
            existing_category = await motor_db.categories.find_one(
                {
                    "name": name,
                    "deleted_at": None,
                    "_id": {"$ne": ObjectId(category_id)},
                }
            )
            if existing_category:
                raise HTTPException(
                    status_code=400, detail="Category with this name already exists"
                )
            update_data["name"] = name

        if description is not None:
            update_data["description"] = description

        # Handle file upload if a new thumbnail is provided
        # Only process thumbnail if it's an actual file, not just an empty field
        if thumbnail and thumbnail.filename:
            # Generate a unique filename
            filename = f"{uuid.uuid4()}-{thumbnail.filename}"

            # Upload to S3
            s3_url = upload_file_to_s3(thumbnail.file, "public/categories", filename)
            if not s3_url:
                raise HTTPException(status_code=500, detail="Failed to upload image to S3")

            # Delete the old thumbnail from S3 if it exists
            if current_doc.get("thumbnail"):
                delete_file_from_s3(current_doc["thumbnail"])

            update_data["thumbnail"] = s3_url

        result = await motor_db.categories.update_one(
            {"_id": ObjectId(category_id), "deleted_at": None}, {"$set": update_data}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Category not found")

        updated_doc = await motor_db.categories.find_one({"_id": ObjectId(category_id)})
        processed_category = convert_objectid_to_str(updated_doc)

        return {
            "status": "success",
            "data": processed_category,
            "message": "Category updated successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/categories/{category_id}")
async def delete_category(
        category_id: str = Path(..., description="The ID of the category to delete"),
        current_user=Depends(admin_permission_required(MODULE, ACTIONS["DELETE"])),
):
    """Soft delete a category and handle S3 file deletion"""
    try:
        if not ObjectId.is_valid(category_id):
            raise HTTPException(status_code=400, detail="Invalid category ID")

        # Check for associated active jobs or workers
        jobs_count = await motor_db.jobs.count_documents(
            {"category_id": category_id, "deleted_at": None}
        )
        workers_count = await motor_db.workers.count_documents(
            {"category_id": category_id, "deleted_at": None}
        )

        if jobs_count > 0 or workers_count > 0:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete category with associated jobs or workers",
            )

        # Get category data before deletion to handle S3 cleanup
        category = await motor_db.categories.find_one({"_id": ObjectId(category_id), "deleted_at": None})
        if not category:
            raise HTTPException(status_code=404, detail="Category not found or already deleted")

        # Perform soft delete
        current_time = datetime.utcnow()
        result = await motor_db.categories.update_one(
            {"_id": ObjectId(category_id), "deleted_at": None},
            {
                "$set": {
                    "deleted_at": current_time,
                    "updated_at": current_time,
                    "sub_categories.$[].deleted_at": current_time,
                    "sub_categories.$[].updated_at": current_time,
                }
            },
        )

        if result.modified_count == 0:
            raise HTTPException(
                status_code=404, detail="Category not found or already deleted"
            )

        # Optional: Delete files from S3 (uncomment if you want hard delete of files)
        # if category.get("thumbnail"):
        #     delete_file_from_s3(category["thumbnail"])
        # delete_folder_from_s3(f"public/subcategories/{category_id}")

        # Reorder remaining categories
        remaining_categories = (
            await motor_db.categories.find({"deleted_at": None})
            .sort("order", 1)
            .to_list(None)
        )

        for index, cat in enumerate(remaining_categories, 1):
            await motor_db.categories.update_one(
                {"_id": cat["_id"]},
                {"$set": {"order": index, "updated_at": current_time}},
            )

        return {"status": "success", "message": "Category deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/categories/{category_id}/subcategories")
async def create_subcategory(
        category_id: str = Path(..., description="The ID of the parent category"),
        name: str = Form(..., min_length=2, max_length=100),
        thumbnail: UploadFile = File(...),
        current_user=Depends(admin_permission_required(MODULE, ACTIONS["CREATE"])),
):
    """Add a subcategory to an existing category with file upload"""
    try:
        if not ObjectId.is_valid(category_id):
            raise HTTPException(status_code=400, detail="Invalid category ID")

        # Generate a unique filename
        filename = f"{uuid.uuid4()}-{thumbnail.filename}"

        # Upload to S3
        s3_url = upload_file_to_s3(
            thumbnail.file, f"public/subcategories/{category_id}", filename
        )
        if not s3_url:
            raise HTTPException(status_code=500, detail="Failed to upload image to S3")

        # Get category to determine next order value
        category = await motor_db.categories.find_one(
            {"_id": ObjectId(category_id), "deleted_at": None}
        )

        if not category:
            raise HTTPException(status_code=404, detail="Category not found or is deleted")

        # Calculate the next order value
        subcategories = category.get("sub_categories", [])
        active_subcategories = [sub for sub in subcategories if sub.get("deleted_at") is None]
        next_order = len(active_subcategories) + 1

        current_time = datetime.utcnow()
        subcategory = {
            "id": ObjectId(),
            "name": name,
            "thumbnail": s3_url,
            "created_at": current_time,
            "updated_at": current_time,
            "deleted_at": None,
            "order": next_order
        }

        result = await motor_db.categories.update_one(
            {"_id": ObjectId(category_id), "deleted_at": None},
            {
                "$push": {"sub_categories": subcategory},
                "$set": {"updated_at": current_time},
            },
        )

        if result.modified_count == 0:
            raise HTTPException(
                status_code=404, detail="Parent category not found or is deleted"
            )

        return {
            "status": "success",
            "data": convert_objectid_to_str(subcategory),
            "message": "Subcategory created successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# @router.post("/categories/{category_id}/subcategories")
# async def create_subcategory(
#         category_id: str = Path(..., description="The ID of the parent category"),
#         name: str = Form(..., min_length=2, max_length=100),
#         thumbnail: UploadFile = File(...),
#         current_user=Depends(admin_permission_required(MODULE, ACTIONS["CREATE"])),
# ):
#     """Add a subcategory to an existing category with file upload"""
#     try:
#         if not ObjectId.is_valid(category_id):
#             raise HTTPException(status_code=400, detail="Invalid category ID")
#
#         # Generate a unique filename
#         filename = f"{uuid.uuid4()}-{thumbnail.filename}"
#
#         # Upload to S3
#         s3_url = upload_file_to_s3(
#             thumbnail.file, f"public/subcategories/{category_id}", filename
#         )
#         if not s3_url:
#             raise HTTPException(status_code=500, detail="Failed to upload image to S3")
#
#         current_time = datetime.utcnow()
#         subcategory = {
#             "id": ObjectId(),
#             "name": name,
#             "thumbnail": s3_url,
#             "created_at": current_time,
#             "updated_at": current_time,
#             "deleted_at": None,
#         }
#
#         result = await motor_db.categories.update_one(
#             {"_id": ObjectId(category_id), "deleted_at": None},
#             {
#                 "$push": {"sub_categories": subcategory},
#                 "$set": {"updated_at": current_time},
#             },
#         )
#
#         if result.modified_count == 0:
#             raise HTTPException(
#                 status_code=404, detail="Parent category not found or is deleted"
#             )
#
#         return {
#             "status": "success",
#             "data": convert_objectid_to_str(subcategory),
#             "message": "Subcategory created successfully",
#         }
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


@router.patch("/categories/{category_id}/subcategories/{subcategory_id}")
async def update_subcategory(
        category_id: str = Path(..., description="The ID of the parent category"),
        subcategory_id: str = Path(..., description="The ID of the subcategory to update"),
        name: Optional[str] = Form(None, min_length=2, max_length=100),
        thumbnail: Optional[UploadFile] = File(None),
        current_user=Depends(admin_permission_required(MODULE, ACTIONS["UPDATE"])),
):
    """Update an existing subcategory with optional file upload"""
    try:
        if not ObjectId.is_valid(category_id) or not ObjectId.is_valid(subcategory_id):
            raise HTTPException(status_code=400, detail="Invalid ID format")

        # Find the category and subcategory
        category = await motor_db.categories.find_one(
            {"_id": ObjectId(category_id), "deleted_at": None}
        )
        if not category:
            raise HTTPException(status_code=404, detail="Category not found or is deleted")

        # Find the subcategory within the category
        subcategory = next(
            (sub for sub in category.get("sub_categories", [])
             if str(sub["id"]) == subcategory_id and sub.get("deleted_at") is None),
            None
        )
        if not subcategory:
            raise HTTPException(status_code=404, detail="Subcategory not found or is deleted")

        # Prepare update data
        update_data = {}
        current_time = datetime.utcnow()

        # Set name if provided
        if name is not None:
            update_data["sub_categories.$.name"] = name

        # Always update the timestamp
        update_data["sub_categories.$.updated_at"] = current_time
        update_data["updated_at"] = current_time

        # Handle file upload if a new thumbnail is provided
        # Only process thumbnail if it's an actual file, not just an empty field
        if thumbnail and thumbnail.filename:
            # Generate a unique filename
            filename = f"{uuid.uuid4()}-{thumbnail.filename}"

            # Upload to S3
            s3_url = upload_file_to_s3(
                thumbnail.file, f"public/subcategories/{category_id}", filename
            )
            if not s3_url:
                raise HTTPException(status_code=500, detail="Failed to upload image to S3")

            # Delete the old thumbnail from S3 if it exists
            if subcategory.get("thumbnail"):
                delete_file_from_s3(subcategory["thumbnail"])

            update_data["sub_categories.$.thumbnail"] = s3_url

        # Update the subcategory
        result = await motor_db.categories.update_one(
            {
                "_id": ObjectId(category_id),
                "sub_categories.id": ObjectId(subcategory_id),
                "deleted_at": None,
                "sub_categories.deleted_at": None
            },
            {"$set": update_data}
        )

        if result.modified_count == 0:
            raise HTTPException(
                status_code=404,
                detail="Failed to update subcategory. Either category or subcategory not found or is deleted."
            )

        # Get the updated document
        updated_doc = await motor_db.categories.find_one({"_id": ObjectId(category_id)})
        updated_subcategory = next(
            (sub for sub in updated_doc.get("sub_categories", []) if str(sub["id"]) == subcategory_id),
            None
        )

        return {
            "status": "success",
            "data": convert_objectid_to_str(updated_subcategory),
            "message": "Subcategory updated successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/categories/{category_id}/subcategories/{subcategory_id}")
async def delete_subcategory(
        category_id: str = Path(..., description="The ID of the parent category"),
        subcategory_id: str = Path(..., description="The ID of the subcategory to delete"),
        current_user=Depends(admin_permission_required(MODULE, ACTIONS["DELETE"])),
):
    """Soft delete a subcategory and handle S3 file deletion"""
    try:
        if not ObjectId.is_valid(category_id) or not ObjectId.is_valid(subcategory_id):
            raise HTTPException(status_code=400, detail="Invalid ID format")

        # Find the category and subcategory
        category = await motor_db.categories.find_one(
            {"_id": ObjectId(category_id), "deleted_at": None}
        )
        if not category:
            raise HTTPException(status_code=404, detail="Category not found or is deleted")

        # Find the subcategory within the category
        subcategory = next(
            (sub for sub in category.get("sub_categories", [])
             if str(sub["id"]) == subcategory_id and sub.get("deleted_at") is None),
            None
        )
        if not subcategory:
            raise HTTPException(status_code=404, detail="Subcategory not found or is deleted")

        # Check for associated active jobs or workers
        jobs_count = await motor_db.jobs.count_documents(
            {"subcategory_id": subcategory_id, "deleted_at": None}
        )
        workers_count = await motor_db.workers.count_documents(
            {"subcategory_id": subcategory_id, "deleted_at": None}
        )

        if jobs_count > 0 or workers_count > 0:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete subcategory with associated jobs or workers",
            )

        # Perform soft delete
        current_time = datetime.utcnow()
        result = await motor_db.categories.update_one(
            {
                "_id": ObjectId(category_id),
                "sub_categories.id": ObjectId(subcategory_id),
                "deleted_at": None
            },
            {
                "$set": {
                    "sub_categories.$.deleted_at": current_time,
                    "sub_categories.$.updated_at": current_time,
                    "updated_at": current_time
                }
            }
        )

        if result.modified_count == 0:
            raise HTTPException(
                status_code=404,
                detail="Failed to delete subcategory. Either category or subcategory not found or is deleted."
            )

        # Optional: Delete files from S3 (uncomment if you want hard delete of files)
        # if subcategory.get("thumbnail"):
        #     delete_file_from_s3(subcategory["thumbnail"])

        return {
            "status": "success",
            "message": "Subcategory deleted successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/categories/{category_id}/subcategories/{subcategory_id}/order")
async def update_subcategory_order(
        category_id: str = Path(..., description="The ID of the parent category"),
        subcategory_id: str = Path(..., description="The ID of the subcategory to update"),
        order: int = Form(..., description="New order value"),
        current_user=Depends(admin_permission_required(MODULE, ACTIONS["UPDATE"])),
):
    """Update the order of a subcategory within its parent category"""
    try:
        if not ObjectId.is_valid(category_id) or not ObjectId.is_valid(subcategory_id):
            raise HTTPException(status_code=400, detail="Invalid ID format")

        # Find the category and subcategory
        category = await motor_db.categories.find_one(
            {"_id": ObjectId(category_id), "deleted_at": None}
        )
        if not category:
            raise HTTPException(status_code=404, detail="Category not found or is deleted")

        # Find the subcategory within the category
        subcategory = next(
            (sub for sub in category.get("sub_categories", [])
             if str(sub["id"]) == subcategory_id and sub.get("deleted_at") is None),
            None
        )
        if not subcategory:
            raise HTTPException(status_code=404, detail="Subcategory not found or is deleted")

        current_time = datetime.utcnow()

        # Update the subcategory's order
        result = await motor_db.categories.update_one(
            {
                "_id": ObjectId(category_id),
                "sub_categories.id": ObjectId(subcategory_id),
                "deleted_at": None,
                "sub_categories.deleted_at": None
            },
            {
                "$set": {
                    "sub_categories.$.order": order,
                    "sub_categories.$.updated_at": current_time,
                    "updated_at": current_time
                }
            }
        )

        if result.modified_count == 0:
            raise HTTPException(
                status_code=404,
                detail="Failed to update subcategory order. Either category or subcategory not found or is deleted."
            )

        # Get the updated document
        updated_doc = await motor_db.categories.find_one({"_id": ObjectId(category_id)})
        updated_subcategory = next(
            (sub for sub in updated_doc.get("sub_categories", []) if str(sub["id"]) == subcategory_id),
            None
        )

        return {
            "status": "success",
            "data": convert_objectid_to_str(updated_subcategory),
            "message": "Subcategory order updated successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
