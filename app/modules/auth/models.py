from sqlalchemy import Column, String, Boolean, JSON, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.utils.models import BaseModel


# Association table for many-to-many relationship between users and countries
user_preferred_countries = Table(
    'user_preferred_countries',
    BaseModel.metadata,
    Column('user_id', String, ForeignKey('users.id'), primary_key=True),
    Column('country_id', String, ForeignKey('countries.id'), primary_key=True)
)


class User(BaseModel):
    __tablename__ = "users"

    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    permissions = Column(JSON, default=list, nullable=False)  # List of permission strings
    
    # Many-to-many relationship with countries
    preferred_countries = relationship(
        "Country",
        secondary=user_preferred_countries,
        back_populates="preferred_by_users"
    )
