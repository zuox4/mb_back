import datetime
from typing import List
from sqlalchemy.orm import Session
from app.services.sync_service.schemas.sync_schemas import StudentResponse, SyncStats
from app.services.sync_service.base_sync_service import BaseSyncService
from app.services.sync_service.external_services import get_students_external
from app.auth.utils import get_password_hash
from app.database.models import User, Role


class StudentSyncService(BaseSyncService[StudentResponse]):
    """Сервис синхронизации учеников"""

    def __init__(self):
        super().__init__("student")

    def sync_students(self, db: Session) -> SyncStats:
        """Синхронизация учеников"""
        students = get_students_external()
        print(f"👨‍🎓 Найдено учеников: {len(students)}")
        return self.sync(db, students)

    def _should_update_email(self, user: User, student: StudentResponse) -> bool:
        """Проверяет нужно ли обновлять email ученика"""
        # В базовом классе теперь используется email_mapping, так что всегда возвращаем True
        # чтобы email обновлялся согласно маппингу
        return True

    def _get_external_email(self, student: StudentResponse) -> str:
        """Получает email из внешней БД или генерирует новый если его нет"""
        # Используем email из внешней БД если он валидный
        if student.email and student.email.strip() and student.email.lower() != 'none':
            return student.email.strip().lower()

        # Если во внешней БД нет email, генерируем его
        return self._generate_student_email(student)

    def _get_item_email(self, student: StudentResponse) -> str:
        """Получает email для использования"""
        return self._get_external_email(student)

    def _generate_student_email(self, student: StudentResponse) -> str:
        """Генерация email для ученика если его нет во внешней БД"""
        first_name = (student.first_name or '').strip().lower()
        last_name = (student.last_name or '').strip().lower()

        first_name_clean = ''.join(c for c in first_name if c.isalnum())
        last_name_clean = ''.join(c for c in last_name if c.isalnum())

        if first_name_clean and last_name_clean:
            base_email = f"{first_name_clean}.{last_name_clean}"
        elif first_name_clean:
            base_email = first_name_clean
        elif last_name_clean:
            base_email = last_name_clean
        else:
            base_email = f"student.{student.uid[:8]}"

        return f"{base_email}@school1298.ru"

    def _update_specific_fields(self, user: User, student: StudentResponse) -> bool:
        """Обновление специфичных полей ученика"""
        has_changes = False

        if student.group_name and user.group_name != student.group_name:
            user.group_name = student.group_name
            has_changes = True
            print(f"📚 Изменена группа: {user.display_name} -> {student.group_name}")

        return has_changes

    def _get_specific_fields(self, student: StudentResponse) -> dict:
        """Получение специфичных полей для нового ученика"""
        return {
            'group_name': student.group_name,
            'password_hash': get_password_hash("temporary_password_123")
        }

    # УБРАТЬ переопределенный _process_single_item - использовать базовый