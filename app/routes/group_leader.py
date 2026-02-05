from typing import List

from fastapi import APIRouter
from fastapi.params import Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.database.models import User
from app.services.event_type_service.event_type_service import EventTypeService
from app.auth.dependencies import get_current_active_teacher
from app.services.event_type_service.schemas import EventTypeResponse
from app.database.models import Event
router = APIRouter()
class EventType(BaseModel):
    title: str
    description: str

@router.get("/event_types", response_model=List[EventTypeResponse])
def get_event_types(current_user: User=Depends(get_current_active_teacher), db: Session = Depends(get_db)):
    service = EventTypeService(db)
    event_types = service.get_event_types_by_leader(current_user.id)
    return event_types



@router.get("/events")
def get_events(current_user: User=Depends(get_current_active_teacher), db: Session = Depends(get_db)):
    service = EventTypeService(db)
    event_types = service.get_all_event_types_with_details()
    print(event_types)
    events = []
    for event_type in event_types:
        for i in event_type.events:
            events.append(i)
    return events

@router.get("/students")
def get_students(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_teacher)):

    x = db.query(User).filter(User.group_name=='11-Т').all()
    return x