# Task 3: MongoDB Repository Layer - Code Explained

## 🎯 What is the Repository Layer?

**Purpose**: The repository layer is the **only** part of your code that talks directly to MongoDB. It's like a warehouse clerk who handles all storage and retrieval operations.

**Real-World Analogy**:
```
Warehouse Clerk (Repository):
- "I'll store this box for you" (create)
- "Let me find that item" (find_by_id)
- "Here are all the items" (find_all)
- "I'll update this record" (update)
- "I'll remove that item" (delete)
```

**Why separate this layer?**
- ✅ All database code in one place
- ✅ Easy to switch databases later (MongoDB → PostgreSQL)
- ✅ Easy to test (mock the repository)
- ✅ Business logic doesn't need to know about MongoDB

---

## 📁 File: `app/repositories/user_repository.py`

### Section 1: Imports

\`\`\`python
import os
import asyncio
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError, ConnectionFailure, ServerSelectionTimeoutError
from bson import ObjectId
from bson.errors import InvalidId
import logging
\`\`\`

**What each import does**:
- `os` → Access environment variables (MONGODB_URI, DATABASE_NAME)
- `asyncio` → Async operations (sleep for retry delays)
- `Optional, List` → Type hints for return values
- `AsyncIOMotorClient` → Async MongoDB driver (non-blocking)
- `DuplicateKeyError` → Unique constraint violation
- `ConnectionFailure` → Can't connect to MongoDB
- `ObjectId` → MongoDB's ID type (24-character hex)
- `InvalidId` → Invalid ObjectId format error
- `logging` → Log connection events

---

### Section 2: Class Definition

\`\`\`python
class UserRepository:
    """Repository class for MongoDB user operations with connection retry logic"""
    
    def __init__(self):
        """Initialize repository with MongoDB connection"""
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.collection_name = "users"
        self._connection_retries = 3
        self._base_retry_delay = 1  # seconds
\`\`\`

**Breaking it down**:

**`self.client: Optional[AsyncIOMotorClient] = None`**
- Stores the MongoDB connection client
- `Optional` means it can be `None` (not connected yet)
- Starts as `None` until `connect()` is called

**`self.collection_name = "users"`**
- MongoDB collection name (like a table in SQL)
- Our user documents are stored in the "users" collection

**`self._connection_retries = 3`**
- How many times to retry if connection fails
- `_` prefix = private variable (internal use only)

**`self._base_retry_delay = 1`**
- Base delay in seconds between retries
- Uses exponential backoff: 1s → 2s → 4s

---

### Section 3: Connection with Retry Logic

\`\`\`python
async def connect(self):
    """Establish MongoDB connection with retry logic and exponential backoff"""
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    database_name = os.getenv("DATABASE_NAME", "user_api")
\`\`\`

**Environment Variables**:
- `os.getenv("MONGODB_URI", "default")` → Get from .env or use default
- Example: `MONGODB_URI=mongodb://localhost:27017`

