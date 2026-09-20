"""
MongoDB repository layer for user data operations
"""
import os
import asyncio
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError, ConnectionFailure, ServerSelectionTimeoutError
from bson import ObjectId
from bson.errors import InvalidId
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UserRepository:
    """
    Repository class for MongoDB user operations with connection retry logic
    """
    
    def __init__(self):
        """Initialize repository with MongoDB connection"""
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.collection_name = "users"
        self._connection_retries = 3
        self._base_retry_delay = 1  # seconds
        
    async def connect(self):
        """
        Establish MongoDB connection with retry logic and exponential backoff
        """
        mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        database_name = os.getenv("DATABASE_NAME", "user_api")
        
        for attempt in range(self._connection_retries):
            try:
                logger.info(f"Attempting MongoDB connection (attempt {attempt + 1}/{self._connection_retries})...")
                
                # Create client with timeout settings
                self.client = AsyncIOMotorClient(
                    mongodb_uri,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=5000
                )
                
                # Test the connection
                await self.client.admin.command('ping')
                
                # Set database reference
                self.db = self.client[database_name]
                
                # Create unique index on employee_id
                await self._ensure_indexes()
                
                logger.info(f"Successfully connected to MongoDB database: {database_name}")
                return
                
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                retry_delay = self._base_retry_delay * (2 ** attempt)  # Exponential backoff
                logger.error(f"MongoDB connection failed: {str(e)}")
                
                if attempt < self._connection_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error("Failed to connect to MongoDB after all retry attempts")
                    raise ConnectionFailure("Unable to establish MongoDB connection")
    
    async def _ensure_indexes(self):
        """
        Create necessary indexes for the users collection
        """
        try:
            # Create unique index on employee_id field
            await self.db[self.collection_name].create_index(
                "employee_id",
                unique=True,
                name="employee_id_unique_idx"
            )
            logger.info("Created unique index on employee_id field")
        except Exception as e:
            logger.warning(f"Index creation warning: {str(e)}")
    
    async def close(self):
        """
        Close MongoDB connection gracefully
        """
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
    
    async def create(self, user_data: dict) -> dict:
        """
        Insert a new user document into MongoDB
        
        Args:
            user_data: Dictionary containing user fields
            
        Returns:
            Created user document with _id field
            
        Raises:
            DuplicateKeyError: If employee_id already exists
            ConnectionFailure: If database connection fails
        """
        try:
            result = await self.db[self.collection_name].insert_one(user_data)
            created_user = await self.find_by_id(str(result.inserted_id))
            return created_user
        except DuplicateKeyError:
            logger.warning(f"Duplicate employee_id attempted: {user_data.get('employee_id')}")
            raise
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Database connection error during create: {str(e)}")
            raise ConnectionFailure("Database connection unavailable")
    
    async def find_by_id(self, user_id: str) -> Optional[dict]:
        """
        Find a user document by MongoDB ObjectId
        
        Args:
            user_id: String representation of MongoDB ObjectId
            
        Returns:
            User document if found, None otherwise
            
        Raises:
            InvalidId: If user_id is not a valid ObjectId format
            ConnectionFailure: If database connection fails
        """
        try:
            object_id = ObjectId(user_id)
        except (InvalidId, TypeError) as e:
            logger.warning(f"Invalid ObjectId format: {user_id}")
            raise InvalidId(f"Invalid ID format: {user_id}")
        
        try:
            user = await self.db[self.collection_name].find_one({"_id": object_id})
            if user:
                # Convert ObjectId to string for JSON serialization
                user["_id"] = str(user["_id"])
            return user
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Database connection error during find_by_id: {str(e)}")
            raise ConnectionFailure("Database connection unavailable")
    
    async def find_by_employee_id(self, employee_id: str) -> Optional[dict]:
        """
        Find a user document by employee_id field
        
        Args:
            employee_id: Employee ID to search for
            
        Returns:
            User document if found, None otherwise
            
        Raises:
            ConnectionFailure: If database connection fails
        """
        try:
            user = await self.db[self.collection_name].find_one({"employee_id": employee_id})
            if user:
                # Convert ObjectId to string for JSON serialization
                user["_id"] = str(user["_id"])
            return user
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Database connection error during find_by_employee_id: {str(e)}")
            raise ConnectionFailure("Database connection unavailable")
    
    async def find_all(self) -> List[dict]:
        """
        Retrieve all user documents from MongoDB
        
        Returns:
            List of user documents
            
        Raises:
            ConnectionFailure: If database connection fails
        """
        try:
            cursor = self.db[self.collection_name].find({})
            users = await cursor.to_list(length=None)
            
            # Convert ObjectId to string for each user
            for user in users:
                user["_id"] = str(user["_id"])
            
            return users
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Database connection error during find_all: {str(e)}")
            raise ConnectionFailure("Database connection unavailable")
    
    async def update(self, user_id: str, update_data: dict) -> Optional[dict]:
        """
        Update a user document and return the updated version
        
        Args:
            user_id: String representation of MongoDB ObjectId
            update_data: Dictionary containing fields to update
            
        Returns:
            Updated user document if found, None if user doesn't exist
            
        Raises:
            InvalidId: If user_id is not a valid ObjectId format
            DuplicateKeyError: If updating employee_id to an existing value
            ConnectionFailure: If database connection fails
        """
        try:
            object_id = ObjectId(user_id)
        except (InvalidId, TypeError) as e:
            logger.warning(f"Invalid ObjectId format: {user_id}")
            raise InvalidId(f"Invalid ID format: {user_id}")
        
        try:
            # Use $set to update only specified fields
            result = await self.db[self.collection_name].find_one_and_update(
                {"_id": object_id},
                {"$set": update_data},
                return_document=True  # Return updated document
            )
            
            if result:
                # Convert ObjectId to string for JSON serialization
                result["_id"] = str(result["_id"])
            
            return result
        except DuplicateKeyError:
            logger.warning(f"Duplicate employee_id attempted during update: {update_data.get('employee_id')}")
            raise
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Database connection error during update: {str(e)}")
            raise ConnectionFailure("Database connection unavailable")
    
    async def delete(self, user_id: str) -> bool:
        """
        Delete a user document by MongoDB ObjectId
        
        Args:
            user_id: String representation of MongoDB ObjectId
            
        Returns:
            True if user was deleted, False if user was not found
            
        Raises:
            InvalidId: If user_id is not a valid ObjectId format
            ConnectionFailure: If database connection fails
        """
        try:
            object_id = ObjectId(user_id)
        except (InvalidId, TypeError) as e:
            logger.warning(f"Invalid ObjectId format: {user_id}")
            raise InvalidId(f"Invalid ID format: {user_id}")
        
        try:
            result = await self.db[self.collection_name].delete_one({"_id": object_id})
            return result.deleted_count > 0
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Database connection error during delete: {str(e)}")
            raise ConnectionFailure("Database connection unavailable")


# Global repository instance
user_repository = UserRepository()
