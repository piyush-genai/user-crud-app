"""
FastAPI User CRUD Application - Main Entry Point
"""
from fastapi import FastAPI

app = FastAPI(
    title="User CRUD API",
    description="FastAPI-based REST API for managing user records with MongoDB",
    version="1.0.0"
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to User CRUD API. Visit /docs for API documentation."}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
