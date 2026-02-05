from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_,func,case
from fastapi import APIRouter, Depends, HTTPException,Query
from typing import List

from ..auth.dependencies import get_current_active_user
from ..database import get_db
from app.database.models import User, Event, ProjectOffice, EventType, Stage, Achievement, PossibleResult, Group, \
    p_office_group_association, p_office_event_association
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

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

class ProjectOfficeJournalResponse(BaseModel):
    id: int
    student_id: int
    student_name: str
    group_name: str  # Новое поле - название класса
    class_teacher: Optional[str] = None  # Классный руководитель
    event_name: str
    type: str
    date: datetime
    stages: List[StageResultResponse]
    total_score: int
    min_stages_required: int
    completed_stages_count: int

    class Config:
        from_attributes = True

router = APIRouter()


@router.get("/journal/{event_id}", response_model=List[ProjectOfficeJournalResponse])
def get_project_office_journal(
        event_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    Получить журнал по мероприятию для проектного офиса (классы проектного офиса)
    МАКСИМАЛЬНО ОПТИМИЗИРОВАННАЯ ВЕРСИЯ - 1 ЗАПРОС К БД
    """

    # ОДИН сложный запрос для получения всех данных
    query = db.query(
        User.id.label('student_id'),
        User.display_name.label('student_name'),
        User.group_name,
        Group.name.label('group_name'),
        Event.title.label('event_title'),
        Event.date_start,
        EventType.title.label('event_type_title'),
        EventType.min_stages_for_completion,
        Stage.id.label('stage_id'),
        Stage.title.label('stage_title'),
        Stage.min_score_for_finished,
        Stage.stage_order,
        PossibleResult.id.label('possible_result_id'),
        PossibleResult.title.label('possible_result_title'),
        PossibleResult.points_for_done.label('possible_result_points'),
        Achievement.achieved_at,
        Achievement.result_id,
        func.coalesce(PossibleResult.points_for_done, 0).label('current_score'),
        # Получаем информацию о классном руководителе
        func.string_agg(
            case(
                (User.groups_leader.contains([Group.name]), User.display_name),
                else_=None
            ),
            ', '
        ).label('class_teacher_names')
    ).select_from(Event) \
        .join(Event.event_type) \
        .join(p_office_event_association, Event.id == p_office_event_association.c.event_id) \
        .join(ProjectOffice, p_office_event_association.c.p_office_id == ProjectOffice.id) \
        .join(p_office_group_association, ProjectOffice.id == p_office_group_association.c.p_office_id) \
        .join(Group, p_office_group_association.c.group_id == Group.id) \
        .join(User, User.group_name == Group.name) \
        .join(Stage, Stage.event_type_id == EventType.id) \
        .outerjoin(Achievement, and_(
        Achievement.student_id == User.id,
        Achievement.event_id == Event.id,
        Achievement.stage_id == Stage.id
    )) \
        .outerjoin(PossibleResult, and_(
        PossibleResult.stage_id == Stage.id,
        PossibleResult.id == Achievement.result_id
    )) \
        .filter(
        Event.id == event_id,
        ProjectOffice.leader_uid == current_user.id,
        User.archived.is_(False)
    ) \
        .group_by(
        User.id, User.display_name, User.group_name, Group.name,
        Event.title, Event.date_start, EventType.title, EventType.min_stages_for_completion,
        Stage.id, Stage.title, Stage.min_score_for_finished, Stage.stage_order,
        PossibleResult.id, PossibleResult.title, PossibleResult.points_for_done,
        Achievement.achieved_at, Achievement.result_id
    ) \
        .order_by(Group.name, User.display_name, Stage.stage_order)

    rows = query.all()

    if not rows:
        # Проверяем существование мероприятия и доступ
        event_exists = db.query(Event).filter(Event.id == event_id).first()
        if not event_exists:
            raise HTTPException(status_code=404, detail="Мероприятие не найдено")

        project_office = db.query(ProjectOffice).filter(
            ProjectOffice.leader_uid == current_user.id
        ).first()
        if not project_office:
            raise HTTPException(status_code=404, detail="Проектный офис не найден")

        raise HTTPException(status_code=404, detail="Нет данных для отображения")

    # Группируем данные в памяти
    from collections import defaultdict

    # Мапа для студентов
    students_data = defaultdict(lambda: {
        'id': None,
        'student_id': None,
        'student_name': None,
        'group_name': None,
        'class_teacher': None,
        'event_name': None,
        'type': None,
        'date': None,
        'stages': defaultdict(lambda: {
            'name': None,
            'status': 'незачет',
            'date': None,
            'result_title': None,
            'score': 0,
            'min_required_score': 0,
            'current_score': 0,
            'stage_id': None,
            'possible_results': set()
        }),
        'total_score': 0,
        'min_stages_required': 0,
        'completed_stages_count': 0
    })

    # Собираем возможные результаты для стадий
    possible_results_map = defaultdict(list)

    for row in rows:
        student_key = row.student_id
        stage_key = row.stage_id

        # Инициализируем студента
        if students_data[student_key]['id'] is None:
            students_data[student_key].update({
                'id': row.student_id,
                'student_id': row.student_id,
                'student_name': row.student_name or f"Ученик {row.student_id}",
                'group_name': row.group_name,
                'class_teacher': row.class_teacher_names if row.class_teacher_names else None,
                'event_name': row.event_title,
                'type': row.event_type_title,
                'date': row.date_start or datetime.utcnow(),
                'min_stages_required': row.min_stages_for_completion or 0
            })

        # Добавляем возможные результаты
        if row.possible_result_id:
            result_info = (row.possible_result_id, row.possible_result_title, row.possible_result_points)
            if result_info not in possible_results_map[stage_key]:
                possible_results_map[stage_key].append(result_info)

        # Обновляем данные стадии
        stage_data = students_data[student_key]['stages'][stage_key]
        if stage_data['name'] is None:
            stage_data.update({
                'name': row.stage_title,
                'min_required_score': row.min_score_for_finished or 0,
                'stage_id': row.stage_id
            })

        # Обновляем баллы и статус
        if row.current_score > 0:
            stage_data['current_score'] = max(stage_data['current_score'], row.current_score)
            stage_data['result_title'] = row.possible_result_title
            stage_data['date'] = row.achieved_at

        # Добавляем возможные результаты
        if row.possible_result_id:
            stage_data['possible_results'].add((
                row.possible_result_id,
                row.possible_result_title,
                row.possible_result_points
            ))

    # Формируем финальный результат
    result = []

    for student_id, student_data in students_data.items():
        total_score = 0
        completed_stages_count = 0
        stages_list = []

        for stage_id, stage_data in student_data['stages'].items():
            # Определяем статус стадии
            is_completed = stage_data['current_score'] >= stage_data['min_required_score']
            status = "зачет" if is_completed else "незачет"

            if is_completed:
                completed_stages_count += 1

            total_score += stage_data['current_score']

            # Преобразуем possible_results в список словарей
            possible_results_list = [
                {
                    "id": res[0],
                    "title": res[1],
                    "points": res[2]
                } for res in stage_data['possible_results']
            ]

            stages_list.append(StageResultResponse(
                name=stage_data['name'],
                status=status,
                date=stage_data['date'],
                result_title=stage_data['result_title'],
                score=stage_data['min_required_score'],
                min_required_score=stage_data['min_required_score'],
                current_score=stage_data['current_score'],
                stage_id=stage_data['stage_id'],
                possible_results=possible_results_list
            ))

        result.append(ProjectOfficeJournalResponse(
            id=student_data['id'],
            student_id=student_data['student_id'],
            student_name=student_data['student_name'],
            group_name=student_data['group_name'],
            class_teacher=student_data['class_teacher'],
            event_name=student_data['event_name'],
            type=student_data['type'],
            date=student_data['date'],
            stages=stages_list,
            total_score=total_score,
            min_stages_required=student_data['min_stages_required'],
            completed_stages_count=completed_stages_count
        ))

    # Сортируем результат
    result.sort(key=lambda x: (x.group_name, x.student_name))

    return result


@router.get("/events")
def get_project_office_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Получить список мероприятий доступных для проектного офиса
    """
    # Получаем проектный офис пользователя
    project_office = db.query(ProjectOffice).filter(
        ProjectOffice.leader_uid == current_user.id
    ).first()

    if not project_office:
        raise HTTPException(status_code=404, detail="Проектный офис не найден")

    # Получаем мероприятия, привязанные к проектному офису
    events = db.query(Event).join(
        p_office_event_association,
        p_office_event_association.c.event_id == Event.id
    ).filter(
        and_(
            p_office_event_association.c.p_office_id == project_office.id,
            Event.is_active == True
        )
    ).order_by(Event.date_start.desc()).all()
    x = db.query(p_office_event_association).filter(p_office_event_association.c.p_office_id == project_office.id).all()
    impotant_ids = [i.event_id for i in x if i.is_important == True]
    print('11111',impotant_ids)
    return [
        {
            "id": event.id,
            "title": event.title,
            "date_start": event.date_start,
            "date_end": event.date_end,
            "event_type": event.event_type.title,
            "description": event.description,
            'is_important': event.id in impotant_ids,
        }
        for event in events
    ]


@router.get("/groups")
def get_project_office_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Получить список классов под управлением проектного офиса
    """
    # Получаем проектный офис пользователя
    project_office = db.query(ProjectOffice).filter(
        ProjectOffice.leader_uid == current_user.id
    ).first()

    if not project_office:
        raise HTTPException(status_code=404, detail="Проектный офис не найден")

    # Получаем классы, привязанные к проектному офису
    groups = db.query(Group).join(
        p_office_group_association,
        p_office_group_association.c.group_id == Group.id
    ).filter(
        p_office_group_association.c.p_office_id == project_office.id
    ).order_by(Group.name).all()

    return [
        {
            "id": group.id,
            "name": group.name,
            "student_count": db.query(User).filter(
                User.group_name == group.name,
                User.archived == False
            ).count(),
            "leader_name": group.leader_name if hasattr(group, 'leader_name') else None
        }
        for group in groups
    ]


@router.get("/pivot-data-optimized")
def get_project_office_pivot_data_optimized(
        groups: List[str] = Query(None),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    Супер-оптимизированная версия pivot-data
    """
    import time
    start_time = time.time()

    # 1. Получаем проектный офис и важные мероприятия ОДИН РАЗ
    project_office = db.query(ProjectOffice).filter(
        ProjectOffice.leader_uid == current_user.id
    ).first()

    if not project_office:
        raise HTTPException(status_code=404, detail="Проектный офис не найден")

    # 2. Получаем важные мероприятия ОДИН РАЗ
    important_events_query = db.query(p_office_event_association.c.event_id).filter(
        p_office_event_association.c.p_office_id == project_office.id,
        p_office_event_association.c.is_important == True
    )
    important_event_ids = {row.event_id for row in important_events_query.all()}

    print(f"1. Получение важных мероприятий: {time.time() - start_time:.2f} сек")

    # 3. Основной запрос - получаем только необходимые данные
    # Используем CTE или подзапросы для оптимизации

    # ВАРИАНТ А: Используем подзапрос для достижений (часто самый быстрый)
    from sqlalchemy import func

    # Сначала получаем всех студентов и их группы
    students_query = db.query(
        User.id.label('student_id'),
        User.display_name,
        User.group_name,
        Group.id.label('group_id')
    ).join(Group, User.group_name == Group.name) \
        .join(p_office_group_association, Group.id == p_office_group_association.c.group_id) \
        .filter(
        p_office_group_association.c.p_office_id == project_office.id,
        User.archived == False
    )

    if groups:
        students_query = students_query.filter(User.group_name.in_(groups))

    students = students_query.all()
    student_ids = [s.student_id for s in students]

    if not student_ids:
        return []

    print(f"2. Получение студентов: {time.time() - start_time:.2f} сек")

    # 4. Получаем все мероприятия проектного офиса
    events_query = db.query(
        Event.id.label('event_id'),
        Event.title.label('event_title'),
        EventType.id.label('event_type_id'),
        EventType.min_stages_for_completion,
        Stage.id.label('stage_id'),
        Stage.title.label('stage_title'),
        Stage.min_score_for_finished,
        Stage.stage_order
    ).join(p_office_event_association, Event.id == p_office_event_association.c.event_id) \
        .join(EventType, Event.event_type_id == EventType.id) \
        .join(Stage, Stage.event_type_id == EventType.id) \
        .filter(
        p_office_event_association.c.p_office_id == project_office.id,
        Event.is_active == True
    ) \
        .order_by(Event.id, Stage.stage_order)

    events_data = events_query.all()

    # Группируем мероприятия по event_id для быстрого доступа
    events_by_id = {}
    for event in events_data:
        event_id = event.event_id
        if event_id not in events_by_id:
            events_by_id[event_id] = {
                'event_title': event.event_title,
                'min_stages_required': event.min_stages_for_completion or 0,
                'stages': [],
                'is_important': event_id in important_event_ids
            }
        events_by_id[event_id]['stages'].append({
            'stage_id': event.stage_id,
            'title': event.stage_title,
            'min_score': event.min_score_for_finished,
            'order': event.stage_order
        })

    print(f"3. Получение мероприятий: {time.time() - start_time:.2f} сек")

    # 5. Получаем ВСЕ достижения студентов для этих мероприятий ОДНИМ запросом
    achievements_query = db.query(
        Achievement.student_id,
        Achievement.event_id,
        Achievement.stage_id,
        PossibleResult.points_for_done
    ).join(PossibleResult, Achievement.result_id == PossibleResult.id) \
        .filter(
        Achievement.student_id.in_(student_ids),
        Achievement.event_id.in_(list(events_by_id.keys()))
    ) \
        .order_by(Achievement.student_id, Achievement.event_id, Achievement.stage_id)

    # Группируем достижения по студенту и мероприятию
    from collections import defaultdict
    achievements_by_student_event = defaultdict(lambda: defaultdict(dict))

    for ach in achievements_query.all():
        achievements_by_student_event[ach.student_id][ach.event_id][ach.stage_id] = ach.points_for_done or 0

    print(f"4. Получение достижений: {time.time() - start_time:.2f} сек")

    # 6. Собираем финальный результат
    result = []

    for student in students:
        student_data = {
            "id": student.student_id,
            "student_name": student.display_name or f"Ученик {student.student_id}",
            "group_name": student.group_name,
            "class_teacher": None,
            "events": {}
        }

        student_achievements = achievements_by_student_event.get(student.student_id, {})

        for event_id, event_info in events_by_id.items():
            event_achievements = student_achievements.get(event_id, {})

            # Считаем статистику по мероприятию
            total_score = 0
            completed_stages_count = 0
            stages_list = []

            for stage_info in event_info['stages']:
                stage_score = event_achievements.get(stage_info['stage_id'], 0)
                status = "зачет" if stage_score >= (stage_info['min_score'] or 0) else "незачет"

                stages_list.append({
                    "name": stage_info['title'],
                    "status": status,
                    "current_score": stage_score
                })

                total_score += stage_score
                if status == "зачет":
                    completed_stages_count += 1

            # Определяем общий статус мероприятия
            if completed_stages_count >= event_info['min_stages_required']:
                status = "зачет"
            elif total_score > 0:
                status = "в процессе"
            else:
                status = "не начато"

            student_data["events"][str(event_id)] = {
                "event_name": event_info['event_title'],
                "total_score": total_score,
                "completed_stages_count": completed_stages_count,
                "min_stages_required": event_info['min_stages_required'],
                "is_important": event_info['is_important'],
                "stages": stages_list,
                "status": status
            }

        result.append(student_data)

    print(f"5. Формирование результата: {time.time() - start_time:.2f} сек")
    print(f"Итого: {time.time() - start_time:.2f} сек")

    return result

class EventsData(BaseModel):
    event_ids: List[int]


@router.post('/change-events-project')
def set_events_for_p_office(data: EventsData, db: Session = Depends(get_db),
                            current_user: User = Depends(get_current_active_user)):
    """
    Сохраняет мероприятия для проектного офиса с использованием ORM.
    """

    try:
        # 1. Находим проектный офис
        project_office = db.query(ProjectOffice).filter(
            ProjectOffice.leader_uid == current_user.id
        ).first()

        if not project_office:
            raise HTTPException(status_code=404, detail="Проектный офис не найден")

        # 2. Если новые мероприятия не переданы, очищаем все
        if not data.event_ids:
            project_office.accessible_events = []  # Если есть связь events в модели
            db.commit()

            return {
                "message": "Все мероприятия удалены из проектного офиса",
                "project_office_id": project_office.id,
                "event_ids": [],
                "event_count": 0
            }

        # 3. Проверяем существование новых мероприятий
        existing_events = db.query(Event).filter(
            Event.id.in_(data.event_ids)
        ).all()

        if len(existing_events) != len(data.event_ids):
            found_event_ids = {event.id for event in existing_events}
            not_found_ids = [event_id for event_id in data.event_ids if event_id not in found_event_ids]
            raise HTTPException(
                status_code=404,
                detail=f"Мероприятия с ID {not_found_ids} не найдены"
            )

        # 4. Получаем текущие мероприятия
        current_event_ids = {event.id for event in project_office.accessible_events}  # Если есть связь
        new_event_ids = set(data.event_ids)

        # 5. Определяем мероприятия для удаления и добавления
        events_to_remove_ids = current_event_ids - new_event_ids
        events_to_add_ids = new_event_ids - current_event_ids

        # 6. Удаляем ненужные мероприятия
        if events_to_remove_ids:
            events_to_remove = db.query(Event).filter(Event.id.in_(events_to_remove_ids)).all()
            for event in events_to_remove:
                project_office.accessible_events.remove(event)

        # 7. Добавляем новые мероприятия
        if events_to_add_ids:
            events_to_add = db.query(Event).filter(Event.id.in_(events_to_add_ids)).all()
            for event in events_to_add:
                project_office.accessible_events.append(event)

        # 8. Сохраняем изменения
        db.add(project_office)
        db.commit()

        # 9. Обновляем объект из базы
        db.refresh(project_office)

        return {
            "message": "Мероприятия успешно обновлены",
            "project_office_id": project_office.id,
            "event_ids": data.event_ids,
            "event_count": len(data.event_ids),
            "events": [
                {
                    "id": event.id,
                    "title": event.title
                }
                for event in project_office.accessible_events
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Ошибка при обновлении мероприятий: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при обновлении мероприятий: {str(e)}"
        )
class EventUptatePriority(BaseModel):
    value: bool


@router.post('/change-event-imp/{event_id}')
def set_priority_for_project_event(
        event_id: int,
        data: EventUptatePriority,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    Установить приоритет мероприятия для проектного офиса
    """
    # Проверяем, есть ли у пользователя проектный офис
    if not current_user.p_office:
        raise HTTPException(
            status_code=400,
            detail="Пользователь не привязан к проектному офису"
        )
    project_office = db.query(ProjectOffice).filter(
        ProjectOffice.leader_uid == current_user.id
    ).first()
    project_office_id = project_office.id

    # Ищем связь в ассоциативной таблице
    association = db.execute(
        p_office_event_association.select().where(
            and_(
                p_office_event_association.c.event_id == event_id,
                p_office_event_association.c.p_office_id == project_office_id
            )
        )
    ).first()

    if not association:
        # Если связи нет, создаем новую запись
        try:
            db.execute(
                p_office_event_association.insert().values(
                    event_id=event_id,
                    p_office_id=project_office_id,
                    is_important=data.value  # или data.is_important в зависимости от модели
                )
            )
            db.commit()
            print()
            return {"message": "Приоритет установлен", "is_important": data.value}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Ошибка при создании связи: {str(e)}")
    else:
        # Если связь есть, обновляем поле is_important
        print(association)
        try:
            db.execute(
                p_office_event_association.update().where(
                    and_(
                        p_office_event_association.c.event_id == event_id,
                        p_office_event_association.c.p_office_id == project_office_id
                    )
                ).values(is_important=data.value)
            )
            db.commit()
            print("Приоритет обновлен", "is_important", data.value)
            return {"message": "Приоритет обновлен", "is_important": data.value}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Ошибка при обновлении: {str(e)}")
