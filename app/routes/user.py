import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database.database import get_db
from app.services import SchoolService
from app.services.registration_service import RegistrationService
from app.database.models import User, Group

from app.auth.utils import create_access_token
from app.core.config import settings
from app.auth.dependencies import get_current_active_user, get_current_user
from app.auth.models import RegisterRequest, VerifyEmailRequest, LoginRequest, UserResponse


router = APIRouter()

@router.get("/{id}", response_model=dict)
def get_user_main_data(current_user: User = Depends(get_current_active_user),  db: Session = Depends(get_db)):

    roles = [i.name for i in current_user.roles]
    p_office = current_user.p_office if current_user.p_office else []
    event_types = current_user.event_types if current_user.event_types else []
    groups_leader = current_user.groups_leader if current_user.groups_leader else []
    print('sdcscd:',groups_leader)
    gr = db.query(Group).all()
    has_groups = False
    for i in gr:
        if i.name in groups_leader:
            has_groups = True


    # Проверяем каждое поле отдельно
    has_p_office = len(p_office) > 0
    has_event_types = len(event_types) > 0
    has_groups_leader = has_groups
    has_admin = True if 'admin' in [i.name for i in current_user.roles] else False
    return {
        "id": current_user.id,
        "display_name": current_user.display_name,
        "email": current_user.email,
        "image": current_user.image,
        "roles": roles,
        'has_p_office': has_p_office,
        'has_event_types': has_event_types,
        'has_groups_leader': has_groups_leader,
        'has_admin': has_admin,

        }


