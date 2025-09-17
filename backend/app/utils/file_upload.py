import os
import uuid
import shutil
from typing import Optional
from fastapi import UploadFile, HTTPException, status
from PIL import Image
import aiofiles

from app.core.config import settings


class FileUploadManager:
    """File upload management utility"""
    
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        self.max_file_size = settings.MAX_FILE_SIZE
        self.allowed_types = settings.ALLOWED_FILE_TYPES
        
        # Create upload directory if it doesn't exist
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(f"{self.upload_dir}/images", exist_ok=True)
        os.makedirs(f"{self.upload_dir}/thumbnails", exist_ok=True)
        os.makedirs(f"{self.upload_dir}/temp", exist_ok=True)
    
    async def validate_file(self, file: UploadFile) -> None:
        """Validate uploaded file"""
        # Check file size
        if file.size and file.size > self.max_file_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum allowed size of {self.max_file_size} bytes"
            )
        
        # Check file type
        if file.content_type not in self.allowed_types:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"File type {file.content_type} is not allowed"
            )
    
    def generate_filename(self, original_filename: str) -> str:
        """Generate unique filename"""
        file_extension = os.path.splitext(original_filename)[1].lower()
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        return unique_filename
    
    async def save_file(self, file: UploadFile, subfolder: str = "images") -> str:
        """Save uploaded file to disk"""
        await self.validate_file(file)
        
        filename = self.generate_filename(file.filename)
        file_path = os.path.join(self.upload_dir, subfolder, filename)
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        return filename
    
    async def save_image(self, file: UploadFile) -> dict:
        """Save image file with thumbnail generation"""
        await self.validate_file(file)
        
        filename = self.generate_filename(file.filename)
        image_path = os.path.join(self.upload_dir, "images", filename)
        
        # Save original image
        async with aiofiles.open(image_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Validate that the saved file is actually a valid image
        try:
            with Image.open(image_path) as img:
                # Verify it's a valid image by trying to load it
                img.verify()
        except Exception as e:
            # If it's not a valid image, delete the file and raise an error
            if os.path.exists(image_path):
                os.remove(image_path)
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid image file: {str(e)}"
            )
        
        # Reopen the image to get dimensions (verify() closes the file)
        try:
            with Image.open(image_path) as img:
                width, height = img.size
        except Exception as e:
            # If we can't get dimensions, use defaults
            width, height = None, None
        
        # Generate thumbnail
        thumbnail_filename = await self.generate_thumbnail(image_path, filename)
        
        return {
            "filename": filename,
            "url": f"/{self.upload_dir}/images/{filename}",
            "thumbnail_url": f"/{self.upload_dir}/thumbnails/{thumbnail_filename}" if thumbnail_filename else None,
            "size": os.path.getsize(image_path),
            "content_type": file.content_type,
            "width": width,
            "height": height
        }
    
    async def save_temp_image(self, file: UploadFile) -> dict:
        """Save temporary image file for preview"""
        await self.validate_file(file)
        
        filename = self.generate_filename(file.filename)
        temp_path = os.path.join(self.upload_dir, "temp", filename)
        
        # Save original image to temp directory
        async with aiofiles.open(temp_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Validate that the saved file is actually a valid image
        try:
            with Image.open(temp_path) as img:
                # Verify it's a valid image by trying to load it
                img.verify()
        except Exception as e:
            # If it's not a valid image, delete the file and raise an error
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid image file: {str(e)}"
            )
        
        # Reopen the image to get dimensions (verify() closes the file)
        try:
            with Image.open(temp_path) as img:
                width, height = img.size
        except Exception as e:
            # If we can't get dimensions, use defaults
            width, height = None, None
        
        return {
            "filename": filename,
            "url": f"/{self.upload_dir}/temp/{filename}",
            "thumbnail_url": None,  # No thumbnail for temp images
            "size": os.path.getsize(temp_path),
            "content_type": file.content_type,
            "width": width,
            "height": height
        }
    
    async def generate_thumbnail(self, image_path: str, filename: str, size: tuple = (300, 300)) -> Optional[str]:
        """Generate thumbnail for image"""
        try:
            thumbnail_filename = f"thumb_{filename}"
            thumbnail_path = os.path.join(self.upload_dir, "thumbnails", thumbnail_filename)
            
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                
                # Generate thumbnail
                img.thumbnail(size, Image.Resampling.LANCZOS)
                img.save(thumbnail_path, "JPEG", quality=85)
            
            return thumbnail_filename
        except Exception as e:
            print(f"Error generating thumbnail: {e}")
            return None
    
    def delete_file(self, filename: str, subfolder: str = "images") -> bool:
        """Delete file from disk"""
        try:
            file_path = os.path.join(self.upload_dir, subfolder, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False
    
    def delete_image_with_thumbnail(self, filename: str) -> bool:
        """Delete image and its thumbnail"""
        image_deleted = self.delete_file(filename, "images")
        thumbnail_deleted = self.delete_file(f"thumb_{filename}", "thumbnails")
        return image_deleted
    
    def get_file_url(self, filename: str, subfolder: str = "images") -> str:
        """Get public URL for file"""
        return f"/{self.upload_dir}/{subfolder}/{filename}"


# Global file upload manager instance
file_upload_manager = FileUploadManager()


def get_file_upload_manager() -> FileUploadManager:
    """Get file upload manager instance"""
    return file_upload_manager