\`\`\`python
    for attempt in range(self._connection_retries):
        try:
            logger.info(f"Attempting MongoDB connection (attempt {attempt + 1}/{self._connection_retries})...")
\`\`\`

**Retry Loop**:
- Tries up to 3 times (attempts 0, 1, 2)
- Logs each attempt: "Attempting MongoDB connection (attempt 1/3)..."

\`\`\`python
            self.client = AsyncIOMotorClient(
                mongodb_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )
\`\`\`

**Create MongoDB Client**:
- `serverSelectionTimeoutMS=5000` → 5 seconds to find a server
- `connectTimeoutMS=5000` → 5 seconds to establish connection
- If MongoDB is down, fails after 5 seconds (not forever)

\`\`\`python
            # Test the connection
            await self.client.admin.command('ping')
\`\`\`

**Test Connection**:
- Sends a "ping" command to MongoDB
- If this succeeds, connection is working ✅
- If this fails, MongoDB is unreachable ❌

\`\`\`python
            # Set database reference
            self.db = self.client[database_name]
            
            # Create unique index on employee_id
            await self._ensure_indexes()
\`\`\`

**Setup Database**:
- `self.db = self.client[database_name]` → Select database
- `_ensure_indexes()` → Create unique index on employee_id

\`\`\`python
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            retry_delay = self._base_retry_delay * (2 ** attempt)  # Exponential backoff
            logger.error(f"MongoDB connection failed: {str(e)}")
            
            if attempt < self._connection_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                logger.error("Failed to connect to MongoDB after all retry attempts")
                raise ConnectionFailure("Unable to establish MongoDB connection")
\`\`\`

**Exponential Backoff**:
- **Attempt 1**: `1 * (2^0) = 1 * 1 = 1 second`
- **Attempt 2**: `1 * (2^1) = 1 * 2 = 2 seconds`
- **Attempt 3**: `1 * (2^2) = 1 * 4 = 4 seconds`

**Why exponential backoff?**
- Gives MongoDB time to recover
- Doesn't hammer the server with rapid retries
- Standard pattern for distributed systems

**Flow Example**:
\`\`\`
Attempt 1 → Fails → Wait 1 second
Attempt 2 → Fails → Wait 2 seconds
Attempt 3 → Fails → Raise error (give up)
\`\`\`

---

### Section 4: Create Index

\`\`\`python
async def _ensure_indexes(self):
    """Create necessary indexes for the users collection"""
    try:
        await self.db[self.collection_name].create_index(
            "employee_id",
            unique=True,
            name="employee_id_unique_idx"
        )
        logger.info("Created unique index on employee_id field")
    except Exception as e:
        logger.warning(f"Index creation warning: {str(e)}")
\`\`\`

**What is an index?**

**Without Index**:
\`\`\`
Finding employee_id "EMP001":
Check document 1 → Not it
Check document 2 → Not it
Check document 3 → Not it
...
Check document 10,000 → Found it!

Time: Slow (scans all documents)
\`\`\`

**With Index**:
\`\`\`
Finding employee_id "EMP001":
Look in index → Points to document 5
Get document 5 → Found it!

Time: Fast (direct lookup)
\`\`\`

**Unique Constraint**:
- `unique=True` → No two documents can have same employee_id
- MongoDB enforces this at database level
- Trying to insert duplicate → `DuplicateKeyError`

---

### Section 5: Create Operation

\`\`\`python
async def create(self, user_data: dict) -> dict:
    """Insert a new user document into MongoDB"""
    try:
        result = await self.db[self.collection_name].insert_one(user_data)
        created_user = await self.find_by_id(str(result.inserted_id))
        return created_user
    except DuplicateKeyError:
        logger.warning(f"Duplicate employee_id attempted: {user_data.get('employee_id')}")
        raise
\`\`\`

**Breaking it down**:

**`await self.db[self.collection_name].insert_one(user_data)`**
- Inserts document into "users" collection
- `await` = asynchronous (doesn't block)
- Returns result with `inserted_id`

**`created_user = await self.find_by_id(str(result.inserted_id))`**
- Retrieve the newly created document
- Why? To get it with `_id` as string (for JSON serialization)

**`except DuplicateKeyError:`**
- Catches unique constraint violation
- Re-raises the error (service layer handles it)

**Example**:
\`\`\`python
user_data = {
    "user_name": "John Doe",
    "employee_id": "EMP001",
    "salary": 75000.50,
    ...
}

result = await repository.create(user_data)
# Returns: {"_id": "507f...", "user_name": "John Doe", ...}
\`\`\`

---

### Section 6: Find by ID

\`\`\`python
async def find_by_id(self, user_id: str) -> Optional[dict]:
    """Find a user document by MongoDB ObjectId"""
    try:
        object_id = ObjectId(user_id)
    except (InvalidId, TypeError) as e:
        logger.warning(f"Invalid ObjectId format: {user_id}")
        raise InvalidId(f"Invalid ID format: {user_id}")
\`\`\`

**ObjectId Validation**:
- MongoDB uses special ObjectId format (24-character hex)
- Valid: `"507f1f77bcf86cd799439011"` ✅
- Invalid: `"123"`, `"not-an-id"`, `"abc"` ❌

**`ObjectId(user_id)`**:
- Converts string to ObjectId type
- Validates format automatically
- Raises `InvalidId` if invalid

\`\`\`python
    user = await self.db[self.collection_name].find_one({"_id": object_id})
    if user:
        user["_id"] = str(user["_id"])
    return user
\`\`\`

**Find Document**:
- `find_one({"_id": object_id})` → Query by ID
- Returns document or `None`

**Convert ObjectId to String**:
- MongoDB stores: `ObjectId("507f1f77bcf86cd799439011")`
- JSON needs: `"507f1f77bcf86cd799439011"` (string)
- `str(user["_id"])` converts it

---

### Section 7: Find All

\`\`\`python
async def find_all(self) -> List[dict]:
    """Retrieve all user documents from MongoDB"""
    try:
        cursor = self.db[self.collection_name].find({})
        users = await cursor.to_list(length=None)
        
        for user in users:
            user["_id"] = str(user["_id"])
        
        return users
\`\`\`

**Breaking it down**:

**`cursor = self.db[self.collection_name].find({})`**
- `find({})` → No filter, get all documents
- Returns a cursor (iterator, not actual data yet)

**`users = await cursor.to_list(length=None)`**
- Convert cursor to list
- `length=None` → Get all documents (no limit)

**Convert all IDs to strings**:
\`\`\`python
for user in users:
    user["_id"] = str(user["_id"])
\`\`\`

**Example Result**:
\`\`\`python
[
    {"_id": "507f...", "user_name": "John", ...},
    {"_id": "508a...", "user_name": "Jane", ...}
]
\`\`\`

---

### Section 8: Update Operation

\`\`\`python
async def update(self, user_id: str, update_data: dict) -> Optional[dict]:
    """Update a user document and return the updated version"""
    try:
        object_id = ObjectId(user_id)
    except (InvalidId, TypeError) as e:
        raise InvalidId(f"Invalid ID format: {user_id}")
    
    result = await self.db[self.collection_name].find_one_and_update(
        {"_id": object_id},
        {"$set": update_data},
        return_document=True
    )
\`\`\`

**MongoDB Update Query**:
- `{"_id": object_id}` → Which document to update
- `{"$set": update_data}` → What fields to update
- `return_document=True` → Return updated document (not old one)

**`$set` Operator**:
\`\`\`python
# Only updates specified fields
{"$set": {"salary": 80000, "active_status": False}}

# Other fields remain unchanged ✅
\`\`\`

**Example**:
\`\`\`python
# Before update:
{"_id": "507f...", "user_name": "John", "salary": 75000, "address": "123 Main St"}

# Update call:
update("507f...", {"salary": 80000})

# After update:
{"_id": "507f...", "user_name": "John", "salary": 80000, "address": "123 Main St"}
#                                        ↑ Updated      ↑ Unchanged
\`\`\`

---

### Section 9: Delete Operation

\`\`\`python
async def delete(self, user_id: str) -> bool:
    """Delete a user document by MongoDB ObjectId"""
    try:
        object_id = ObjectId(user_id)
    except (InvalidId, TypeError) as e:
        raise InvalidId(f"Invalid ID format: {user_id}")
    
    result = await self.db[self.collection_name].delete_one({"_id": object_id})
    return result.deleted_count > 0
\`\`\`

**Breaking it down**:

**`result = await ...delete_one({"_id": object_id})`**
- Deletes the document matching the ID
- Returns result with `deleted_count`

**`return result.deleted_count > 0`**
- If `deleted_count = 1` → Document was deleted → `True` ✅
- If `deleted_count = 0` → Document didn't exist → `False` ❌

**Example**:
\`\`\`python
# Document exists:
await repository.delete("507f1f77bcf86cd799439011")
# Returns: True (deleted)

# Document doesn't exist:
await repository.delete("999999999999999999999999")
# Returns: False (nothing to delete)
\`\`\`

---

## ✅ Summary: What We Learned

### Key Concepts:

**1. Async/Await**
- Non-blocking database operations
- Can handle many requests simultaneously

**2. Connection Retry with Exponential Backoff**
- Retry 3 times with increasing delays
- 1s → 2s → 4s
- Graceful handling of temporary network issues

**3. ObjectId Handling**
- MongoDB's special ID format (24-char hex)
- Must convert to string for JSON
- Validate before querying

**4. Unique Index**
- Prevents duplicate employee_ids
- Enforced at database level
- Raises `DuplicateKeyError` on violation

**5. CRUD Operations**
- **C**reate → `insert_one()`
- **R**ead → `find_one()`, `find()`
- **U**pdate → `find_one_and_update()` with `$set`
- **D**elete → `delete_one()`

---

**Next**: Task 4 - File Handler Code Explained
