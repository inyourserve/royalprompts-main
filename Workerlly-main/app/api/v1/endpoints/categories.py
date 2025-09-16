from fastapi import APIRouter

from app.db.models.database import db

router = APIRouter()


@router.get("/categories")
async def get_categories():
    categories = list(
        db.categories.find({"deleted_at": None}).sort(
            [("order", 1)]
        )  # Explicit sorting
    )

    for category in categories:
        category["_id"] = str(category["_id"])  # Convert ObjectId to string
        for sub_category in category.get("sub_categories", []):
            sub_category["id"] = str(sub_category["id"])

    return {"categories": categories}

# @router.post("/categories")
# async def create_category(
#         name: str = Form(...),
#         thumbnail: UploadFile = File(...),
# ):
#     # Generate a unique filename
#     filename = f"{uuid.uuid4()}-{thumbnail.filename}"
#
#     # Upload to S3 (synchronous operation)
#     s3_url = upload_file_to_s3(thumbnail.file, "public/categories", filename)
#
#     if not s3_url:
#         raise HTTPException(status_code=500, detail="Failed to upload image to S3")
#
#     # Create category document
#     category = {"name": name, "thumbnail": s3_url, "sub_categories": []}
#
#     # Insert into MongoDB (it will automatically create the _id)
#     result = db.categories.insert_one(category)
#
#     return {"id": str(result.inserted_id), "message": "Category created successfully"}
#
#
# @router.post("/subcategories")
# async def create_subcategory(
#         category_id: str = Form(...),
#         name: str = Form(...),
#         thumbnail: UploadFile = File(...),
# ):
#     # Generate a unique filename
#     filename = f"{uuid.uuid4()}-{thumbnail.filename}"
#
#     # Upload to S3 (synchronous operation)
#     s3_url = upload_file_to_s3(
#         thumbnail.file, f"public/subcategories/{category_id}", filename
#     )
#
#     if not s3_url:
#         raise HTTPException(status_code=500, detail="Failed to upload image to S3")
#
#     # Create subcategory document
#     subcategory = {"id": ObjectId(), "name": name, "thumbnail": s3_url}
#
#     # Update the category in MongoDB
#     result = db.categories.update_one(
#         {"_id": ObjectId(category_id)}, {"$push": {"sub_categories": subcategory}}
#     )
#
#     if result.modified_count == 0:
#         raise HTTPException(status_code=404, detail="Category not found")
#
#     return {"message": "Subcategory created successfully"}
#
#
# @router.delete("/categories/{category_id}")
# async def delete_category(category_id: str):
#     # Validate category_id
#     if not ObjectId.is_valid(category_id):
#         raise HTTPException(status_code=400, detail="Invalid category ID")
#
#     # Find the category in MongoDB
#     category = db.categories.find_one({"_id": ObjectId(category_id)})
#     if not category:
#         raise HTTPException(status_code=404, detail="Category not found")
#
#     # Delete the category document from MongoDB first
#     result = db.categories.delete_one({"_id": ObjectId(category_id)})
#     if result.deleted_count == 0:
#         raise HTTPException(
#             status_code=500, detail="Failed to delete category from MongoDB"
#         )
#
#     # Proceed to delete the category thumbnail from S3
#     category_thumbnail_key = category["thumbnail"]
#     delete_file_from_s3(category_thumbnail_key)
#
#     # Proceed to delete the folder for subcategories in S3
#     delete_folder_from_s3(f"public/subcategories/{category_id}")
#
#     return {"message": "Category and associated subcategories deleted successfully"}
#
#
# @router.delete("/subcategories/{category_id}/{subcategory_id}")
# async def delete_subcategory(category_id: str, subcategory_id: str):
#     # Validate IDs
#     if not ObjectId.is_valid(category_id) or not ObjectId.is_valid(subcategory_id):
#         raise HTTPException(
#             status_code=400, detail="Invalid category or subcategory ID"
#         )
#
#     # Find the category in MongoDB
#     category = db.categories.find_one({"_id": ObjectId(category_id)})
#     if not category:
#         raise HTTPException(status_code=404, detail="Category not found")
#
#     # Find the subcategory in the category
#     subcategory = next(
#         (
#             sub
#             for sub in category.get("sub_categories", [])
#             if str(sub["id"]) == subcategory_id
#         ),
#         None,
#     )
#     if not subcategory:
#         raise HTTPException(status_code=404, detail="Subcategory not found")
#
#     # Remove the subcategory from the category document in MongoDB first
#     result = db.categories.update_one(
#         {"_id": ObjectId(category_id)},
#         {"$pull": {"sub_categories": {"id": ObjectId(subcategory_id)}}},
#     )
#     if result.modified_count == 0:
#         raise HTTPException(
#             status_code=500, detail="Failed to delete subcategory from MongoDB"
#         )
#
#     # Proceed to delete the subcategory thumbnail from S3
#     subcategory_thumbnail_key = subcategory["thumbnail"]
#     delete_file_from_s3(subcategory_thumbnail_key)
#
#     return {"message": "Subcategory deleted successfully"}
#
#
# @router.put("/categories/{category_id}")
# async def edit_category(
#         category_id: str,
#         name: str = Form(...),
#         thumbnail: UploadFile = File(None),
# ):
#     # Validate category_id
#     if not ObjectId.is_valid(category_id):
#         raise HTTPException(status_code=400, detail="Invalid category ID")
#
#     # Find the category in MongoDB
#     category = db.categories.find_one({"_id": ObjectId(category_id)})
#     if not category:
#         raise HTTPException(status_code=404, detail="Category not found")
#
#     # Prepare update data
#     update_data = {"name": name}
#
#     # If a new thumbnail is provided, upload it and update the URL
#     if thumbnail:
#         # Generate a unique filename
#         filename = f"{uuid.uuid4()}-{thumbnail.filename}"
#
#         # Upload to S3 (synchronous operation)
#         s3_url = upload_file_to_s3(thumbnail.file, "public/categories", filename)
#
#         if not s3_url:
#             raise HTTPException(status_code=500, detail="Failed to upload image to S3")
#
#         # Delete the old thumbnail from S3
#         delete_file_from_s3(category["thumbnail"])
#
#         update_data["thumbnail"] = s3_url
#
#     # Update the category in MongoDB
#     result = db.categories.update_one(
#         {"_id": ObjectId(category_id)}, {"$set": update_data}
#     )
#
#     if result.modified_count == 0:
#         raise HTTPException(status_code=500, detail="Failed to update category")
#
#     return {"message": "Category updated successfully"}
#
#
# @router.put("/subcategories/{category_id}/{subcategory_id}")
# async def edit_subcategory(
#         category_id: str,
#         subcategory_id: str,
#         name: str = Form(...),
#         thumbnail: UploadFile = File(None),
# ):
#     # Validate IDs
#     if not ObjectId.is_valid(category_id) or not ObjectId.is_valid(subcategory_id):
#         raise HTTPException(
#             status_code=400, detail="Invalid category or subcategory ID"
#         )
#
#     # Find the category in MongoDB
#     category = db.categories.find_one({"_id": ObjectId(category_id)})
#     if not category:
#         raise HTTPException(status_code=404, detail="Category not found")
#
#     # Find the subcategory in the category
#     subcategory = next(
#         (
#             sub
#             for sub in category.get("sub_categories", [])
#             if str(sub["id"]) == subcategory_id
#         ),
#         None,
#     )
#     if not subcategory:
#         raise HTTPException(status_code=404, detail="Subcategory not found")
#
#     # Prepare update data
#     update_data = {"sub_categories.$.name": name}
#
#     # If a new thumbnail is provided, upload it and update the URL
#     if thumbnail:
#         # Generate a unique filename
#         filename = f"{uuid.uuid4()}-{thumbnail.filename}"
#
#         # Upload to S3 (synchronous operation)
#         s3_url = upload_file_to_s3(
#             thumbnail.file, f"public/subcategories/{category_id}", filename
#         )
#
#         if not s3_url:
#             raise HTTPException(status_code=500, detail="Failed to upload image to S3")
#
#         # Delete the old thumbnail from S3
#         delete_file_from_s3(subcategory["thumbnail"])
#
#         update_data["sub_categories.$.thumbnail"] = s3_url
#
#     # Update the subcategory in MongoDB
#     result = db.categories.update_one(
#         {"_id": ObjectId(category_id), "sub_categories.id": ObjectId(subcategory_id)},
#         {"$set": update_data},
#     )
#
#     if result.modified_count == 0:
#         raise HTTPException(status_code=500, detail="Failed to update subcategory")
#
#     return {"message": "Subcategory updated successfully"}
