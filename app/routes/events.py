from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.database.models import User, Achievement, Event, EventType
from typing import List, Dict, Any

router = APIRouter()


class StageStatistic(BaseModel):
    stage_id: int
    title: str
    order: int
    achievement_count: int
    achievements: List[Dict[str, Any]]


class EventDetailResponse(BaseModel):
    id: int
    title: str
    description: str
    academic_year: str
    date_start: str
    date_end: str
    is_active: bool
    event_type_id: int
    event_type_name: str
    total_achievements: int
    stage_statistics: List[StageStatistic]
    unique_students_count: int
    total_highschool_students: int  # Добавим для информации
    participation_rate: float  # Процент участия 10-11 классов

@router.get('/all_events')
def get_all_events(db: Session = Depends(get_db)):
    return db.query(Event).filter(Event.is_active == True).all()

@router.get("/{event_id}", response_model=EventDetailResponse)
def get_event(event_id: int, db: Session = Depends(get_db)):
    # Получаем 10,11 классников
    students = db.query(User).all()
    students_highschool = []
    for i in students:
        try:
            if i.group_name and (i.group_name.startswith("10") or i.group_name.startswith("11")):
                students_highschool.append(i)
        except:
            continue
    print(f'Всего 10-11 классников {len(students_highschool)}')

    # Получаем мероприятие с загрузкой всех необходимых данных
    event = db.query(Event).options(
        joinedload(Event.event_type).joinedload(EventType.stages),
        joinedload(Event.achievements).joinedload(Achievement.stage),  # Загружаем stage
        joinedload(Event.achievements).joinedload(Achievement.result),  # Загружаем result
        joinedload(Event.achievements).joinedload(Achievement.student)  # Загружаем student
    ).filter(Event.id == event_id).first()

    if not event:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")

    # Получаем все достижения для этого мероприятия с загрузкой связанных данных
    achievements = db.query(Achievement).options(
        joinedload(Achievement.stage),
        joinedload(Achievement.result),
        joinedload(Achievement.student)
    ).filter(
        Achievement.event_id == event_id
    ).all()

    # Получаем все стадии для типа мероприятия
    stages = event.event_type.stages if event.event_type else []

    # Создаем словарь для быстрого поиска стадий по ID
    stage_dict = {stage.id: stage for stage in stages}

    # Группируем достижения по стадиям
    stage_statistics = []
    total_achievements = 0
    student_ids = set()

    # Для отладки: выводим информацию о достижениях
    print(f"\nВсего достижений для мероприятия {event_id}: {len(achievements)}")
    for i, ach in enumerate(achievements[:5]):  # Первые 5 для проверки
        print(f"Достижение {i + 1}: stage_id={ach.stage_id}, result_id={ach.result_id}")

    for stage in stages:
        # Фильтруем достижения для текущей стадии по stage_id
        stage_achievements = [
            ach for ach in achievements
            if ach.stage_id == stage.id  # Используем stage_id вместо result.id
        ]

        achievement_count = len(stage_achievements)
        total_achievements += achievement_count

        print(f"Стадия '{stage.title}' (id={stage.id}): {achievement_count} достижений")

        # Собираем ID студентов для подсчета уникальных участников
        for ach in stage_achievements:
            student_ids.add(ach.student_id)

        # Форматируем информацию о достижениях
        achievements_data = []
        for ach in stage_achievements:
            student_name = ""
            if ach.student:
                student_name = f"{ach.student.display_name or ''}".strip()

            achievements_data.append({
                "id": ach.id,
                "student_id": ach.student_id,
                "student_name": student_name,
                "teacher_id": ach.teacher_id,
                "stage_id": ach.stage_id,
                "result_id": ach.result_id,
                "result_title": ach.result.title if ach.result else None,
                "achieved_at": ach.achieved_at.isoformat() if ach.achieved_at else None,
                "proof_document_path": ach.proof_document_path,
                "student_data": ach.student_data
            })

        stage_statistics.append(StageStatistic(
            stage_id=stage.id,
            title=stage.title,
            order=getattr(stage, 'order', 0),
            achievement_count=achievement_count,
            achievements=achievements_data
        ))

    # Сортируем стадии по порядку (если есть поле order)
    stage_statistics.sort(key=lambda x: x.order)

    # Рассчитываем процент участия
    participation_rate = 0
    if students_highschool:
        participating_highschool = [s for s in students_highschool if s.id in student_ids]
        participation_rate = round(len(participating_highschool) / len(students_highschool) * 100, 2)

    # Формируем ответ
    return EventDetailResponse(
        id=event.id,
        title=event.title,
        description=event.description or "",
        academic_year=event.academic_year or "",
        date_start=event.date_start.isoformat() if event.date_start else "",
        date_end=event.date_end.isoformat() if event.date_end else "",
        is_active=event.is_active,
        event_type_id=event.event_type_id,
        event_type_name=event.event_type.title if event.event_type else "",
        total_achievements=total_achievements,
        stage_statistics=stage_statistics,
        unique_students_count=len(student_ids),
        total_highschool_students=len(students_highschool),
        participation_rate=participation_rate
    )


