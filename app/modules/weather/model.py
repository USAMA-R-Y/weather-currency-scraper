from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from app.utils.models import BaseModel

class Country(BaseModel):
    __tablename__ = "countries"

    name = Column(String, nullable=False)
    url = Column(String, nullable=True)

    cities = relationship("City", back_populates="country", cascade="all, delete-orphan")

class City(BaseModel):
    __tablename__ = "cities"

    name = Column(String, nullable=False)
    url = Column(String, nullable=True)
    country_id = Column(String, ForeignKey("countries.id"), nullable=False)

    country = relationship("Country", back_populates="cities")
