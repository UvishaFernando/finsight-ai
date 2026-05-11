from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.models.user import User, UserRole
from app.services.auth_service import AuthService

bearer_scheme = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),db: Session = Depends(get_db),) :
    return AuthService.get_current_user(db, credentials.credentials)


def get_current_active_user(current_user: User = Depends(get_current_user),) :
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Account is deactivated")
    return current_user


def require_admin(current_user: User = Depends(get_current_active_user),) :
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user
