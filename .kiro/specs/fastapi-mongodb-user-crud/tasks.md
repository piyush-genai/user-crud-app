# Implementation Plan: FastAPI MongoDB User CRUD API

## Overview

This implementation plan creates a FastAPI-based REST API for managing user records in MongoDB. The system implements a layered architecture with distinct router, service, and repository layers. The API provides CRUD endpoints for user management plus profile photo upload capabilities. Task 9 represents the primary definition of done - manual testing to verify all requirements. Tasks 10-12 are optional testing tasks for comprehensive test coverage.

## Tasks

- [ ] 1. Set up project structure and dependencies
  - Create directory structure: `app/`, `app/routers/`, `app/services/`, `app/repositories/`, `app/models/`, `uploads/`
  - Create `requirements.txt` with dependencies: fastapi, uvicorn, motor (async MongoDB driver), pydantic, python-multipart
  - Create `app/__init__.py` and module `__init__.py` files
  - Create `app/main.py` with FastAPI app initialization
  - Create `.env.example` file with MongoDB connection string template
  - _Requirements: Requirement 8_

- [ ] 2. Implement Pydantic data models
  - Create `app/models/user_models.py`
  - Implement `UserCreate` model with all field validations (user_name max 100 chars, address max 500 chars, employee_id max 50 chars, salary float greater than 0, gender enum, joining_date date validation with range 1900-01-01 to 100 years future, active_status bool)
  - Implement `UserUpdate` model with optional fields matching UserCreate constraints
  - Implement `UserResponse` model with id field aliased from `_id`
  - Implement `ErrorDetail` and `ValidationErrorResponse` models
  - Implement `DeleteResponse` model
  - Add custom validators for joining_date range validation
  - _Requirements: Requirement 7_

- [ ] 3. Implement MongoDB repository layer
  - Create `app/repositories/user_repository.py`
  - Implement `UserRepository` class with Motor AsyncIOMotorClient initialization
  - Implement `create(user_data: dict) -> dict` method
  - Implement `find_by_id(user_id: str) -> Optional[dict]` method with ObjectId validation
  - Implement `find_by_employee_id(employee_id: str) -> Optional[dict]` method
  - Implement `find_all() -> List[dict]` method
  - Implement `update(user_id: str, update_data: dict) -> Optional[dict]` method
  - Implement `delete(user_id: str) -> bool` method
  - Implement connection retry logic with exponential backoff
  - Create unique index on `employee_id` field
  - Add error handling for MongoDB connection failures
  - _Requirements: Requirement 8_

- [ ] 4. Implement file storage handler
  - Create `app/services/file_handler.py`
  - Implement `FileHandler` class with constants for allowed extensions and max file size
  - Define `ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}`
  - Define `MAX_FILE_SIZE = 5 * 1024 * 1024` (5MB)
  - Implement `validate_file_type(filename: str) -> bool` method
  - Implement `validate_file_size(file: UploadFile) -> bool` method
  - Implement `save_file(file: UploadFile) -> str` method with unique filename generation using pattern `{user_id}_profile_{timestamp}.{extension}`
  - Implement `delete_file(file_url: str) -> bool` method
  - Add error handling for file I/O operations
  - _Requirements: Requirement 6_

- [ ] 5. Implement user service layer
  - Create `app/services/user_service.py`
  - Implement `UserService` class with dependencies on UserRepository and FileHandler
  - Implement `create_user(user_data: UserCreate) -> UserResponse` with employee_id uniqueness check
  - Implement `get_user_by_id(user_id: str) -> UserResponse` with 404 handling
  - Implement `get_all_users() -> List[UserResponse]`
  - Implement `update_user(user_id: str, user_data: UserUpdate) -> UserResponse` with employee_id uniqueness check and partial update support
  - Implement `delete_user(user_id: str) -> DeleteResponse` with 404 handling
  - Implement `manage_photo(user_id: str, file: UploadFile) -> UserResponse` that creates photo if none exists or replaces existing photo with old file deletion
  - Add error translation from repository exceptions to HTTP exceptions
  - _Requirements: Requirement 1, Requirement 2, Requirement 3, Requirement 4, Requirement 5, Requirement 6_

- [ ] 6. Implement user router endpoints
  - Create `app/routers/user_router.py`
  - Create APIRouter instance
  - Implement `POST /users` endpoint calling UserService.create_user, returning 201 on success
  - Implement `GET /users/{id}` endpoint calling UserService.get_user_by_id, returning 200 or 404
  - Implement `GET /users` endpoint calling UserService.get_all_users, returning 200
  - Implement `PUT /users/{id}` endpoint calling UserService.update_user, returning 200 or 404
  - Implement `DELETE /users/{id}` endpoint calling UserService.delete_user, returning 200 or 404
  - Implement `POST /users/{id}/photo` endpoint with multipart form data handling, calling UserService.manage_photo
  - Add response_model specifications for all endpoints
  - Add OpenAPI documentation with examples for all endpoints
  - _Requirements: Requirement 1, Requirement 2, Requirement 3, Requirement 4, Requirement 5, Requirement 6, Requirement 9_

