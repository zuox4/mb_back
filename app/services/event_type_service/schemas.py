# app/schemas/event_type_schemas.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class PossibleResultBase(BaseModel):
    title: str
    points_for_done: int

class PossibleResultCreate(PossibleResultBase):
    pass

class PossibleResultResponse(PossibleResultBase):
    id: int

    class Config:
        from_attributes = True

class StageBase(BaseModel):
    title: str
    min_score_for_finished: int
    stage_order: int

class StageCreate(StageBase):
    possible_results: List[PossibleResultCreate]

class StageResponse(StageBase):
    id: int
    possible_results: List[PossibleResultResponse]

    class Config:
        from_attributes = True

class EventTypeBase(BaseModel):
    title: str
    description: Optional[str] = None
    leader_id: Optional[int] = None
    min_stages_for_completion: Optional[int] = 0

class EventTypeCreate(EventTypeBase):
    stages: List[StageCreate]

class EventTypeUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    leader_id: Optional[int] = None
    min_stages_for_completion: Optional[int] = None

class UserSimpleResponse(BaseModel):
    id: int
    display_name: Optional[str]
    email: str

    class Config:
        from_attributes = True
class Event(BaseModel):
    id: int
    title: str
    description: Optional[str] = None

class EventTypeResponse(EventTypeBase):
    id: int
    stages: List[StageResponse]
    leader: Optional[UserSimpleResponse]
    is_archived: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    events: List[Event]
    class Config:
        from_attributes = True