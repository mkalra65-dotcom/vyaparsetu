from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from fastapi import Depends

from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserRead

router = APIRouter()


@router.post("/login", response_model=Token)
def login(
    db: DbSession,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = db.query(User).filter(User.email == form_data.username.lower()).first()
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user.id),
        expires_delta=access_token_expires,
        token_version=user.token_version,
    )
    return Token(access_token=access_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(db: DbSession, current_user: CurrentUser) -> None:
    current_user.token_version += 1
    current_user.last_logout_at = datetime.now(UTC)
    db.add(current_user)
    db.commit()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: DbSession) -> User:
    existing_user = db.query(User).filter(User.email == user_in.email.lower()).first()
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    user = User(
        email=user_in.email.lower(),
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        is_active=True,
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
