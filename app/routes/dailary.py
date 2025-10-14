from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import APIRouter, Depends, HTTPException
from typing import List

from ..auth.dependencies import get_current_active_user, get_current_active_teacher
from ..database import get_db
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database.models import User, Event, EventType, Stage, Achievement, PossibleResult, Group
from datetime import datetime
router = APIRouter()


class StageResultResponse(BaseModel):
    name: str
    status: str
    date: Optional[datetime]
    result_title: Optional[str]
    score: int
    min_required_score: int
    current_score: int
    stage_id: int
    possible_results: List[dict]


class StudentJournalResponse(BaseModel):
    id: int
    student_name: str
    student_id: int
    event_name: str
    type: str
    date: datetime
    stages: List[StageResultResponse]
    total_score: int
    min_stages_required: int
    completed_stages_count: int


@router.get("/{event_id}/{group_id}", response_model=List[StudentJournalResponse])
def get_class_journal(
        event_id: int,
        group_id: str,  # group_name из User
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_teacher)
):
    """
    Получить журнал класса по мероприятию
    """
    # Проверяем существование мероприятия
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")

    # Получаем всех учеников указанного класса
    group = db.query(Group).filter(Group.id == group_id).first()
    students = db.query(User).filter(
        User.group_name == group.name,
        User.archived == False,
    ).all()

    if not students:
        raise HTTPException(status_code=404, detail="В классе нет учеников")

    # Получаем тип мероприятия и его стадии
    event_type = db.query(EventType).filter(EventType.id == event.event_type_id).first()
    stages = db.query(Stage).filter(
        Stage.event_type_id == event.event_type_id
    ).order_by(Stage.stage_order).all()

    result = []

    for student in students:
        student_data = {
            "id": student.id,
            "student_id": student.id,
            "student_name": student.display_name or f"Ученик {student.id}",
            "event_name": event.title,
            "type": event_type.title,
            "date": event.date_start or datetime.utcnow(),
            "stages": [],
            "total_score": 0,
            "min_stages_required": event_type.min_stages_for_completion or len(stages),
            "completed_stages_count": 0
        }

        total_score = 0
        completed_stages = 0

        for stage in stages:
            # Получаем возможные результаты для стадии
            possible_results = db.query(PossibleResult).filter(
                PossibleResult.stage_id == stage.id
            ).all()

            # Ищем достижение ученика для этой стадии
            achievement = db.query(Achievement).filter(
                and_(
                    Achievement.student_id == student.id,
                    Achievement.event_id == event_id,
                    Achievement.stage_id == stage.id
                )
            ).first()

            current_score = 0
            result_title = None
            status = "незачет"

            if achievement:
                # Если есть достижение, берем баллы и название результата
                current_score = achievement.result.points_for_done
                result_title = achievement.result.title

                # НОВАЯ ЛОГИКА: проверяем удовлетворяет ли результат минимальным требованиям
                if current_score >= stage.min_score_for_finished:
                    status = "зачет"
                    completed_stages += 1
                else:
                    status = "незачет"
            else:
                # Если достижения нет
                status = "незачет"
                current_score = 0

            total_score += current_score

            stage_data = StageResultResponse(
                name=stage.title,
                status=status,
                date=achievement.achieved_at if achievement else None,
                result_title=result_title,
                score=stage.min_score_for_finished,  # Минимальный требуемый балл
                min_required_score=stage.min_score_for_finished,
                current_score=current_score,
                stage_id=stage.id,
                possible_results=[
                    {
                        "id": pr.id,
                        "title": pr.title,
                        "points": pr.points_for_done
                    } for pr in possible_results
                ]
            )

            student_data["stages"].append(stage_data)

        student_data["total_score"] = total_score
        student_data["completed_stages_count"] = completed_stages
        result.append(StudentJournalResponse(**student_data))

    return result

class UpdateResultRequest(BaseModel):
    result_id: int
@router.post("/{event_id}/{student_id}/{stage_id}")
def update_student_result(
        event_id: int,
        student_id: int,
        stage_id: int,
        request: UpdateResultRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_teacher),

):
    result_id = request.result_id
    teacher_id = current_user.id
    """
    Обновить результат ученика для стадии мероприятия
    """
    # Проверяем существование сущностей
    student = db.query(User).filter(User.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Ученик не найден")

    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")

    stage = db.query(Stage).filter(Stage.id == stage_id).first()
    if not stage:
        raise HTTPException(status_code=404, detail="Стадия не найдена")

    result = db.query(PossibleResult).filter(PossibleResult.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Результат не найден")

    teacher = db.query(User).filter(User.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Учитель не найден")

    # Ищем существующее достижение
    existing_achievement = db.query(Achievement).filter(
        and_(
            Achievement.student_id == student_id,
            Achievement.event_id == event_id,
            Achievement.stage_id == stage_id
        )
    ).first()

    if existing_achievement:
        # Обновляем существующее достижение
        existing_achievement.result_id = result_id
        existing_achievement.teacher_id = teacher_id
        existing_achievement.achieved_at = func.now()
    else:
        # Создаем новое достижение
        new_achievement = Achievement(
            student_id=student_id,
            teacher_id=teacher_id,
            event_id=event_id,
            stage_id=stage_id,
            result_id=result_id,
            student_data={
                "student_name": student.display_name,
                "group_name": student.group_name
            }
        )
        db.add(new_achievement)

    db.commit()

    return {"message": "Результат успешно обновлен"}


@router.get("/events/{event_type_id}/stages")
def get_event_stages(event_type_id: int, db: Session = Depends(get_db),current_user: User = Depends(get_current_active_teacher)):
    """
    Получить стадии типа мероприятия
    """
    stages = db.query(Stage).filter(
        Stage.event_type_id == event_type_id
    ).order_by(Stage.stage_order).all()

    result = []
    for stage in stages:
        possible_results = db.query(PossibleResult).filter(
            PossibleResult.stage_id == stage.id
        ).all()

        result.append({
            "id": stage.id,
            "title": stage.title,
            "stage_order": stage.stage_order,
            "min_score_for_finished": stage.min_score_for_finished,
            "possible_results": [
                {
                    "id": pr.id,
                    "title": pr.title,
                    "points_for_done": pr.points_for_done
                } for pr in possible_results
            ]
        })

    return result


@router.delete("/{event_id}/{student_id}/{stage_id}")
def delete_student_result(
        event_id: int,
        student_id: int,
        stage_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_teacher),
):
    """
    Удалить результат ученика для стадии мероприятия
    """
    # Находим достижение для удаления
    achievement = db.query(Achievement).filter(
        and_(
            Achievement.student_id == student_id,
            Achievement.event_id == event_id,
            Achievement.stage_id == stage_id
        )
    ).first()

    if not achievement:
        raise HTTPException(status_code=404, detail="Результат не найден")

    # Удаляем достижение
    db.delete(achievement)
    db.commit()

    return {"message": "Результат успешно удален"}