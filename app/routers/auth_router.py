from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import create_access_token, get_current_user, hash_password, user_has_chat_access, verify_password
from app.config import FREE_MESSAGE_LIMIT
from app.database import get_db
from app.models import User
from app.schemas import AuthResponse, LoginRequest, SignUpRequest, UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _user_response(user: User) -> UserResponse:
    remaining = max(0, FREE_MESSAGE_LIMIT - user.free_messages_used)
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_premium=user.is_premium,
        premium_until=user.premium_until,
        free_messages_used=user.free_messages_used,
        free_messages_remaining=remaining,
        can_chat=user_has_chat_access(user),
    )


@router.post("/signup", response_model=AuthResponse)
def signup(payload: SignUpRequest, db: Session = Depends(get_db)) -> AuthResponse:
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name.strip(),
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id, user.email)
    return AuthResponse(access_token=token, user=_user_response(user))


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_access_token(user.id, user.email)
    return AuthResponse(access_token=token, user=_user_response(user))


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)) -> UserResponse:
    return _user_response(user)
