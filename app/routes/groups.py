from fastapi import APIRouter
from typing import List

from fastapi import APIRouter
from fastapi.params import Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.database.models import User, Group
from app.services.event_type_service.event_type_service import EventTypeService
from app.auth.dependencies import get_current_active_user, get_current_active_teacher
from app.services.event_type_service.schemas import EventTypeResponse
from app.database.models import Event
router = APIRouter()
@router.get('/all')
def get_all_groups(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_teacher)):
    groups_list = db.query(Group).all()
    return groups_list


@router.get('/for_group_leader')
def get_all_groups(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_teacher)):

    groups = current_user.groups_leader
    all_groups_list = db.query(Group).all()
    teacher_classes = []
    for group in all_groups_list:
        if group.name in groups:
            teacher_classes.append(group)
    print(teacher_classes)
    return teacher_classes