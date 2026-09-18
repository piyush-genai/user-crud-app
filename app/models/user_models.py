"""
Pydantic models for user data validation and serialization
"""
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from typing_extensions import Literal


class UserCreate(BaseModel):
    """Model for creating a new user"""
    user_name: str = Field(..., max_length=100, description="User's full name")
    address: str = Field(..., max_length=500, description="User's address")
    employee_id: str = Field(..., max_length=50, description="Unique employee identifier")
    salary: float = Field(..., gt=0, description="User's salary (must be greater than 0)")
    gender: Literal["Male", "Female", "Other"] = Field(..., description="User's gender")
    joining_date: date = Field(..., description="Date when user joined (YYYY-MM-DD)")
    active_status: bool = Field(..., description="Whether the user is currently active")

    @field_validator('joining_date')
    @classmethod
    def validate_joining_date(cls, v: date) -> date:
        """Validate joining_date is between 1900-01-01 and 100 years from now"""
        min_date = date(1900, 1, 1)
        max_date = date.today().replace(year=date.today().year + 100)
        
        if v < min_date:
            raise ValueError(f"joining_date must be on or after {min_date}")
        if v > max_date:
            raise ValueError(f"joining_date must be on or before {max_date}")
        
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "user_name": "John Doe",
                "address": "123 Main St, Springfield, IL 62701",
                "employee_id": "EMP001",
                "salary": 75000.50,
                "gender": "Male",
                "joining_date": "2024-01-15",
                "active_status": True
            }
        }


class UserUpdate(BaseModel):
    """Model for updating an existing user (all fields optional)"""
    user_name: Optional[str] = Field(None, max_length=100, description="User's full name")
    address: Optional[str] = Field(None, max_length=500, description="User's address")
    employee_id: Optional[str] = Field(None, max_length=50, description="Unique employee identifier")
    salary: Optional[float] = Field(None, gt=0, description="User's salary (must be greater than 0)")
    gender: Optional[Literal["Male", "Female", "Other"]] = Field(None, description="User's gender")
    joining_date: Optional[date] = Field(None, description="Date when user joined (YYYY-MM-DD)")
    active_status: Optional[bool] = Field(None, description="Whether the user is currently active")

    @field_validator('joining_date')
    @classmethod
    def validate_joining_date(cls, v: Optional[date]) -> Optional[date]:
        """Validate joining_date is between 1900-01-01 and 100 years from now"""
        if v is None:
            return v
        
        min_date = date(1900, 1, 1)
        max_date = date.today().replace(year=date.today().year + 100)
        
        if v < min_date:
            raise ValueError(f"joining_date must be on or after {min_date}")
        if v > max_date:
            raise ValueError(f"joining_date must be on or before {max_date}")
        
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "salary": 80000.00,
                "active_status": False
            }
        }


class UserResponse(BaseModel):
    """Model for user response (returned from API)"""
    id: str = Field(..., alias="_id", description="MongoDB ObjectId as string")
    user_name: str = Field(..., description="User's full name")
    address: str = Field(..., description="User's address")
    employee_id: str = Field(..., description="Unique employee identifier")
    salary: float = Field(..., description="User's salary")
    gender: str = Field(..., description="User's gender")
    joining_date: str = Field(..., description="Date when user joined (ISO 8601 format)")
    active_status: bool = Field(..., description="Whether the user is currently active")
    profile_photo_url: Optional[str] = Field(None, description="URL to user's profile photo")

    class Config:
        populate_by_name = True
        json_schema_extra = {
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


class ErrorDetail(BaseModel):
    """Model for individual error details"""
    field: str = Field(..., description="Field name that caused the error")
    message: str = Field(..., description="Error message describing what went wrong")

    class Config:
        json_schema_extra = {
            "example": {
                "field": "salary",
                "message": "ensure this value is greater than 0"
            }
        }


class ValidationErrorResponse(BaseModel):
    """Model for validation error responses"""
    detail: List[ErrorDetail] = Field(..., description="List of validation errors")

    class Config:
        json_schema_extra = {
            "example": {
                "detail": [
                    {
                        "field": "salary",
                        "message": "ensure this value is greater than 0"
                    },
                    {
                        "field": "joining_date",
                        "message": "invalid date format, expected YYYY-MM-DD"
                    }
                ]
            }
        }


class DeleteResponse(BaseModel):
    """Model for delete operation response"""
    id: str = Field(..., description="MongoDB ObjectId of the deleted user")
    message: str = Field(..., description="Confirmation message")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "message": "User successfully deleted"
            }
        }
