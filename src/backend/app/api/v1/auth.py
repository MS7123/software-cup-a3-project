"""Authentication API routes — register, login, and current-user."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.core.auth import (
    create_access_token,
    get_current_user,
    get_password_hash,
    verify_password,
)
from app.db.session import session_scope
from app.models import User
from app.schemas import TokenResponse, UserLogin, UserRegister, UserResponse

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister) -> TokenResponse:
    """Register a new user account and return an access token."""
    with session_scope() as session:
        existing = session.scalar(select(User).where(User.username == payload.username))
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken.",
            )

        user = User(
            username=payload.username,
            email=payload.email,
            hashed_password=get_password_hash(payload.password),
            role="student",
        )
        session.add(user)
        session.flush()

        token = create_access_token({"sub": str(user.id), "username": user.username})
        return TokenResponse(
            access_token=token,
            user_id=user.id,
            username=user.username,
        )


@auth_router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin) -> TokenResponse:
    """Authenticate with username / password and receive a JWT token."""
    with session_scope() as session:
        user = session.scalar(select(User).where(User.username == payload.username))
        if user is None or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password.",
            )

        token = create_access_token({"sub": str(user.id), "username": user.username})
        return TokenResponse(
            access_token=token,
            user_id=user.id,
            username=user.username,
        )


@auth_router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Return the profile of the currently authenticated user."""
    return UserResponse.model_validate(current_user)
