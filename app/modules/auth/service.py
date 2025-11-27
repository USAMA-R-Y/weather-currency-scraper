from typing import Optional
from sqlalchemy.orm import Session
from app.modules.auth.models import User
from app.modules.auth.schemas import UserCreate
from app.modules.auth.security import verify_password, create_access_token
from app.modules.auth import repository


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    Authenticate a user by username and password.
    
    Args:
        db: Database session
        username: Username to authenticate
        password: Plain text password
        
    Returns:
        User object if authentication successful, None otherwise
    """
    user = repository.get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def register_user(db: Session, user_data: UserCreate) -> Optional[User]:
    """
    Register a new user.
    
    Args:
        db: Database session
        user_data: User registration data
        
    Returns:
        Created User object if successful, None if username/email already exists
    """
    # Check if username already exists
    if repository.get_user_by_username(db, user_data.username):
        return None
    
    # Check if email already exists
    if repository.get_user_by_email(db, user_data.email):
        return None
    
    # Create the user
    return repository.create_user(db, user_data)


def create_user_token(user: User) -> str:
    """
    Create a JWT access token for a user.
    
    Args:
        user: User object to create token for
        
    Returns:
        JWT access token string
    """
    token_data = {
        "sub": user.username,
        "permissions": user.permissions
    }
    return create_access_token(token_data)
