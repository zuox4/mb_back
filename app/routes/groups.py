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
from fastapi import HTTPException
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


@router.get('/for_group_leader/{group_id}')
def get_class(group_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_teacher)):
    group_name = db.query(Group).get(group_id).name
    return db.query(User).filter((User.group_name == group_name) & (User.archived !=True)).all()


@router.get('/{group_id}')
def get_class(group_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_teacher)):
    try:
        # Получаем класс
        group = db.query(Group).get(group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Класс не найден")

        group_name = group.name

        # Получаем классного руководителя
        teacher = db.query(User).filter(
            User.groups_leader.contains([group_name])
        ).first()

        if not teacher:
            raise HTTPException(status_code=404, detail="Классный руководитель не найден")

        teacher_data = {
            'id': teacher.id,
            'display_name': teacher.display_name,
            'phone': teacher.phone if teacher.phone else '',
            'lastLogin': teacher.last_login_at,
            'email': teacher.email,
            'avatar': teacher.image if teacher.image else '',
        }

        # Получаем студентов класса
        students = db.query(User).filter(
            (User.group_name == group_name) &
            (User.archived != True)
        ).all()

        students_data = [{
            'id': student.id,  # Исправлено: используем student.id вместо 1
            'display_name': student.display_name,
            'avatar': student.image if student.image else '',
            'isActive': student.is_active,
            'lastLogin': student.last_login_at,
            'email': student.email,
        } for student in students]

        # Разбираем название класса на части
        try:
            grade_part = group_name.split('-')[0]
            letter_part = group_name.split('-')[1] if len(group_name.split('-')) > 1 else ''

            grade = int(grade_part) if grade_part.isdigit() else 0
            letter = letter_part
        except (ValueError, IndexError) as e:
            # Если формат названия класса не соответствует ожидаемому
            grade = 0
            letter = ''
            # Можно логировать ошибку, но не прерывать выполнение
            print(f"Ошибка парсинга названия класса {group_name}: {e}")

        group_res = {
            'id': group_id,
            'name': group_name,
            'grade': grade,
            'letter': letter,
            'studentCount': len(students_data),
        }

        return {
            'group': group_res,
            'teacher': teacher_data,
            'students': students_data
        }

    except HTTPException:
        # Пробрасываем HTTP исключения дальше
        raise
    except ValueError as e:
        # Обработка ошибок преобразования типов
        raise HTTPException(status_code=400, detail=f"Ошибка в данных: {str(e)}")
    except Exception as e:
        # Обработка всех остальных непредвиденных ошибок
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


