import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.database import get_db
from fastapi import APIRouter, Depends, HTTPException

from app.database.models import User, ProjectOffice, Group, p_office_event_association, Achievement

from app.auth.dependencies import get_current_active_user, get_current_user
from app.routes.mark_book import RecordBookResponse, get_student_record_book_marks_optimized
from app.services.SchoolServices import SchoolService


router = APIRouter()

class Event(BaseModel):
    id: int
    title: str
    is_active: bool
    is_important: bool

class ProjectOfficeResponse(BaseModel):
    title: str
    description: str
    logo_url: Optional[str] = None
    accessible_events: List[Event]

class GroupLeaderResponse(BaseModel):
    display_name: str
    about: Optional[str] = None
    image: Optional[str] = None
    email: Optional[str] = None
    max_url: Optional[str] = None


class StudentInfoResponse(BaseModel):
    display_name: str
    class_name: str
    project_office_id: Optional[int] = None
    group_leader: Optional[GroupLeaderResponse] = None
    project_leader: Optional[GroupLeaderResponse] = None



@router.get("", response_model=StudentInfoResponse)
def get_student_info(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> StudentInfoResponse:

    if not ('student' in [role.name for role in current_user.roles]):
        raise HTTPException(status_code=401, detail="Нет доступа в соответствии с ролью")
    projects_office = db.query(ProjectOffice) \
        .join(ProjectOffice.accessible_classes) \
        .filter(Group.name == current_user.group_name) \
        .first()

    if projects_office:

        project_leader = projects_office.leader
    else:
        project_leader =None
    project_leader_response=None
    if project_leader:
        project_leader_response = GroupLeaderResponse(
            display_name=project_leader.display_name,
            about=project_leader.about,
            image=project_leader.image,
            max_url=project_leader.max_link_url,
            email=project_leader.email,
        )

    group_leader = db.query(User).filter(
        User.groups_leader.contains([current_user.group_name])
    ).first()

    # Обработка классного руководителя
    group_leader_response = None
    if group_leader:
        group_leader_response = GroupLeaderResponse(
            display_name=group_leader.display_name,
            about=group_leader.about,
            image=group_leader.image,
            max_url=group_leader.max_link_url,
            email=group_leader.email,
        )

    return StudentInfoResponse(
        display_name=current_user.display_name,
        class_name=current_user.group_name,
        project_office_id=projects_office.id if projects_office else None,
        group_leader=group_leader_response,
        project_leader=project_leader_response,
    )


@router.get("/project_office", response_model=ProjectOfficeResponse)
def get_project_office_info(current_user: User = Depends(get_current_active_user),  db: Session = Depends(get_db)):
    if not ('student'in [role.name for role in current_user.roles]):
        raise HTTPException(status_code=401, detail="Нет доступа в соответствии с ролью")
    projects_office = db.query(ProjectOffice).join(ProjectOffice.accessible_classes).filter(Group.name==current_user.group_name).first()
    x = db.query(p_office_event_association).filter(p_office_event_association.c.p_office_id == projects_office.id).all()
    impotant_ids = [i.event_id for i in x if i.is_important == True]
    if projects_office is None:
        raise HTTPException(status_code=404, detail=str('Проект для пользователя не найден'))
    data = {
        'title': projects_office.title,
        'description': projects_office.description,
        'logo_url': projects_office.logo_url,
        'accessible_events': [{'id': i.id, 'title': i.title, 'is_active': True,
    'is_important': i.id in impotant_ids} for i in projects_office.accessible_events]
    }
    return data


@router.get("/record-book/marks", response_model=RecordBookResponse)
def get_record_book_marks(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    try:
        mark_book = get_student_record_book_marks_optimized(db, current_user.id, current_user.group_name)
    except HTTPException as err:
        raise HTTPException(status_code=404, detail=str(err))
    return mark_book


@router.get("/achivments")
def get_achivments(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return db.query(Achievement).filter(Achievement.student_id==current_user.id).first()