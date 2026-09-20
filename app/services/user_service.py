"""
Service layer for user management business logic
"""
from typing import List, Optional
from fastapi import HTTPException, UploadFile
from pymongo.errors import DuplicateKeyError, ConnectionFailure
from bson.errors import InvalidId

from app.models.user_models import UserCreate, UserUpdate, UserResponse, DeleteResponse
from app.repositories.user_repository import user_repository
from app.services.file_handler import FileHandler


class UserService:
    """
    Service layer implementing business logic for user operations
    """
    
    def __init__(self):
        """Initialize service with dependencies"""
        self.repository = user_repository
        self.file_handler = FileHandler(upload_dir="uploads")
    
    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """
        Create a new user after validating employee_id uniqueness
        
        Args:
            user_data: Validated user creation data from Pydantic model
            
        Returns:
            Created user as UserResponse
            
        Raises:
            HTTPException: 409 if employee_id already exists, 503 if database unavailable
        """
        try:
            # Check if employee_id already exists
            existing_user = await self.repository.find_by_employee_id(user_data.employee_id)
            if existing_user:
                raise HTTPException(
                    status_code=409,
                    detail=[{
                        "field": "employee_id",
                        "message": f"employee_id '{user_data.employee_id}' already exists"
                    }]
                )
            
            # Convert Pydantic model to dict for MongoDB
            user_dict = user_data.model_dump()
            
            # Convert date object to ISO 8601 string
            user_dict["joining_date"] = user_data.joining_date.isoformat()
            
            # Create user in database
            created_user = await self.repository.create(user_dict)
            
            # Convert to response model
            return UserResponse(**created_user)
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except ConnectionFailure:
            raise HTTPException(
                status_code=503,
                detail="Database connection unavailable, please retry"
            )
        except Exception as e:
            # Log unexpected errors and return generic message
            print(f"Unexpected error in create_user: {e}")
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred"
            )
    
    async def get_user_by_id(self, user_id: str) -> UserResponse:
        """
        Retrieve a single user by MongoDB ObjectId
        
        Args:
            user_id: MongoDB ObjectId as string
            
        Returns:
            User as UserResponse
            
        Raises:
            HTTPException: 404 if user not found, 422 if invalid ID format, 503 if database unavailable
        """
        try:
            user = await self.repository.find_by_id(user_id)
            
            if not user:
                raise HTTPException(
                    status_code=404,
                    detail=f"User with id '{user_id}' not found"
                )
            
            return UserResponse(**user)
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except InvalidId:
            raise HTTPException(
                status_code=422,
                detail=[{
                    "field": "id",
                    "message": f"Invalid MongoDB ObjectId format: '{user_id}'"
                }]
            )
        except ConnectionFailure:
            raise HTTPException(
                status_code=503,
                detail="Database connection unavailable, please retry"
            )
        except Exception as e:
            # Log unexpected errors and return generic message
            print(f"Unexpected error in get_user_by_id: {e}")
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred"
            )
    
    async def get_all_users(self) -> List[UserResponse]:
        """
        Retrieve all users from the database
        
        Returns:
            List of users as UserResponse objects (empty list if no users)
            
        Raises:
            HTTPException: 503 if database unavailable
        """
        try:
            users = await self.repository.find_all()
            
            # Convert all users to response models
            return [UserResponse(**user) for user in users]
            
        except ConnectionFailure:
            raise HTTPException(
                status_code=503,
                detail="Database connection unavailable, please retry"
            )
        except Exception as e:
            # Log unexpected errors and return generic message
            print(f"Unexpected error in get_all_users: {e}")
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred"
            )
    
    async def update_user(self, user_id: str, user_data: UserUpdate) -> UserResponse:
        """
        Update a user with partial data, validating employee_id uniqueness
        
        Args:
            user_id: MongoDB ObjectId as string
            user_data: Validated user update data from Pydantic model
            
        Returns:
            Updated user as UserResponse
            
        Raises:
            HTTPException: 404 if user not found, 409 if employee_id conflict, 
                         422 if invalid ID format or validation error, 503 if database unavailable
        """
        try:
            # First verify the user exists
            existing_user = await self.repository.find_by_id(user_id)
            if not existing_user:
                raise HTTPException(
                    status_code=404,
                    detail=f"User with id '{user_id}' not found"
                )
            
            # Convert Pydantic model to dict, excluding unset fields
            update_dict = user_data.model_dump(exclude_unset=True)
            
            # If no fields to update, return current user
            if not update_dict:
                return UserResponse(**existing_user)
            
            # Check for employee_id uniqueness if being updated
            if "employee_id" in update_dict:
                # Check if another user has this employee_id
                conflicting_user = await self.repository.find_by_employee_id(update_dict["employee_id"])
                if conflicting_user and conflicting_user["_id"] != user_id:
                    raise HTTPException(
                        status_code=409,
                        detail=[{
                            "field": "employee_id",
                            "message": f"employee_id '{update_dict['employee_id']}' already exists"
                        }]
                    )
            
            # Convert date object to ISO 8601 string if present
            if "joining_date" in update_dict and update_dict["joining_date"] is not None:
                update_dict["joining_date"] = update_dict["joining_date"].isoformat()
            
            # Validate that required fields are not empty strings or null
            empty_fields = []
            for field_name, field_value in update_dict.items():
                if field_value == "" or field_value is None:
                    if field_name in ["user_name", "address", "employee_id", "gender"]:
                        empty_fields.append(field_name)
            
            if empty_fields:
                raise HTTPException(
                    status_code=422,
                    detail=[{
                        "field": field,
                        "message": f"Field '{field}' cannot be empty"
                    } for field in empty_fields]
                )
            
            # Update user in database
            updated_user = await self.repository.update(user_id, update_dict)
            
            if not updated_user:
                raise HTTPException(
                    status_code=404,
                    detail=f"User with id '{user_id}' not found"
                )
            
            return UserResponse(**updated_user)
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except InvalidId:
            raise HTTPException(
                status_code=422,
                detail=[{
                    "field": "id",
                    "message": f"Invalid MongoDB ObjectId format: '{user_id}'"
                }]
            )
        except DuplicateKeyError:
            # This shouldn't happen due to our pre-check, but handle it anyway
            raise HTTPException(
                status_code=409,
                detail=[{
                    "field": "employee_id",
                    "message": f"employee_id already exists"
                }]
            )
        except ConnectionFailure:
            raise HTTPException(
                status_code=503,
                detail="Database connection unavailable, please retry"
            )
        except Exception as e:
            # Log unexpected errors and return generic message
            print(f"Unexpected error in update_user: {e}")
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred"
            )
    
    async def delete_user(self, user_id: str) -> DeleteResponse:
        """
        Delete a user by MongoDB ObjectId
        
        Args:
            user_id: MongoDB ObjectId as string
            
        Returns:
            DeleteResponse with confirmation message
            
        Raises:
            HTTPException: 404 if user not found, 422 if invalid ID format
        """
        try:
            deleted = await self.repository.delete(user_id)
            
            if not deleted:
                raise HTTPException(
                    status_code=404,
                    detail=f"User with id '{user_id}' not found"
                )
            
            return DeleteResponse(
                id=user_id,
                message="User successfully deleted"
            )
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except InvalidId:
            raise HTTPException(
                status_code=422,
                detail=[{
                    "field": "id",
                    "message": f"Invalid MongoDB ObjectId format: '{user_id}'"
                }]
            )
        except ConnectionFailure:
            raise HTTPException(
                status_code=503,
                detail="Database connection unavailable, please retry"
            )
        except Exception as e:
            # Log unexpected errors and return generic message
            print(f"Unexpected error in delete_user: {e}")
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred"
            )
    
    async def manage_photo(self, user_id: str, file: UploadFile) -> UserResponse:
        """
        Upload or replace profile photo for a user
        
        If user already has a photo, deletes the old file before storing the new one.
        Logs but does not fail if old file deletion fails.
        
        Args:
            user_id: MongoDB ObjectId as string
            file: Uploaded file from multipart form data
            
        Returns:
            Updated user as UserResponse
            
        Raises:
            HTTPException: 404 if user not found, 422 if invalid file type or ID format,
                         413 if file too large, 500 if file storage fails
        """
        try:
            # First verify the user exists
            existing_user = await self.repository.find_by_id(user_id)
            if not existing_user:
                raise HTTPException(
                    status_code=404,
                    detail=f"User with id '{user_id}' not found"
                )
            
            # If user has an existing photo, attempt to delete it
            if existing_user.get("profile_photo_url"):
                old_photo_url = existing_user["profile_photo_url"]
                deletion_success = self.file_handler.delete_file(old_photo_url)
                if not deletion_success:
                    # Log warning but proceed with new upload
                    print(f"Warning: Failed to delete old photo file: {old_photo_url}")
            
            # Save the new file (this validates file type and size)
            photo_url = await self.file_handler.save_file(user_id, file)
            
            # Update user document with new photo URL
            updated_user = await self.repository.update(
                user_id,
                {"profile_photo_url": photo_url}
            )
            
            if not updated_user:
                raise HTTPException(
                    status_code=404,
                    detail=f"User with id '{user_id}' not found"
                )
            
            return UserResponse(**updated_user)
            
        except HTTPException:
            # Re-raise HTTP exceptions (from file validation or user lookup)
            raise
        except InvalidId:
            raise HTTPException(
                status_code=422,
                detail=[{
                    "field": "id",
                    "message": f"Invalid MongoDB ObjectId format: '{user_id}'"
                }]
            )
        except ConnectionFailure:
            raise HTTPException(
                status_code=503,
                detail="Database connection unavailable, please retry"
            )
        except Exception as e:
            # Log unexpected errors and return generic message
            print(f"Unexpected error in manage_photo: {e}")
            raise HTTPException(
                status_code=500,
                detail="File storage operation failed"
            )


# Global service instance
user_service = UserService()
