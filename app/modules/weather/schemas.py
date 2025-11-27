from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

class CountryBase(BaseModel):
    name: str
    url: Optional[str] = None

class CountryCreate(CountryBase):
    pass

class CountryUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None

class Country(CountryBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CityBase(BaseModel):
    name: str
    url: Optional[str] = None
    country_id: str

class CityCreate(CityBase):
    pass

class CityUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    country_id: Optional[str] = None

class City(CityBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
