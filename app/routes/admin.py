from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.database.models import Event, EventType, Stage
from app.services.sync_service import TeacherSyncService, StudentSyncService

router = APIRouter()


# =============================================================================
# PYDANTIC SCHEMAS
# =============================================================================

class EventBase(BaseModel):
    title: str
    event_type_id: int
    description: Optional[str] = None
    academic_year: Optional[str] = None
    date_start: Optional[datetime] = None
    date_end: Optional[datetime] = None
    is_active: bool = True


class EventCreate(EventBase):
    pass


class EventResponse(EventBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SERVICE FUNCTIONS
# =============================================================================

def check_event_title_exists(db: Session, title: str, exclude_event_id: Optional[int] = None) -> bool:
    """
    Проверяет, существует ли мероприятие с таким названием
    """
    query = db.query(Event).filter(Event.title == title)
    if exclude_event_id:
        query = query.filter(Event.id != exclude_event_id)
    return query.first() is not None


def check_event_type_exists(db: Session, event_type_id: int) -> bool:
    """
    Проверяет, существует ли тип мероприятия
    """
    return db.query(EventType).filter(EventType.id == event_type_id).first() is not None


# =============================================================================
# ROUTES
# =============================================================================

@router.get("/sync_teachers")
def sync_teachers(db: Session = Depends(get_db)):
    """
    **Синхронизация преподавателей**

    - Запускает процесс синхронизации данных преподавателей
    - Возвращает результат синхронизации
    """
    teacher_service = TeacherSyncService()
    teacher_result = teacher_service.sync_teachers(db)
    return {"message": f"{teacher_result}"}


@router.get("/sync_students")
def sync_students(db: Session = Depends(get_db)):
    """
    **Синхронизация студентов**

    - Запускает процесс синхронизации данных студентов
    - Возвращает результат синхронизации
    """
    sync_service = StudentSyncService()
    student_result = sync_service.sync_students(db)
    return {"message": f"{student_result}"}


@router.get("/all_event_types")
def get_all_event_types(db: Session = Depends(get_db)):
    """
    **Получение всех типов мероприятий**

    - Возвращает список всех типов мероприятий
    - Включает связанные этапы и возможные результаты
    - Включает информацию о руководителе типа мероприятия
    """
    events = (
        db.query(EventType)
        .options(
            joinedload(EventType.stages).joinedload(Stage.possible_results),
            joinedload(EventType.leader)
        )
        .all()
    )
    return events


@router.get("/all_events")
def get_all_events(db: Session = Depends(get_db)):
    """
    **Получение всех мероприятий**

    - Возвращает список всех мероприятий
    - Без дополнительных связанных данных
    """
    events = db.query(Event).all()
    return events


@router.post(
    "/create_event",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать мероприятие",
    description="Создание нового мероприятия с указанием всех необходимых данных"
)
async def create_event(
        event_data: EventCreate,
        db: Session = Depends(get_db)
):
    """
    **Создание нового мероприятия**

    ### Параметры:
    - **title**: Название мероприятия (обязательно)
    - **event_type_id**: ID типа мероприятия (обязательно)
    - **description**: Описание мероприятия (опционально)
    - **academic_year**: Учебный год в формате "2024-2025" (опционально)
    - **date_start**: Дата начала мероприятия (опционально)
    - **date_end**: Дата окончания мероприятия (опционально)
    - **is_active**: Статус активности мероприятия (по умолчанию True)

    ### Проверки:
    - Уникальность названия мероприятия
    - Существование типа мероприятия
    - Корректность дат (если указаны обе)
    """
    try:
        # Проверка существования типа мероприятия
        if not check_event_type_exists(db, event_data.event_type_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Указанный тип мероприятия не существует"
            )

        # Проверка уникальности названия мероприятия
        if check_event_title_exists(db, event_data.title):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Мероприятие с таким названием уже существует"
            )

        # Проверка корректности дат
        if event_data.date_start and event_data.date_end:
            if event_data.date_start > event_data.date_end:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Дата начала не может быть позже даты окончания"
                )

        # Создание мероприятия
        event = Event(
            title=event_data.title,
            event_type_id=event_data.event_type_id,
            description=event_data.description,
            academic_year=event_data.academic_year,
            date_start=event_data.date_start,
            date_end=event_data.date_end,
            is_active=event_data.is_active
        )

        db.add(event)
        db.commit()
        db.refresh(event)

        return event

    except HTTPException:
        # Перевыбрасываем HTTP исключения
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        print(f"Ошибка при создании мероприятия: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Произошла внутренняя ошибка при создании мероприятия"
        )


@router.put(
    "/update_event/{event_id}",
    response_model=EventResponse,
    summary="Обновить мероприятие",
    description="Обновление данных существующего мероприятия"
)
async def update_event(
        event_id: int,
        event_data: EventCreate,
        db: Session = Depends(get_db)
):
    """
    **Обновление мероприятия**

    ### Параметры:
    - **event_id**: ID обновляемого мероприятия
    - **title**: Новое название мероприятия
    - **event_type_id**: ID типа мероприятия
    - **description**: Описание мероприятия
    - **academic_year**: Учебный год
    - **date_start**: Дата начала
    - **date_end**: Дата окончания
    - **is_active**: Статус активности

    ### Проверки:
    - Существование мероприятия
    - Уникальность названия (исключая текущее мероприятие)
    - Существование типа мероприятия
    - Корректность дат
    """
    try:
        # Поиск существующего мероприятия
        existing_event = db.query(Event).filter(Event.id == event_id).first()
        if not existing_event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Мероприятие не найдено"
            )

        # Проверка существования типа мероприятия
        if not check_event_type_exists(db, event_data.event_type_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Указанный тип мероприятия не существует"
            )

        # Проверка уникальности названия (исключая текущее мероприятие)
        if check_event_title_exists(db, event_data.title, exclude_event_id=event_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Мероприятие с таким названием уже существует"
            )

        # Проверка корректности дат
        if event_data.date_start and event_data.date_end:
            if event_data.date_start > event_data.date_end:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Дата начала не может быть позже даты окончания"
                )

        # Обновление полей
        for field, value in event_data.model_dump().items():
            setattr(existing_event, field, value)

        db.commit()
        db.refresh(existing_event)

        return existing_event

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Ошибка при обновлении мероприятия: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Произошла внутренняя ошибка при обновлении мероприятия"
        )


@router.delete(
    "/delete_event/{event_id}",
    status_code=status.HTTP_200_OK,
    summary="Удалить мероприятие",
    description="Удаление мероприятия по ID"
)
async def delete_event(
        event_id: int,
        db: Session = Depends(get_db)
):
    """
    **Удаление мероприятия**

    ### Параметры:
    - **event_id**: ID удаляемого мероприятия

    ### Возвращает:
    - Сообщение об успешном удалении
    """
    try:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Мероприятие не найдено"
            )

        db.delete(event)
        db.commit()

        return {"message": "Мероприятие успешно удалено"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Ошибка при удалении мероприятия: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Произошла внутренняя ошибка при удалении мероприятия"
        )