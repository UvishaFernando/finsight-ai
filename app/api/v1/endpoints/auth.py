from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.schemas.user import UserRegister, UserLogin, TokenRefresh,UserResponse, TokenResponse, AuthResponse, MessageResponse,PasswordChange
from app.services.auth_service import AuthService
from app.api.v1.dependencies import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register",response_model=AuthResponse,status_code=status.HTTP_201_CREATED,summary="Register a new user account")
def register(data: UserRegister, db: Session = Depends(get_db)):
    user = AuthService.register(db, data)
    tokens = AuthService._build_token_response(user)
    return AuthResponse(user=UserResponse.model_validate(user),tokens=TokenResponse(**tokens))


@router.post("/login",response_model=AuthResponse,summary="Login and receive JWT tokens",)
def login(data: UserLogin, db: Session = Depends(get_db)):
    tokens = AuthService.login(db, data)
    user = db.query(User).filter( User.email == data.email.lower()).first()
    return AuthResponse(user=UserResponse.model_validate(user),tokens=TokenResponse(**tokens))


@router.post("/refresh",response_model=TokenResponse,summary="Get a new access token using refresh token",)
def refresh_token(data: TokenRefresh, db: Session = Depends(get_db)):
    tokens = AuthService.refresh(db, data.refresh_token)
    return TokenResponse(**tokens)


@router.get( "/me",response_model=UserResponse,summary="Get current user profile",)
def get_me(current_user: User = Depends(get_current_active_user)):
    return UserResponse.model_validate(current_user)


@router.put("/change-password",response_model=MessageResponse,summary="Change your password",)
def change_password(data: PasswordChange,current_user: User = Depends(get_current_active_user),db: Session = Depends(get_db),):
    AuthService.change_password(db, current_user, data.current_password, data.new_password)
    return MessageResponse(message="Password changed successfully")


@router.post("/logout",response_model=MessageResponse,summary="Logout (client-side token discard)",)
def logout(current_user: User = Depends(get_current_active_user)):
    return MessageResponse(message=f"Goodbye, {current_user.full_name}!")
