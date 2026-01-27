# """Example API endpoints demonstrating service layer usage."""

# from uuid import UUID

# from fastapi import APIRouter, Depends, HTTPException, status
# from pydantic import BaseModel, EmailStr
# from sqlalchemy.orm import Session

# from sahiloan_chatbot.application.service_factory import ServiceFactory
# from sahiloan_chatbot.domain.exceptions import NotFoundError, ValidationError
# from sahiloan_chatbot.infrastructure.db.postgres.sessions import get_db_session

# router = APIRouter(prefix="/api/v1/users", tags=["users"])


# # Request/Response Models
# class UserCreateRequest(BaseModel):
#     email: EmailStr
#     phone_number: str
#     first_name: str | None = None
#     last_name: str | None = None


# class UserResponse(BaseModel):
#     id: str
#     email: str
#     phone_number: str
#     first_name: str | None
#     last_name: str | None

#     class Config:
#         from_attributes = True


# class UserUpdateRequest(BaseModel):
#     first_name: str | None = None
#     last_name: str | None = None
#     email: EmailStr | None = None
#     phone_number: str | None = None


# @router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
# async def create_user(
#     request: UserCreateRequest,
#     db: Session = Depends(get_db_session),
# ):
#     """
#     Create a new user.

#     This endpoint demonstrates the proper flow:
#     1. API Layer receives request
#     2. Creates service factory with DB session
#     3. Gets service from factory
#     4. Service handles business logic
#     5. Returns response
#     """
#     try:
#         factory = ServiceFactory(db)
#         user_service = factory.get_user_service()

#         user = user_service.create_user(
#             email=request.email,
#             phone_number=request.phone_number,
#             first_name=request.first_name,
#             last_name=request.last_name,
#         )

#         return UserResponse(
#             id=str(user.id),
#             email=user.email,
#             phone_number=user.phone_number,
#             first_name=user.first_name,
#             last_name=user.last_name,
#         )
#     except ValidationError as e:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
#     except Exception:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Internal server error",
#         )


# @router.get("/{user_id}", response_model=UserResponse)
# async def get_user(
#     user_id: UUID,
#     db: Session = Depends(get_db_session),
# ):
#     """Get user by ID."""
#     try:
#         factory = ServiceFactory(db)
#         user_service = factory.get_user_service()

#         user = user_service.get_user_by_id(user_id)
#         return UserResponse(
#             id=str(user.id),
#             email=user.email,
#             phone_number=user.phone_number,
#             first_name=user.first_name,
#             last_name=user.last_name,
#         )
#     except NotFoundError as e:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
#     except Exception:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Internal server error",
#         )


# @router.put("/{user_id}", response_model=UserResponse)
# async def update_user(
#     user_id: UUID,
#     request: UserUpdateRequest,
#     db: Session = Depends(get_db_session),
# ):
#     """Update user information."""
#     try:
#         factory = ServiceFactory(db)
#         user_service = factory.get_user_service()

#         user = user_service.update_user(
#             user_id=user_id,
#             first_name=request.first_name,
#             last_name=request.last_name,
#             email=request.email,
#             phone_number=request.phone_number,
#         )

#         return UserResponse(
#             id=str(user.id),
#             email=user.email,
#             phone_number=user.phone_number,
#             first_name=user.first_name,
#             last_name=user.last_name,
#         )
#     except NotFoundError as e:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
#     except ValidationError as e:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
#     except Exception:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Internal server error",
#         )


# @router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_user(
#     user_id: UUID,
#     db: Session = Depends(get_db_session),
# ):
#     """Delete a user."""
#     try:
#         factory = ServiceFactory(db)
#         user_service = factory.get_user_service()

#         user_service.delete_user(user_id)
#         return None
#     except NotFoundError as e:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
#     except Exception:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Internal server error",
#         )
