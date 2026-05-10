from typing import Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.user import UserDocument
from app.schemas.user import UserRegisterRequest, UserResponse
from app.core.security import hash_password
from fastapi import HTTPException, status


async def get_user_by_email(
    db: AsyncIOMotorDatabase, email: str
) -> Optional[UserDocument]:
    data = await db.users.find_one({"email": email})
    if data:
        return UserDocument.from_dict(data)
    return None


async def get_user_by_id(
    db: AsyncIOMotorDatabase, user_id: str
) -> Optional[UserDocument]:
    data = await db.users.find_one({"_id": ObjectId(user_id)})
    if data:
        return UserDocument.from_dict(data)
    return None


async def create_user(
    db: AsyncIOMotorDatabase, payload: UserRegisterRequest
) -> UserDocument:
    existing = await get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = UserDocument(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
    )
    await db.users.insert_one(user.to_dict())
    return user


def format_user_response(user: UserDocument) -> UserResponse:
    return UserResponse(
        id=str(user._id),
        email=user.email,
        full_name=user.full_name,
        created_at=user.created_at,
        is_active=user.is_active,
    )
