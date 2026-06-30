from collections.abc import Generator
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DbSession = Annotated[Session, Depends(get_db)]
Token = Annotated[str, Depends(oauth2_scheme)]


MODERN_TOKEN_CLAIMS = {"aud", "iat", "iss", "jti", "token_version"}


def _decode_access_token(token: str) -> dict:
    unverified_claims = jwt.get_unverified_claims(token)
    has_modern_claim = any(claim in unverified_claims for claim in MODERN_TOKEN_CLAIMS)
    if has_modern_claim:
        missing_claims = MODERN_TOKEN_CLAIMS - set(unverified_claims)
        if missing_claims:
            raise JWTError("Missing required token claims")
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
        )

    # Backward compatibility for tokens issued before iss/aud/iat/jti claims existed.
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        options={
            "verify_aud": False,
            "verify_iat": False,
            "verify_iss": False,
        },
    )


def _normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def get_current_user(db: DbSession, token: Token) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = _decode_access_token(token)
        subject = payload.get("sub")
        if subject is None:
            raise credentials_exception
        user_id = int(subject)
    except (JWTError, ValueError):
        raise credentials_exception from None

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise credentials_exception

    try:
        token_version = payload.get("token_version")
        if token_version is not None and int(token_version) != user.token_version:
            raise credentials_exception

        issued_at = payload.get("iat")
        if user.last_logout_at is not None and issued_at is not None:
            issued_at_datetime = datetime.fromtimestamp(int(issued_at), tz=UTC)
            if issued_at_datetime <= _normalize_datetime(user.last_logout_at):
                raise credentials_exception
    except (TypeError, ValueError):
        raise credentials_exception from None
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_admin(current_user: CurrentUser) -> User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


AdminUser = Annotated[User, Depends(require_admin)]
