from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

# Person Schemas
class PersonBase(BaseModel):
    first_name: str
    last_name: str
    external_number: str

class PersonCreate(PersonBase):
    pass

class Person(PersonBase):
    id: int
    
    class Config:
        from_attributes = True

# Plan Schemas
class PlanBase(BaseModel):
    start_date: datetime
    end_date: datetime
    person_id: int
    confirmed: bool = False

class PlanCreate(PlanBase):
    pass

class PlanUpdate(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    person_id: Optional[int] = None
    confirmed: Optional[bool] = None

class Plan(PlanBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    person: Optional[Person] = None

    class Config:
        from_attributes = True

# User Schemas
class UserBase(BaseModel):
    username: str
    role: str = "viewer"

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class PasswordChange(BaseModel):
    old_password: str
    new_password: str
