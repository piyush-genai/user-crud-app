# FastAPI MongoDB User CRUD API

A production-ready REST API for managing employee records with FastAPI and MongoDB. Built using Specification-Driven Development (SDD) methodology.

## 📋 Project Overview

This is an employee management system that provides CRUD (Create, Read, Update, Delete) operations for managing user records. The system includes profile photo management and comprehensive input validation.

**Key Features:**
- ✅ Full CRUD operations for employee records
- ✅ Profile photo upload and management
- ✅ Input validation with detailed error messages
- ✅ MongoDB with async operations
- ✅ Auto-generated interactive API documentation
- ✅ Clean three-layer architecture

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│          USER (HR Person/App)           │
└──────────────────┬──────────────────────┘
                   │ HTTP Request
                   ▼
┌─────────────────────────────────────────┐
│         ROUTER LAYER                    │
│    (Handles HTTP requests)              │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│         SERVICE LAYER                   │
│    (Business logic & validation)        │
└──────────────┬────────────┬─────────────┘
               │            │
               ▼            ▼
┌──────────────────┐  ┌──────────────────┐
│   REPOSITORY     │  │   FILE HANDLER   │
│   (MongoDB ops)  │  │   (Photo storage)│
└────────┬─────────┘  └────────┬─────────┘
         │                     │
         ▼                     ▼
  [MongoDB Database]    [File System]
```

## 🛠️ Tech Stack

- **FastAPI** - Modern async web framework
- **MongoDB** - NoSQL database
- **Motor** - Async MongoDB driver
- **Pydantic** - Data validation
- **Python 3.8+** - Programming language
- **Uvicorn** - ASGI web server

## 📁 Project Structure

```
user-crud-app/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── models/              # Pydantic data models
│   │   └── user_models.py
│   ├── repositories/        # Database operations
│   │   └── user_repository.py (TODO)
│   ├── services/            # Business logic
│   │   ├── user_service.py (TODO)
│   │   └── file_handler.py (TODO)
│   └── routers/             # API endpoints
│       └── user_router.py (TODO)
├── uploads/                 # Profile photo storage
├── docs/                    # Project documentation
│   ├── README.md
│   ├── 01-project-overview.md
│   ├── 02-kiro-sdd-explained.md
│   ├── 03-task1-project-structure.md
│   └── 04-task2-pydantic-models-explained.md
├── .kiro/specs/            # Specification documents
│   └── fastapi-mongodb-user-crud/
│       ├── requirements.md
│       ├── design.md
│       └── tasks.md
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
└── README.md              # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- MongoDB installed and running
- Git

### Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd user-crud-app
   ```

2. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your MongoDB connection details
   ```

5. **Run the application:**
   ```bash
   uvicorn app.main:app --reload
   ```

6. **Access the API:**
   - API: http://localhost:8000
   - Interactive docs: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc

## 📖 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root endpoint |
| GET | `/health` | Health check |
| POST | `/users` | Create new user ⏳ |
| GET | `/users/{id}` | Get user by ID ⏳ |
| GET | `/users` | List all users ⏳ |
| PUT | `/users/{id}` | Update user ⏳ |
| DELETE | `/users/{id}` | Delete user ⏳ |
| POST | `/users/{id}/photo` | Upload/replace profile photo ⏳ |

⏳ = Implementation in progress

## 📊 Development Progress

- [x] **Task 1**: Project structure and dependencies ✅
- [x] **Task 2**: Pydantic data models ✅
- [ ] **Task 3**: MongoDB repository layer (Next)
- [ ] **Task 4**: File storage handler
- [ ] **Task 5**: User service layer
- [ ] **Task 6**: API router endpoints
- [ ] **Task 7**: Application configuration
- [ ] **Task 8**: Documentation
- [ ] **Task 9**: Manual testing

## 📚 Documentation

Comprehensive documentation is available in the `docs/` folder:

- **[Start Here](./docs/README.md)** - Documentation index
- **[Project Overview](./docs/01-project-overview.md)** - What we're building and why
- **[SDD Methodology](./docs/02-kiro-sdd-explained.md)** - Specification-Driven Development
- **[Project Structure](./docs/03-task1-project-structure.md)** - Files and folders explained
- **[Pydantic Models](./docs/04-task2-pydantic-models-explained.md)** - Data validation explained

## 🎯 Specification-Driven Development

This project follows SDD methodology with three core specification documents:

1. **[requirements.md](./.kiro/specs/fastapi-mongodb-user-crud/requirements.md)** - What features we need
2. **[design.md](./.kiro/specs/fastapi-mongodb-user-crud/design.md)** - How we'll build it
3. **[tasks.md](./.kiro/specs/fastapi-mongodb-user-crud/tasks.md)** - Step-by-step implementation plan

## 🧪 Testing

Testing framework will be added in later tasks. Planned testing:
- Unit tests for models, services, and repositories
- Integration tests for API endpoints
- Manual testing via Swagger UI

## 🔒 Environment Variables

Create a `.env` file based on `.env.example`:

```env
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=user_crud_db
UPLOAD_DIR=uploads
MAX_FILE_SIZE=5242880  # 5MB
```

## 📝 Data Model

Employee record structure:

```json
{
  "user_name": "John Doe",
  "address": "123 Main St, Springfield, IL 62701",
  "employee_id": "EMP001",
  "salary": 75000.50,
  "gender": "Male",
  "joining_date": "2024-01-15",
  "active_status": true,
  "profile_photo_url": "/uploads/507f1f77bcf86cd799439011_profile.jpg"
}
```

## 🤝 Contributing

1. Read the specifications in `.kiro/specs/`
2. Follow the task list in `tasks.md`
3. Maintain the three-layer architecture
4. Write tests for new features
5. Update documentation as needed

## 📄 License

This project is for educational purposes.

## 👥 Authors

- Piyush - Initial work

## 🙏 Acknowledgments

- Built with Kiro AI-powered development environment
- Follows Specification-Driven Development methodology
- Uses FastAPI and MongoDB best practices

---

**Status**: 🚧 In Development - Tasks 1-2 Complete
