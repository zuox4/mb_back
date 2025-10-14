import requests
import mysql.connector
from typing import List, Dict
from mysql.connector import Error
from app.services.sync_service.schemas.sync_schemas import TeacherResponse, StudentResponse

# Конфигурация
MYSQL_CONFIG = {
    'host': '192.168.20.61',
    'database': 'students',
    'user': 'pass_system',
    'password': 'ktSXPOr2ekCGS4cr'
}


def get_teachers_external() -> List[TeacherResponse]:
    """Получение данных учителей из внешнего API"""
    teachers = []
    try:
        response = requests.get(
            'https://school1298.ru/portal/workers/workersPS-no.json',
            timeout=10
        )
        response.raise_for_status()
        teachers_data = response.json()

        for teacher in teachers_data.get('value', []):
            try:
                # Пропускаем некорректные записи
                if not teacher.get('Id') or teacher.get('email') in ['нет', 'e.a.kurakina@school1298.ru']:
                    continue

                # Обрабатываем классы руководства
                class_str = teacher.get('classStr')
                leader_groups = None
                if class_str and class_str.strip():
                    leader_groups = [group.strip() for group in class_str.split(',') if group.strip()]

                # Формируем URL изображения
                image_url = None
                if teacher.get('image'):
                    image_url = f"https://school1298.ru/portal/workers/image/teachers/{teacher.get('image')}"

                teachers.append(TeacherResponse(
                    uid=str(teacher.get('Id')),
                    display_name=teacher.get('name', 'Unknown Teacher'),
                    image=image_url,
                    leader_groups=leader_groups,
                    email=teacher.get('email'),
                ))

            except Exception as e:
                print(f"Ошибка обработки учителя: {e}")
                continue

    except Exception as e:
        print(f'Ошибка получения учителей: {e}')

    return teachers


def get_students_external() -> List[StudentResponse]:
    """Получение данных учеников из внешней БД"""
    students = []
    connection = None
    cursor = None

    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT personid, email, firstName, lastName, patronymic, className
            FROM students 
            WHERE archive = 0
        """)

        for student in cursor.fetchall():
            try:
                if not student.get('personid'):
                    continue

                # Формируем display_name
                first_name = student.get('firstName', '').strip()
                last_name = student.get('lastName', '').strip()
                patronymic = student.get('patronymic', '').strip()
                display_name = f"{last_name} {first_name} {patronymic}".strip()

                if not display_name:
                    display_name = f"Ученик {student.get('personid')}"

                students.append(StudentResponse(
                    uid=str(student.get('personid')),
                    display_name=display_name,
                    email=student.get('email'),
                    group_name=student.get('className'),
                    first_name=first_name,
                    last_name=last_name,
                    patronymic=patronymic
                ))

            except Exception as e:
                print(f"Ошибка обработки студента: {e}")
                continue

    except Error as e:
        print(f"❌ Ошибка подключения к БД: {e}")
    except Exception as e:
        print(f"❌ Ошибка получения студентов: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

    return students