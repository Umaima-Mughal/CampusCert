"""
app/auth/dependencies.py

Reusable FastAPI "Depends()" functions that other modules (exams,
questions, attempts, security, analytics) will import to:
  1. Find out who's currently logged in
  2. Restrict a route to certain roles (RBAC)

Example usage in someone else's route file:

    from app.auth.dependencies import get_current_user, require_role

    @router.post("/exams")
    def create_exam(user = Depends(require_role("admin", "examiner"))):
        ...
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.auth.security import decode_token
from app.auth.models import User

# Points Swagger UI / clients at the login endpoint for getting a token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise credentials_error
        user_id = payload.get("sub")
    except JWTError:
        raise credentials_error

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise credentials_error
    return user


def require_role(*allowed_roles: str):
    """
    Factory function — call it with the roles allowed to access a route.
    Returns a dependency FastAPI can use.
    """
    def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role.name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to perform this action",
            )
        return user
    return role_checker
