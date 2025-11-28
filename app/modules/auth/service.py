from typing import Optional, List
from sqlalchemy.orm import Session
from app.modules.auth.models import User
from app.modules.auth.schemas import UserCreate, UserUpdate
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


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """
    Get a list of users.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of User objects
    """
    return repository.get_users(db, skip=skip, limit=limit)


def update_user(db: Session, user_id: str, user_update: UserUpdate) -> Optional[User]:
    """
    Update a user.
    
    Args:
        db: Database session
        user_id: ID of user to update
        user_update: User update data
        
    Returns:
        Updated User object if found, None otherwise
    """
    return repository.update_user(db, user_id, user_update)


def delete_user(db: Session, user_id: str) -> bool:
    """
    Delete a user.
    
    Args:
        db: Database session
        user_id: ID of user to delete
        
    Returns:
        True if user was deleted, False if not found
    """
    return repository.delete_user(db, user_id)
