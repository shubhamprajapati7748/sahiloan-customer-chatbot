# Production-Grade Architecture Guide

## 📋 Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Layer Responsibilities](#layer-responsibilities)
3. [Service Layer Placement](#service-layer-placement)
4. [Data Flow](#data-flow)
5. [Dependency Injection](#dependency-injection)
6. [Best Practices](#best-practices)

---

## 🏗️ Architecture Overview

Your application follows **Clean Architecture** / **Layered Architecture** principles:

```
┌─────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                   │
│              infrastructure/api/                          │
│  - Receives HTTP requests                                │
│  - Validates input (Pydantic models)                     │
│  - Calls Application Services                            │
│  - Returns HTTP responses                                │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│              Application Layer (Services)                 │
│              application/                                │
│  - Business logic                                        │
│  - Orchestrates repositories                             │
│  - Validates business rules                              │
│  - Handles transactions                                  │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│              Domain Layer                                 │
│              domain/                                      │
│  - Domain exceptions                                     │
│  - Domain utilities                                      │
│  - Business rules (pure logic)                          │
└─────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│          Infrastructure Layer (Data Access)               │
│          infrastructure/db/postgres/                     │
│  - Repositories (data access only)                       │
│  - Models (SQLAlchemy ORM)                               │
│  - Database sessions                                     │
└─────────────────────────────────────────────────────────┘
```

---

## 📦 Layer Responsibilities

### 1. **Infrastructure Layer** (`infrastructure/`)
**Purpose**: External concerns - database, APIs, external services

**Contains**:
- `db/postgres/repositories/` - **Data access only** (no business logic)
- `db/postgres/models/` - SQLAlchemy ORM models
- `api/` - FastAPI endpoints
- `llm_providers/` - External LLM integrations

**Rules**:
- ✅ Repositories only do CRUD operations
- ✅ No business logic in repositories
- ✅ Repositories return domain models
- ❌ No validation logic
- ❌ No business rules

### 2. **Application Layer** (`application/`)
**Purpose**: Business logic and orchestration

**Contains**:
- `user_service/` - User business logic
- `loan_service/` - Loan business logic
- `chat_service/` - Chat workflow logic
- `service_factory.py` - Dependency injection

**Rules**:
- ✅ Contains all business logic
- ✅ Validates business rules
- ✅ Orchestrates multiple repositories
- ✅ Handles transactions
- ✅ Uses repositories (not direct DB access)
- ❌ No direct SQLAlchemy queries
- ❌ No HTTP concerns

### 3. **Domain Layer** (`domain/`)
**Purpose**: Pure domain logic, independent of infrastructure

**Contains**:
- `exceptions.py` - Domain exceptions
- `utils.py` - Domain utilities
- Business rules (pure functions)

**Rules**:
- ✅ No dependencies on infrastructure
- ✅ Pure Python code
- ✅ Reusable across layers

---

## 🎯 Service Layer Placement

### ✅ **CORRECT: Services in `application/`**

```
src/sahiloan_chatbot/
├── application/
│   ├── user_service/          ← ✅ Services here
│   │   ├── __init__.py
│   │   └── user_service.py
│   ├── loan_service/           ← ✅ Services here
│   │   ├── __init__.py
│   │   └── loan_service.py
│   └── service_factory.py      ← ✅ Dependency injection
│
└── infrastructure/
    └── db/postgres/
        └── repositories/        ← ✅ Repositories here
            ├── user_repository.py
            └── loan_repository.py
```

### ❌ **WRONG: Services in `infrastructure/`**

```
❌ infrastructure/db/postgres/services/  # DON'T DO THIS
```

**Why?**
- Services contain **business logic**, not infrastructure concerns
- Violates separation of concerns
- Makes testing harder
- Breaks Clean Architecture principles

---

## 🔄 Data Flow

### Example: Creating a User

```
1. HTTP Request
   POST /api/v1/users
   ↓
2. API Endpoint (infrastructure/api/user_endpoints.py)
   - Validates request with Pydantic
   - Gets DB session
   - Creates ServiceFactory
   ↓
3. Service Layer (application/user_service/user_service.py)
   - Validates business rules (email uniqueness)
   - Calls UserRepository
   - Handles errors
   ↓
4. Repository Layer (infrastructure/db/postgres/repositories/user_repository.py)
   - Executes SQL query
   - Returns User model
   ↓
5. Service Layer (back)
   - Returns User to API
   ↓
6. API Endpoint (back)
   - Converts to response model
   - Returns HTTP response
```

---

## 💉 Dependency Injection

### Service Factory Pattern

```python
# application/service_factory.py
class ServiceFactory:
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_service(self) -> UserService:
        user_repo = UserRepository(self.db)
        return UserService(user_repository=user_repo)
```

### Usage in API

```python
# infrastructure/api/user_endpoints.py
@router.post("/users")
async def create_user(
    request: UserCreateRequest,
    db: Session = Depends(get_db),
):
    factory = ServiceFactory(db)
    user_service = factory.get_user_service()
    
    user = user_service.create_user(...)
    return user
```

**Benefits**:
- ✅ Easy to test (mock repositories)
- ✅ Clear dependencies
- ✅ Single responsibility
- ✅ Follows SOLID principles

---

## ✅ Best Practices

### 1. **Repository Pattern**
```python
# ✅ GOOD: Repository only does data access
class UserRepository(BaseRepository[User]):
    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()
```

### 2. **Service Layer**
```python
# ✅ GOOD: Service contains business logic
class UserService:
    def create_user(self, email: str, ...) -> User:
        # Business logic: Check uniqueness
        if self.user_repository.email_exists(email):
            raise ValidationError("Email exists")
        
        # Create through repository
        return self.user_repository.create(email=email, ...)
```

### 3. **Error Handling**
```python
# ✅ GOOD: Domain exceptions in service
try:
    user = user_service.get_user_by_id(user_id)
except NotFoundError:
    raise HTTPException(404, "User not found")
```

### 4. **Type Hints**
```python
# ✅ GOOD: Full type hints
def get_user_by_id(self, user_id: UUID) -> User:
    ...
```

### 5. **Transaction Management**
```python
# ✅ GOOD: Service handles transactions
def create_user_with_loan(self, user_data, loan_data):
    user = self.user_repository.create(**user_data)
    loan = self.loan_repository.create(user_id=user.id, **loan_data)
    self.db.commit()  # Atomic operation
    return user, loan
```

---

## 🚀 Production-Grade Checklist

- [x] **Separation of Concerns**: Each layer has clear responsibilities
- [x] **Repository Pattern**: Data access abstracted from business logic
- [x] **Service Layer**: Business logic in application layer
- [x] **Dependency Injection**: Services receive repositories via constructor
- [x] **Error Handling**: Domain exceptions, proper HTTP status codes
- [x] **Type Safety**: Full type hints throughout
- [x] **Testability**: Easy to mock repositories for unit tests
- [x] **Scalability**: Can add new services/repositories easily
- [x] **Maintainability**: Clear structure, easy to navigate

---

## 📚 Summary

**Where to create service folders?**
- ✅ **`application/user_service/`** - User business logic
- ✅ **`application/loan_service/`** - Loan business logic
- ❌ **NOT in `infrastructure/`** - That's for data access only

**Key Principles**:
1. **Repositories** = Data access (infrastructure)
2. **Services** = Business logic (application)
3. **API** = HTTP handling (infrastructure/api)
4. **Domain** = Pure logic (domain)

This architecture is **production-grade** and follows industry best practices! 🎉
