# app/api/endpoints/event_types.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database.models import User, Event, EventType
from app.auth.dependencies import get_current_active_user, get_current_active_teacher
from app.database.database import get_db
from app.services.event_type_service.event_type_service import EventTypeService
from app.services.event_type_service.schemas import (
    EventTypeResponse,
    EventTypeCreate,
    EventTypeUpdate
)
from sqlalchemy import update


router = APIRouter()


@router.get(
    "/all_event_types",
    response_model=List[EventTypeResponse],
    summary="Получить все типы мероприятий",
    description="Получение всех типов мероприятий с полной информацией о стадиях и результатах"
)
def get_all_event_types(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """
    Получение всех типов мероприятий с детальной информацией:
    - Основная информация о типе мероприятия
    - Все стадии с порядком
    - Возможные результаты для каждой стадии
    - Информация о руководителе
    """
    try:
        service = EventTypeService(db)
        event_types = service.get_all_event_types_with_details()
        return event_types
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/{event_type_id}",
    response_model=EventTypeResponse,
    summary="Получить тип мероприятия по ID",
    description="Получение детальной информации о конкретном типе мероприятия"
)
def get_event_type(event_type_id: int, db: Session = Depends(get_db),current_user: User = Depends(get_current_active_teacher),):
    try:
        service = EventTypeService(db)
        event_type = service.get_event_type_by_id(event_type_id)

        if not event_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Тип мероприятия не найден"
            )

        return event_type
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "",
    response_model=EventTypeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать тип мероприятия",
    description="Создание нового типа мероприятия со стадиями и возможными результатами"
)
def create_event_type(event_type_data: EventTypeCreate, db: Session = Depends(get_db),current_user: User = Depends(get_current_active_teacher),):
    try:
        service = EventTypeService(db)
        event_type = service.create_event_type(event_type_data.dict())
        return event_type
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/leader/{leader_id}",
    response_model=List[EventTypeResponse],
    summary="Получить типы мероприятий руководителя",
    description="Получение типов мероприятий по ID руководителя"
)
def get_event_types_by_leader(leader_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_teacher)):
    try:
        service = EventTypeService(db)
        event_types = service.get_event_types_by_leader(leader_id)
        return event_types
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post(
    "/{event_type_id}",
)
def delete_event_type(
    event_type_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_teacher)):
    try:
        event_type = db.get(EventType, event_type_id)
        event_type.is_archived = True
        db.commit()
        return {'message': 'Успешно обновлено'}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
