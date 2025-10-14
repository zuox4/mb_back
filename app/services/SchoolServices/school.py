import mysql.connector
from mysql.connector import Error
import requests

# проверяет наличие пользователя в бд школы и возвращает обьект

from pydantic import BaseModel
from typing import Optional

from sqlalchemy.dialects.mysql import aiomysql


#модели
class User(BaseModel):
    uid: str
    display_name: str
    image:Optional[str] = None
    leader_classes: Optional[list] = None
    role: Optional[str] = None


class ChekUserResponse(BaseModel):
    message: str
    status_code: int
    user: Optional[User] = None

class StudentResponse(BaseModel):
    uid: str
    display_name: str
    className: Optional[str] = None


class GroupLeaderResponse(BaseModel):
    uid: str
    display_name: str
    image:Optional[str] = None
    email:Optional[str] = None

class SchoolService:
    def __init__(self):
        self.connection_params = {
            'host': '192.168.20.61',
            'database': 'students',
            'user': 'pass_system',
            'password': 'ktSXPOr2ekCGS4cr'
        }
        self.response = requests.get('https://school1298.ru/portal/workers/workersPS-no.json', timeout=10)

    def _check_teacher(self, email):
        """Проверка учителя через внешний API"""
        try:
            self.response.raise_for_status()
            teachers_data = self.response.json()
            for i in teachers_data.get('value'):

                if i['email'] == email:
                    return User(
                        uid=str(i.get('Id')),
                        display_name=i.get('name'),
                        image=i.get('image'),
                        leader_classes=str(i.get('classStr')).split(',') if i.get('classStr') else None,
                        role='teacher',
                    )
            return None
        except requests.RequestException as e:
            return None
        except Exception as e:
            return None

    def _check_student(self, email):
        """Проверка студента в базе данных"""
        conn = None
        cursor = None
        try:
            conn = mysql.connector.connect(**self.connection_params)
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM students WHERE email = %s AND archive=0", (email,))
            result = cursor.fetchone()
            print(result.get('personid'))
            return User(
                uid=result.get('personid'),
                display_name=result.get('firstName')+' '+ result.get('lastName') +' '+ result.get('patronymic'),
                image=None,
                leader_classes=None,
                role='student'

            )
        except Error as e:
            return None
        finally:
            # Всегда закрываем ресурсы в блоке finally
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()
    def check_user_in_school_db(self, email: str):


        """Основной метод проверки пользователя для регистрации"""
        if not email:
            return {'message': 'Email не предоставлен', 'status': 400, 'user': None}

        try:
            # Сначала проверяем учителя
            teacher = self._check_teacher(email)
            if teacher:
                return ChekUserResponse(
                    message='Пользователь найден!',
                    status_code=200,
                    user=teacher,
                )

            # Затем проверяем студента
            student = self._check_student(email)

            if student:
                return ChekUserResponse(
                    message='Пользователь найден!',
                    status_code=200,
                    user=student,

                )

            # Если не найден нигде
            return ChekUserResponse(
                    message='Пользователь не найден!',
                    status_code=400,
                    user=None,
                )

        except Exception as e:
            return ChekUserResponse(
                    message='Пользователь не найден!',
                    status_code=500,
                    user=None,

                )
    def get_student_data(self, uid):
        """Почучение студента из БД"""
        conn = None
        cursor = None
        try:
            conn = mysql.connector.connect(**self.connection_params)
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM students WHERE personid = %s AND archive=0", (uid,))
            result = cursor.fetchone()
            return StudentResponse(
                uid=result.get('personid'),
                display_name=result.get('firstName')+' '+ result.get('lastName') +' '+ result.get('patronymic'),
                className=result.get('className'),
            )
        except Error as e:
            return None
        finally:
            # Всегда закрываем ресурсы в блоке finally
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def get_project_leader_by_external_id(self, external_id):
        """Получение студента из БД"""
        try:
            self.response.raise_for_status()
            teachers_data = self.response.json()

            for teacher in teachers_data.get('value', []):

                if external_id in teacher.get('Id'):
                    return GroupLeaderResponse(
                        uid=str(teacher.get('Id')),
                        display_name=teacher.get('name'),
                        email=teacher.get('email'),
                        image=f"https://school1298.ru/portal/workers/image/teachers/{teacher.get('image')}"
                    )
            return None

        except (requests.RequestException, Exception):
            return None

    def get_group_leader_by_class_name(self, group_name):
        """Получение студента из БД"""
        try:
            self.response.raise_for_status()
            teachers_data = self.response.json()

            for teacher in teachers_data.get('value', []):
                class_str = teacher.get('classStr')
                if class_str and group_name in class_str.split(','):
                    print('11111111111111111111111100000000000')
                    print(teacher)

                    return GroupLeaderResponse(
                        uid=str(teacher.get('Id')),
                        display_name=teacher.get('name'),
                        email=teacher.get('email'),
                        image=f"https://school1298.ru/portal/workers/image/teachers/{teacher.get('image')}"
                    )
            return None

        except (requests.RequestException, Exception):
            return None

