from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app.database.models import *

class StageMark(BaseModel):
    name: str
    status: str  # "зачет" или "незачет"
    date: Optional[str] = None
    result_title: Optional[str] = None  # Название результата
    score: Optional[int] = None  # Баллы за этап
    min_required_score: int  # Минимальное количество баллов для зачета
    current_score: int  # Текущее количество баллов


class EventMark(BaseModel):
    id: int
    eventName: str
    type: str  # "зачет" или "незачет" - на основе всех этапов
    date: str
    stages: List[StageMark]
    total_score: Optional[int] = 0  # Общая сумма баллов за мероприятие
    min_stages_required: int  # Минимальное количество этапов для завершения
    completed_stages_count: int  # Количество завершенных этапов


class RecordBookResponse(BaseModel):
    marks: List[EventMark]


def get_student_record_book_marks_optimized(
        db: Session,
        student_id: int,
        student_class: str
) -> RecordBookResponse:
    """
    Максимально оптимизированная версия с одним запросом
    """

    # ОДИН сложный запрос вместо множественных
    query = db.query(
        Event.id.label('event_id'),
        Event.title.label('event_title'),
        Event.date_start,
        Event.date_end,
        EventType.min_stages_for_completion,
        Stage.id.label('stage_id'),
        Stage.title.label('stage_title'),
        Stage.min_score_for_finished,
        Stage.stage_order,
        func.coalesce(func.sum(PossibleResult.points_for_done), 0).label('stage_score'),
        func.max(Achievement.achieved_at).label('last_achievement_date'),
        func.string_agg(PossibleResult.title, ', ').label('result_titles')
    ).select_from(Event) \
        .join(Event.event_type) \
        .join(p_office_event_association, Event.id == p_office_event_association.c.event_id) \
        .join(ProjectOffice, p_office_event_association.c.p_office_id == ProjectOffice.id) \
        .join(p_office_group_association, ProjectOffice.id == p_office_group_association.c.p_office_id) \
        .join(Group, p_office_group_association.c.group_id == Group.id) \
        .join(Stage, Stage.event_type_id == EventType.id) \
        .outerjoin(Achievement, and_(
        Achievement.student_id == student_id,
        Achievement.event_id == Event.id,
        Achievement.stage_id == Stage.id
    )) \
        .outerjoin(PossibleResult, Achievement.result_id == PossibleResult.id) \
        .filter(
        Group.name == student_class,
        Event.is_active.is_(True),
        ProjectOffice.is_active.is_(True)
    ) \
        .group_by(
        Event.id, Event.title, Event.date_start, Event.date_end,
        EventType.min_stages_for_completion,
        Stage.id, Stage.title, Stage.min_score_for_finished, Stage.stage_order
    ) \
        .order_by(Event.id, Stage.stage_order)

    rows = query.all()

    if not rows:
        return RecordBookResponse(marks=[])

    # Группируем результаты по мероприятиям
    from collections import defaultdict
    events_data = defaultdict(lambda: {
        'id': None,
        'title': None,
        'date_start': None,
        'date_end': None,
        'min_stages_required': 0,
        'stages': [],
        'total_score': 0,
        'completed_stages_count': 0
    })

    for row in rows:
        event_key = row.event_id
        if events_data[event_key]['id'] is None:
            events_data[event_key].update({
                'id': row.event_id,
                'title': row.event_title,
                'date_start': row.date_start,
                'date_end': row.date_end,
                'min_stages_required': row.min_stages_for_completion or 0
            })

        is_stage_completed = row.stage_score >= (row.min_score_for_finished or 0)

        stage_data = StageMark(
            name=row.stage_title,
            status="зачет" if is_stage_completed else "незачет",
            date=row.last_achievement_date.isoformat() if row.last_achievement_date else None,
            result_title=row.result_titles.split(', ')[-1] if row.result_titles else None,
            score=row.stage_score,
            min_required_score=row.min_score_for_finished or 0,
            current_score=row.stage_score
        )

        events_data[event_key]['stages'].append(stage_data)
        events_data[event_key]['total_score'] += row.stage_score
        if is_stage_completed:
            events_data[event_key]['completed_stages_count'] += 1

    # Формируем финальный ответ
    marks = []
    for event_data in events_data.values():
        is_event_completed = event_data['completed_stages_count'] >= event_data['min_stages_required']
        event_status = "зачет" if is_event_completed and event_data['stages'] else "незачет"

        event_date = (
            event_data['date_start'].isoformat() if event_data['date_start'] else
            event_data['date_end'].isoformat() if event_data['date_end'] else
            datetime.now().isoformat()
        )

        marks.append(EventMark(
            id=event_data['id'],
            eventName=event_data['title'],
            type=event_status,
            date=event_date,
            stages=event_data['stages'],
            total_score=event_data['total_score'],
            min_stages_required=event_data['min_stages_required'],
            completed_stages_count=event_data['completed_stages_count']
        ))

    return RecordBookResponse(marks=marks)