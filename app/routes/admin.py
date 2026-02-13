from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload, selectinload
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

from app.database import get_db
from app.database.models import Event, EventType, Stage, Group, ProjectOffice, p_office_group_association, User
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
def create_event(
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
def update_event(
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
def delete_event(
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




class GroupResponse(BaseModel):
    id: int
    name: str



@router.get('/all_groups')
def all_groups(db: Session = Depends(get_db)):
    groups = db.query(Group).all()
    return groups

class GroupCreateRequest(BaseModel):
    name: str


@router.post('/create-group')
def create_group(group_data: GroupCreateRequest, db: Session = Depends(get_db)):
    # Проверяем, существует ли группа с таким именем
    existing_group = db.query(Group).filter(Group.name == group_data.name).first()
    if existing_group:
        raise HTTPException(
            status_code=400,
            detail="Group with this name already exists"
        )

    # Создаем новую группу
    new_group = Group(name=group_data.name)
    db.add(new_group)
    db.commit()
    db.refresh(new_group)
    return GroupResponse(id=new_group.id, name=new_group.name)


@router.get("/get_offices")
def get_offices(db: Session = Depends(get_db)):
    offices = db.query(ProjectOffice).all()
    print(offices)
    return offices

@router.get("/get_office/{office_id}")
def get_offices(office_id:int, db: Session = Depends(get_db)):
    office = db.query(ProjectOffice).filter(ProjectOffice.id == office_id).first()
    return office

@router.get('/get_teacher_info/{id}')
def get_leader_info(id: int, db: Session = Depends(get_db)):
    user = db.query(User).get(id)
    return user


@router.get('/get_teachers_info')
def get_teachers_info(db: Session = Depends(get_db)):
    teachers = db.query(User).filter(User.roles.any(name='teacher')).all()

    return [{
        'id': teacher.id,
        'display_name': teacher.display_name,
        'email': teacher.email,
        'roles': [role.name for role in teacher.roles],
        'image': teacher.image,
    } for teacher in teachers]


class AssignResponsibleRequest(BaseModel):
    teacherId: Optional[int] = None
    eventTypeId: int


@router.post('/assign_responsible')
def assign_responsible(
        request: AssignResponsibleRequest,
        db: Session = Depends(get_db)
):
    """Назначение ответственного за тип мероприятия"""
    print(request.teacherId)

    # Находим тип мероприятия
    event_type = db.query(EventType).filter(EventType.id == request.eventTypeId).first()
    if not event_type:
        raise HTTPException(status_code=404, detail="Event type not found")
    teacher = db.query(User).filter(User.id == request.teacherId).first()
    # Назначаем ответственного
    event_type.leader = teacher

    db.commit()
    db.refresh(event_type)

    return {
        "success": True,
        "teacher_id": request.teacherId,
        "event_type_id": request.eventTypeId,
    }

@router.get('/event-types/{id}')
def event_types(id: int, db: Session = Depends(get_db)):
    event_type = db.query(EventType).filter(EventType.id == id).first()
    return {'leader': event_type.leader if event_type else None,}