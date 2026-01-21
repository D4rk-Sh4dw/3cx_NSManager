from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# User Schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    phone_number: Optional[str] = None
    role: str = "planner"  # admin, planner, buchhaltung
    is_active: bool = True
    can_take_duty: bool = True

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    can_take_duty: Optional[bool] = None
    password: Optional[str] = None  # Only if changing password

class User(UserBase):
    id: int
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserSimple(BaseModel):
    """Simplified user for display in plans"""
    id: int
    first_name: str
    last_name: str
    phone_number: Optional[str] = None
    email: str

    class Config:
        from_attributes = True

# Plan Schemas
class PlanBase(BaseModel):
    start_date: datetime
    end_date: datetime
    user_id: int  # Changed from person_id
    confirmed: bool = False

class PlanCreate(PlanBase):
    pass

class PlanUpdate(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    user_id: Optional[int] = None  # Changed from person_id
    confirmed: Optional[bool] = None

class Plan(PlanBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    user: Optional[UserSimple] = None  # Changed from person

    class Config:
        from_attributes = True

# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

class PasswordChange(BaseModel):
    old_password: str
    new_password: str

# Audit Schemas
class AuditLogEntry(BaseModel):
    id: int
    user_id: Optional[int]
    username: Optional[str]
    action: str
    target_table: str
    target_id: Optional[int]
    timestamp: datetime

    class Config:
        from_attributes = True
