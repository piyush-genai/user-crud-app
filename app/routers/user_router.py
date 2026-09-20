"""
FastAPI router for user management endpoints
"""
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse

from app.models.user_models import (
    UserCreate,
    UserUpdate,
    UserResponse,
    DeleteResponse,
    ValidationErrorResponse
)
from app.services.user_service import user_service


# Create router instance
router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={
        503: {"description": "Database connection unavailable"},
        500: {"description": "Internal server error"}
    }
)


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Create a new user record with all required information. Employee ID must be unique.",
    responses={
        201: {
            "description": "User successfully created",
            "model": UserResponse,
            "content": {
                "application/json": {
                    "example": {
                        "_id": "507f1f77bcf86cd799439011",
                        "user_name": "John Doe",
                        "address": "123 Main St, Springfield, IL 62701",
                        "employee_id": "EMP001",
                        "salary": 75000.50,
                        "gender": "Male",
                        "joining_date": "2024-01-15",
                        "active_status": True,
                        "profile_photo_url": None
                    }
                }
            }
        },
        409: {
            "description": "Employee ID already exists",
            "model": ValidationErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "field": "employee_id",
                                "message": "employee_id 'EMP001' already exists"
                            }
                        ]
                    }
                }
            }
        },
        422: {
            "description": "Validation error",
            "model": ValidationErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "field": "salary",
                                "message": "ensure this value is greater than 0"
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def create_user(user_data: UserCreate) -> UserResponse:
    """
    Create a new user record.
    
    Args:
        user_data: User creation data with all required fields
        
    Returns:
        Created user with MongoDB ID
        
    Raises:
        HTTPException: 409 if employee_id exists, 422 if validation fails, 503 if database unavailable
    """
    return await user_service.create_user(user_data)


@router.get(
    "/{id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user by ID",
    description="Retrieve a single user record by MongoDB ObjectId.",
    responses={
        200: {
            "description": "User found",
            "model": UserResponse,
            "content": {
                "application/json": {
                    "example": {
                        "_id": "507f1f77bcf86cd799439011",
                        "user_name": "John Doe",
                        "address": "123 Main St, Springfield, IL 62701",
                        "employee_id": "EMP001",
                        "salary": 75000.50,
                        "gender": "Male",
                        "joining_date": "2024-01-15",
                        "active_status": True,
                        "profile_photo_url": "/uploads/507f1f77bcf86cd799439011_profile.jpg"
                    }
                }
            }
        },
        404: {
            "description": "User not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "User with id '507f1f77bcf86cd799439011' not found"
                    }
                }
            }
        },
        422: {
            "description": "Invalid ID format",
            "model": ValidationErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "field": "id",
                                "message": "Invalid MongoDB ObjectId format: 'invalid-id'"
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def get_user_by_id(id: str) -> UserResponse:
    """
    Retrieve a user by MongoDB ObjectId.
    
    Args:
        id: MongoDB ObjectId as 24-character hexadecimal string
        
    Returns:
        User record with all fields
        
    Raises:
        HTTPException: 404 if user not found, 422 if invalid ID format, 503 if database unavailable
    """
    return await user_service.get_user_by_id(id)


@router.get(
    "",
    response_model=List[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all users",
    description="Retrieve a list of all user records in the system.",
    responses={
        200: {
            "description": "List of all users (empty array if no users exist)",
            "model": List[UserResponse],
            "content": {
                "application/json": {
                    "examples": {
                        "with_users": {
                            "summary": "Multiple users",
                            "value": [
                                {
                                    "_id": "507f1f77bcf86cd799439011",
                                    "user_name": "John Doe",
                                    "address": "123 Main St, Springfield, IL 62701",
                                    "employee_id": "EMP001",
                                    "salary": 75000.50,
                                    "gender": "Male",
                                    "joining_date": "2024-01-15",
                                    "active_status": True,
                                    "profile_photo_url": "/uploads/507f1f77bcf86cd799439011_profile.jpg"
                                },
                                {
                                    "_id": "507f1f77bcf86cd799439012",
                                    "user_name": "Jane Smith",
                                    "address": "456 Oak Ave, Boston, MA 02101",
                                    "employee_id": "EMP002",
                                    "salary": 85000.00,
                                    "gender": "Female",
                                    "joining_date": "2024-02-01",
                                    "active_status": True,
                                    "profile_photo_url": None
                                }
                            ]
                        },
                        "empty": {
                            "summary": "No users",
                            "value": []
                        }
                    }
                }
            }
        }
    }
)
async def get_all_users() -> List[UserResponse]:
    """
    Retrieve all users from the database.
    
    Returns:
        List of all user records (empty list if no users exist)
        
    Raises:
        HTTPException: 503 if database unavailable
    """
    return await user_service.get_all_users()


@router.put(
    "/{id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update user",
    description="Update an existing user with partial data. Only provided fields will be updated.",
    responses={
        200: {
            "description": "User successfully updated",
            "model": UserResponse,
            "content": {
                "application/json": {
                    "example": {
                        "_id": "507f1f77bcf86cd799439011",
                        "user_name": "John Doe",
                        "address": "123 Main St, Springfield, IL 62701",
                        "employee_id": "EMP001",
                        "salary": 80000.00,
                        "gender": "Male",
                        "joining_date": "2024-01-15",
                        "active_status": False,
                        "profile_photo_url": "/uploads/507f1f77bcf86cd799439011_profile.jpg"
                    }
                }
            }
        },
        404: {
            "description": "User not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "User with id '507f1f77bcf86cd799439011' not found"
                    }
                }
            }
        },
        409: {
            "description": "Employee ID conflict",
            "model": ValidationErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "field": "employee_id",
                                "message": "employee_id 'EMP001' already exists"
                            }
                        ]
                    }
                }
            }
        },
        422: {
            "description": "Validation error",
            "model": ValidationErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "field": "salary",
                                "message": "ensure this value is greater than 0"
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def update_user(id: str, user_data: UserUpdate) -> UserResponse:
    """
    Update an existing user with partial data.
    
    Args:
        id: MongoDB ObjectId as 24-character hexadecimal string
        user_data: Partial user update data (only provided fields will be updated)
        
    Returns:
        Updated user record with all fields
        
    Raises:
        HTTPException: 404 if user not found, 409 if employee_id conflict, 
                      422 if validation fails, 503 if database unavailable
    """
    return await user_service.update_user(id, user_data)


@router.delete(
    "/{id}",
    response_model=DeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete user",
    description="Delete a user record by MongoDB ObjectId.",
    responses={
        200: {
            "description": "User successfully deleted",
            "model": DeleteResponse,
            "content": {
                "application/json": {
                    "example": {
                        "id": "507f1f77bcf86cd799439011",
                        "message": "User successfully deleted"
                    }
                }
            }
        },
        404: {
            "description": "User not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "User with id '507f1f77bcf86cd799439011' not found"
                    }
                }
            }
        },
        422: {
            "description": "Invalid ID format",
            "model": ValidationErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "field": "id",
                                "message": "Invalid MongoDB ObjectId format: 'invalid-id'"
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def delete_user(id: str) -> DeleteResponse:
    """
    Delete a user by MongoDB ObjectId.
    
    Args:
        id: MongoDB ObjectId as 24-character hexadecimal string
        
    Returns:
        Confirmation message with deleted user ID
        
    Raises:
        HTTPException: 404 if user not found, 422 if invalid ID format
    """
    return await user_service.delete_user(id)


@router.post(
    "/{id}/photo",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload or replace profile photo",
    description="Upload a profile photo for a user or replace an existing photo. Supports JPEG, PNG, and WebP formats. Maximum file size: 5MB.",
    responses={
        200: {
            "description": "Photo successfully uploaded or replaced",
            "model": UserResponse,
            "content": {
                "application/json": {
                    "example": {
                        "_id": "507f1f77bcf86cd799439011",
                        "user_name": "John Doe",
                        "address": "123 Main St, Springfield, IL 62701",
                        "employee_id": "EMP001",
                        "salary": 75000.50,
                        "gender": "Male",
                        "joining_date": "2024-01-15",
                        "active_status": True,
                        "profile_photo_url": "/uploads/507f1f77bcf86cd799439011_profile_1704067200.jpg"
                    }
                }
            }
        },
        404: {
            "description": "User not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "User with id '507f1f77bcf86cd799439011' not found"
                    }
                }
            }
        },
        413: {
            "description": "File too large",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "File size exceeds maximum allowed size of 5MB"
                    }
                }
            }
        },
        422: {
            "description": "Invalid file type or missing file",
            "model": ValidationErrorResponse,
            "content": {
                "application/json": {
                    "examples": {
                        "unsupported_format": {
                            "summary": "Unsupported file format",
                            "value": {
                                "detail": [
                                    {
                                        "field": "file",
                                        "message": "File type not supported. Allowed formats: .jpg, .jpeg, .png, .webp"
                                    }
                                ]
                            }
                        },
                        "missing_file": {
                            "summary": "Missing file field",
                            "value": {
                                "detail": [
                                    {
                                        "field": "file",
                                        "message": "File field is required"
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        },
        500: {
            "description": "File storage operation failed",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "File storage operation failed"
                    }
                }
            }
        }
    }
)
async def upload_profile_photo(id: str, file: UploadFile = File(...)) -> UserResponse:
    """
    Upload or replace a profile photo for a user.
    
    If the user already has a photo, the old photo will be deleted before storing the new one.
    
    Args:
        id: MongoDB ObjectId as 24-character hexadecimal string
        file: Image file in multipart form data (JPEG, PNG, or WebP, max 5MB)
        
    Returns:
        Updated user record with new photo URL
        
    Raises:
        HTTPException: 404 if user not found, 413 if file too large, 
                      422 if invalid file type or ID format, 500 if storage fails
    """
    return await user_service.manage_photo(id, file)