- [ ] 7. Configure FastAPI application and global error handlers
  - Update `app/main.py` to create FastAPI instance with title, description, and version
  - Include user_router in the application
  - Implement global exception handler for `RequestValidationError` to format validation errors
  - Implement global exception handler for `HTTPException` to pass through status and detail
  - Implement global exception handler for PyMongo errors to return 503 with generic message
  - Implement catch-all exception handler for unexpected errors returning 500
  - Configure CORS middleware if needed
  - Add startup event handler for MongoDB connection initialization
  - Add shutdown event handler for graceful MongoDB connection closure
  - Add logging configuration for all error types with request ID, timestamp, and error details
  - Verify `/docs` and `/redoc` endpoints are accessible
  - _Requirements: Requirement 7, Requirement 8, Requirement 9_

- [ ] 8. Add documentation and configuration files
  - Create `README.md` with project description, setup instructions, and API usage examples
  - Create `.env.example` with MongoDB connection string, database name, and upload directory path
  - Create `.gitignore` with entries for venv/, __pycache__/, .env, uploads/
  - Create `docker-compose.yml` for local MongoDB instance (optional)
  - Document all environment variables required
  - Add API endpoint examples in README with curl commands
  - _Requirements: Requirement 9_

- [ ] 9. Manual testing and verification (PRIMARY DEFINITION OF DONE)
  - Start the application with `uvicorn app.main:app --reload`
  - Verify MongoDB connection establishes successfully on startup
  - Access `/docs` and verify Swagger UI loads with all endpoints
  - Test creating a user via Swagger UI
  - Test retrieving the created user by ID
  - Test listing all users
  - Test updating a user with partial data
  - Test managing a profile photo (create and replace scenarios)
  - Test deleting a user
  - Test all error scenarios (duplicate employee_id, invalid ID format, missing fields, file too large, unsupported file type)
  - Verify all status codes match requirements
  - Verify all error messages are clear and descriptive
  - _Requirements: Requirement 1, Requirement 2, Requirement 3, Requirement 4, Requirement 5, Requirement 6, Requirement 7, Requirement 8, Requirement 9_

- [ ]* 10. Implement integration tests
  - Create `tests/integration/test_api.py`
  - Set up test fixtures with TestClient, test MongoDB instance, and temporary upload directory
  - Implement database cleanup before each test
  - Implement test for POST /users with valid data returns 201
  - Implement test for POST /users with duplicate employee_id returns 409
  - Implement test for POST /users with missing fields returns 422
  - Implement test for POST /users with invalid data types returns 422
  - Implement test for GET /users/{id} with valid ID returns 200
  - Implement test for GET /users/{id} with non-existent ID returns 404
  - Implement test for GET /users/{id} with invalid ID format returns 422
  - Implement test for GET /users with empty collection returns empty array
  - Implement test for GET /users with multiple users returns all users
  - Implement test for PUT /users/{id} with partial data updates only specified fields
  - Implement test for PUT /users/{id} with duplicate employee_id returns 409
  - Implement test for PUT /users/{id} with non-existent ID returns 404
  - Implement test for DELETE /users/{id} with valid ID returns 200 and removes from DB
  - Implement test for DELETE /users/{id} with non-existent ID returns 404
  - Implement test for DELETE /users/{id} called twice returns 404 on second call
  - Implement test for POST /users/{id}/photo with valid file creates photo
  - Implement test for POST /users/{id}/photo replaces existing photo and deletes old file
  - Implement test for POST /users/{id}/photo with unsupported format returns 422
  - Implement test for POST /users/{id}/photo with file >5MB returns 413
  - Implement test for POST /users/{id}/photo for non-existent user returns 404
  - Create `tests/integration/test_connection.py` for database connection tests
  - Create `tests/integration/test_docs.py` to verify /docs and /redoc endpoints return 200
  - _Requirements: All requirements_

- [ ]* 11. Create test fixtures and seed data
  - Create `tests/fixtures.py`
  - Implement `valid_user_data` fixture with complete valid user payload
  - Implement `invalid_user_data_missing_fields` fixture
  - Implement `invalid_user_data_wrong_types` fixture
  - Implement `user_update_partial` fixture
  - Implement `mock_uploaded_file` fixture for file upload testing
  - Implement fixture for test MongoDB client
  - Implement fixture for temporary upload directory with cleanup
  - _Requirements: All requirements_

- [ ]* 12. Run full test suite and verify coverage
  - Install test dependencies: pytest, pytest-asyncio, pytest-cov, httpx
  - Create `pytest.ini` for test configuration
  - Run `pytest tests/` to execute all tests
  - Run `pytest --cov=app tests/` to generate coverage report
  - Verify overall coverage is at least 80%
  - Verify service layer coverage is at least 90%
  - Verify repository layer coverage is at least 85%
  - Verify router layer coverage is at least 80%
  - Verify file handler coverage is at least 90%
  - Fix any failing tests
  - Add additional tests if coverage is below thresholds
  - _Requirements: All requirements_

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP delivery
- Task 9 is the primary definition of done - all requirements can be verified through manual testing
- Optional tasks 10-12 provide comprehensive automated test coverage for production readiness
- Each task references specific requirements for traceability
- The design has no Correctness Properties section, so no property-based tests are included
- Testing focuses on unit tests and integration tests appropriate for REST API CRUD operations

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1"] },
    { "id": 1, "tasks": ["2", "3", "4"] },
    { "id": 2, "tasks": ["5"] },
    { "id": 3, "tasks": ["6"] },
    { "id": 4, "tasks": ["7"] },
    { "id": 5, "tasks": ["8"] },
    { "id": 6, "tasks": ["9"] },
    { "id": 7, "tasks": ["10"] },
    { "id": 8, "tasks": ["11"] },
    { "id": 9, "tasks": ["12"] }
  ]
}
```
