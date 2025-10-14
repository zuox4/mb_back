from pydantic import BaseModel
from typing import Optional, List

class TeacherResponse(BaseModel):
    uid: str
    display_name: str
    image: Optional[str] = None
    leader_groups: Optional[List[str]] = None
    email: Optional[str] = None

class StudentResponse(BaseModel):
    uid: str
    display_name: str
    email: Optional[str] = None
    group_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    patronymic: Optional[str] = None

class SyncStats(BaseModel):
    added: int = 0
    updated: int = 0
    archived: int = 0
    errors: List[str] = []
    total_external: int = 0