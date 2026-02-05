# schemas/student.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class StudentBase(BaseModel):
    display_name: str
    email: EmailStr
    phone: Optional[str] = None


class StudentCreate(StudentBase):
    group_id: int
    password: str


class StudentUpdate(BaseModel):
    display_name: Optional[str] = None
    email: Optional[EmailStr] = None



class StudentResponse(StudentBase):
    id: int
    is_active: bool
    email_verified_at: Optional[datetime]
    verification_sent_at: Optional[datetime]
    archived: bool
    group_name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ClassStats(BaseModel):
    total_students: int
    active_students: int
    verified_students: int
    pending_verification: int
    archived_students: int
    class_name: str