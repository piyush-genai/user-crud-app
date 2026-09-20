"""
FastAPI User CRUD Application - Main Entry Point
"""
import logging
import uuid
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from pymongo.errors import DuplicateKeyError, ConnectionFailure, ServerSelectionTimeoutError
from bson.errors import InvalidId

from app.routers.user_router import router as user_router
from app.repositories.user_repository import user_repository
from app.models.user_models import ErrorDetail


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] request_id=%(request_id)s %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S'
)
logger = logging.getLogger(__name__)


# Lifespan context manager for startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle events
    
    Startup: Initialize MongoDB connection
    Shutdown: Close MongoDB connection gracefully
    """
    # Startup
    try:
        logger.info("Starting User CRUD API...")
        await user_repository.connect()
        logger.info("Application startup complete")
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"Failed to connect to MongoDB during startup: {str(e)}")
        raise  # Exit with non-zero status code
    
    yield
    
    # Shutdown
    logger.info("Shutting down User CRUD API...")
    await user_repository.close()
    logger.info("Application shutdown complete")


# Create FastAPI application instance
app = FastAPI(
    title="User CRUD API",
    description="FastAPI-based REST API for managing user records with MongoDB. "
                "Provides CRUD operations for user management with MongoDB storage and profile photo upload capabilities.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)


# Configure CORS middleware (allow all origins for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware to add request ID to all requests
@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    """Add unique request ID to each request for tracing"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Add request_id to logging context
    old_factory = logging.getLogRecordFactory()
    
    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.request_id = request_id
        return record
    
    logging.setLogRecordFactory(record_factory)
    
    response = await call_next(request)
    
    # Restore original factory
    logging.setLogRecordFactory(old_factory)
    
    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id
    return response


# Global exception handler for RequestValidationError (422)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle Pydantic validation errors and format them consistently
    
    Converts FastAPI/Pydantic validation errors to structured error format
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    # Extract and format validation errors
    errors = []
    for error in exc.errors():
        field = error.get("loc", ["unknown"])[-1]  # Get the last element of loc (field name)
        message = error.get("msg", "validation error")
        errors.append(ErrorDetail(field=str(field), message=message))
    
    logger.warning(
        f"request_id={request_id} method={request.method} "
        f"endpoint={request.url.path} error=ValidationError "
        f"errors={[{'field': e.field, 'message': e.message} for e in errors]}"
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": [e.dict() for e in errors]}
    )


# Global exception handler for HTTPException (pass through)
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Handle HTTP exceptions and pass through with existing status and detail
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.warning(
        f"request_id={request_id} method={request.method} "
        f"endpoint={request.url.path} status={exc.status_code} "
        f"error=HTTPException detail={exc.detail}"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


# Global exception handler for PyMongo errors (503)
@app.exception_handler(ConnectionFailure)
@app.exception_handler(ServerSelectionTimeoutError)
async def mongodb_connection_exception_handler(request: Request, exc: Exception):
    """
    Handle MongoDB connection errors and return 503 Service Unavailable
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.error(
        f"request_id={request_id} method={request.method} "
        f"endpoint={request.url.path} error=DatabaseConnectionError "
        f"message={str(exc)}"
    )
    
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Database connection unavailable, please retry"}
    )


# Global exception handler for DuplicateKeyError (409)
@app.exception_handler(DuplicateKeyError)
async def duplicate_key_exception_handler(request: Request, exc: DuplicateKeyError):
    """
    Handle MongoDB duplicate key errors and return 409 Conflict
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    # Extract field name from duplicate key error message
    error_message = str(exc)
    field = "employee_id"  # Default to employee_id as it's the only unique field
    
    logger.warning(
        f"request_id={request_id} method={request.method} "
        f"endpoint={request.url.path} error=DuplicateKeyError "
        f"field={field}"
    )
    
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "detail": [
                {
                    "field": field,
                    "message": f"{field} already exists"
                }
            ]
        }
    )


# Global exception handler for InvalidId (422)
@app.exception_handler(InvalidId)
async def invalid_id_exception_handler(request: Request, exc: InvalidId):
    """
    Handle invalid MongoDB ObjectId format errors
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.warning(
        f"request_id={request_id} method={request.method} "
        f"endpoint={request.url.path} error=InvalidIdError "
        f"message={str(exc)}"
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": [
                {
                    "field": "id",
                    "message": f"Invalid MongoDB ObjectId format: {str(exc)}"
                }
            ]
        }
    )


# Catch-all exception handler for unexpected errors (500)
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle all unexpected exceptions and return 500 Internal Server Error
    
    Logs full error details but returns generic message to client
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.error(
        f"request_id={request_id} method={request.method} "
        f"endpoint={request.url.path} error=UnexpectedError "
        f"type={type(exc).__name__} message={str(exc)}",
        exc_info=True  # Include stack trace in logs
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


# Include routers
app.include_router(user_router)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to User CRUD API",
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        },
        "version": "1.0.0"
    }


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "User CRUD API"}
