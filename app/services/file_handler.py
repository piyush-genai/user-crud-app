"""
File handler for managing profile photo uploads and storage.
"""
import os
import time
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException


class FileHandler:
    """Handles file upload validation, storage, and deletion for profile photos."""
    
    # Allowed file extensions for profile photos
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
    
    # Maximum file size in bytes (5MB)
    MAX_FILE_SIZE = 5 * 1024 * 1024
    
    def __init__(self, upload_dir: str = "uploads"):
        """
        Initialize FileHandler with upload directory.
        
        Args:
            upload_dir: Directory path where uploaded files will be stored
        """
        self.upload_dir = Path(upload_dir)
        # Create upload directory if it doesn't exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def validate_file_type(self, filename: str) -> bool:
        """
        Validate if the file extension is allowed.
        
        Args:
            filename: Name of the file to validate
            
        Returns:
            True if file extension is allowed, False otherwise
        """
        file_ext = Path(filename).suffix.lower()
        return file_ext in self.ALLOWED_EXTENSIONS
    
    async def validate_file_size(self, file: UploadFile) -> bool:
        """
        Validate if the file size is within the allowed limit.
        
        Args:
            file: UploadFile object to validate
            
        Returns:
            True if file size is within limit, False otherwise
        """
        # Read file content to check size
        content = await file.read()
        file_size = len(content)
        
        # Reset file pointer to beginning for later use
        await file.seek(0)
        
        return file_size <= self.MAX_FILE_SIZE
    
    async def save_file(self, user_id: str, file: UploadFile) -> str:
        """
        Validate and save uploaded file with unique filename.
        
        Args:
            user_id: MongoDB ObjectId of the user
            file: UploadFile object to save
            
        Returns:
            URL/path to the saved file
            
        Raises:
            HTTPException: If validation fails or file I/O error occurs
        """
        try:
            # Validate file type
            if not self.validate_file_type(file.filename):
                raise HTTPException(
                    status_code=422,
                    detail=f"Unsupported file type. Allowed formats: {', '.join(self.ALLOWED_EXTENSIONS)}"
                )
            
            # Validate file size
            if not await self.validate_file_size(file):
                raise HTTPException(
                    status_code=413,
                    detail=f"File size exceeds maximum allowed size of {self.MAX_FILE_SIZE / (1024 * 1024)}MB"
                )
            
            # Generate unique filename using pattern: {user_id}_profile_{timestamp}.{extension}
            file_ext = Path(file.filename).suffix.lower()
            timestamp = int(time.time())
            unique_filename = f"{user_id}_profile_{timestamp}{file_ext}"
            file_path = self.upload_dir / unique_filename
            
            # Read file content (file pointer is already at beginning from validate_file_size)
            content = await file.read()
            
            # Write file to disk
            with open(file_path, "wb") as f:
                f.write(content)
            
            # Return URL/path to the file
            return f"/{self.upload_dir}/{unique_filename}"
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except (IOError, OSError) as e:
            # Handle file I/O errors
            raise HTTPException(
                status_code=500,
                detail="File storage operation failed"
            ) from e
        except Exception as e:
            # Handle unexpected errors
            raise HTTPException(
                status_code=500,
                detail="File storage operation failed"
            ) from e
    
    def delete_file(self, file_url: str) -> bool:
        """
        Delete file from storage.
        
        Args:
            file_url: URL/path to the file to delete
            
        Returns:
            True if file was deleted successfully, False otherwise
        """
        try:
            # Extract filename from URL (remove leading slash and directory)
            # Example: "/uploads/user123_profile_1234567890.jpg" -> "user123_profile_1234567890.jpg"
            if file_url.startswith("/"):
                file_url = file_url[1:]
            
            file_path = Path(file_url)
            
            # Check if file exists
            if file_path.exists() and file_path.is_file():
                file_path.unlink()
                return True
            else:
                # File doesn't exist, consider it already deleted
                return False
                
        except (IOError, OSError) as e:
            # Log error but don't raise - as per design, deletion failure should be logged but not block
            print(f"Error deleting file {file_url}: {e}")
            return False
        except Exception as e:
            # Handle unexpected errors
            print(f"Unexpected error deleting file {file_url}: {e}")
            return False
