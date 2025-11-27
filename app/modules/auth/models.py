from sqlalchemy import Column, String, Boolean, JSON
from app.utils.models import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    permissions = Column(JSON, default=list, nullable=False)  # List of permission strings
