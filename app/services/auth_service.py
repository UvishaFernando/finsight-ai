from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timezone

from app.models.user import User, UserRole
from app.core.security import hash_password, verify_password,create_access_token, create_refresh_token, decode_token

from app.core.config import settings
from app.schemas.user import UserRegister, UserLogin


class AuthService:
    @staticmethod
    def register(db: Session, data: UserRegister) :
        existing = db.query(User).filter(User.email == data.email.lower()).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="An account with this email already exists")
        user = User(
            email=data.email.lower(),
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
            role=UserRole.user,
            is_active=True,
            is_verified=False,  
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def login(db: Session, data: UserLogin) :
        user = db.query(User).filter(User.email == data.email.lower()).first()

        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Incorrect email or password",headers={"WWW-Authenticate": "Bearer"},)

        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Account is deactivated. Contact support.")
            
        user.last_login = datetime.now(timezone.utc)
        db.commit()

        return AuthService._build_token_response(user)

    @staticmethod
    def refresh(db: Session, refresh_token: str) :
        payload = decode_token(refresh_token)

        if not payload or payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid or expired refresh token")

        user = db.query(User).filter(User.id == int(payload["sub"])).first()
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

        return AuthService._build_token_response(user)

    @staticmethod
    def change_password(db: Session,user: User,current_password: str,new_password: str) :
        if not verify_password(current_password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Current password is incorrect")
        user.hashed_password = hash_password(new_password)
        db.commit()

    @staticmethod
    def get_current_user(db: Session, token: str) :
        payload = decode_token(token)

        if not payload or payload.get("type") != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Could not validate credentials",headers={"WWW-Authenticate": "Bearer"},)

        user = db.query(User).filter(User.id == int(payload["sub"])).first()
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="User not found or inactive")
        return user

    @staticmethod
    def _build_token_response(user: User) :
        expire_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        return {
            "access_token": create_access_token(user.id),
            "refresh_token": create_refresh_token(user.id),
            "token_type": "bearer",
            "expires_in": expire_seconds,
        }
