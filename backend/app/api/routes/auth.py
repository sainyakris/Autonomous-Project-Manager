from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.database import get_db
from app.models.models import User
from app.schemas.auth import LoginRequest, Token, UserOut, UserRegister

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    email = data.email.lower()
    if await db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    user = User(
        email=email,
        name=data.name,
        hashed_password=hash_password(data.password),
        skills=data.skills,
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:  # two simultaneous signups can slip past the check above
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    await db.refresh(user)  # loads created_at, which the database generated
    return user


@router.post("/login", response_model=Token)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.email == data.email.lower()))
    # One generic message for both cases, so attackers can't tell which emails exist
    if user is None or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token({"sub": user.id}))


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return current_user