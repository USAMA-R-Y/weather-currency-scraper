from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.modules.auth.models import User
from app.modules.auth.schemas import UserCreate, UserInDB, UserUpdate, Token
from app.modules.auth.dependencies import (
    get_current_active_user,
    require_superuser
)
from app.modules.auth import service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserInDB, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    
    Args:
        user_data: User registration data
        db: Database session
        
    Returns:
        The created user
        
    Raises:
        HTTPException: If username or email already exists
    """
    user = service.register_user(db, user_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    return user


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login and receive a JWT access token.
    
    Args:
        form_data: OAuth2 form with username and password
        db: Database session
        
    Returns:
        Access token and token type
        
    Raises:
        HTTPException: If credentials are invalid
    """
    user = service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    access_token = service.create_user_token(user)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserInDB)
def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """
    Get current user information.
    
    Args:
        current_user: The authenticated user
        
    Returns:
        Current user data
    """
    return current_user


@router.put("/me", response_model=UserInDB)
def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user information.
    
    Args:
        user_update: User update data
        current_user: The authenticated user
        db: Database session
        
    Returns:
        Updated user data
        
    Raises:
        HTTPException: If update fails
    """
    # Don't allow users to change their own is_active or permissions
    user_update.is_active = None
    user_update.permissions = None
    
    updated_user = service.update_user(db, current_user.id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return updated_user


@router.get("/users", response_model=List[UserInDB])
def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_superuser),
    db: Session = Depends(get_db)
):
    """
    List all users (superuser only).
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: The authenticated superuser
        db: Database session
        
    Returns:
        List of users
    """
    return service.get_users(db, skip=skip, limit=limit)


@router.put("/users/{user_id}", response_model=UserInDB)
def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(require_superuser),
    db: Session = Depends(get_db)
):
    """
    Update a user (superuser only).
    
    Args:
        user_id: ID of user to update
        user_update: User update data
        current_user: The authenticated superuser
        db: Database session
        
    Returns:
        Updated user data
        
    Raises:
        HTTPException: If user not found
    """
    updated_user = service.update_user(db, user_id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return updated_user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: str,
    current_user: User = Depends(require_superuser),
    db: Session = Depends(get_db)
):
    """
    Delete a user (superuser only).
    
    Args:
        user_id: ID of user to delete
        current_user: The authenticated superuser
        db: Database session
        
    Raises:
        HTTPException: If user not found
    """
    if not service.delete_user(db, user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
