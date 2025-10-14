from app.services.sync_service.base_sync_service import BaseSyncService
from app.services.sync_service.external_services import get_teachers_external
from app.services.sync_service.schemas.sync_schemas import TeacherResponse, SyncStats
from sqlalchemy.orm import Session
from app.database.models import User, Role


class TeacherSyncService(BaseSyncService[TeacherResponse]):
    """Сервис синхронизации учителей"""

    def __init__(self):
        super().__init__("teacher")

    def sync_teachers(self, db: Session) -> SyncStats:
        """Синхронизация учителей"""
        teachers = get_teachers_external()
        print(f"👨‍🏫 Найдено учителей: {len(teachers)}")
        return self.sync(db, teachers)

    def _should_update_email(self, user: User, teacher: TeacherResponse) -> bool:
        """Проверяет нужно ли обновлять email учителя"""
        return teacher.email and user.email != teacher.email

    def _get_item_email(self, teacher: TeacherResponse) -> str:
        """Получает email учителя"""
        if not teacher.email:
            raise ValueError("У учителя отсутствует email")
        return teacher.email

    def _update_specific_fields(self, user: User, teacher: TeacherResponse) -> bool:
        """Обновление специфичных полей учителя"""
        has_changes = False

        if teacher.image != user.image:
            user.image = teacher.image
            has_changes = True
            print(f"🖼️  Обновлено фото: {user.display_name}")

        if teacher.leader_groups != user.groups_leader:
            user.groups_leader = teacher.leader_groups
            has_changes = True
            print(f"👥 Изменены классы руководства: {user.display_name} -> {teacher.leader_groups}")

        return has_changes

    def _get_specific_fields(self, teacher: TeacherResponse) -> dict:
        """Получение специфичных полей для нового учителя"""
        return {
            'image': teacher.image,
            'groups_leader': teacher.leader_groups
        }

    def _process_single_item(self, db: Session, teacher: TeacherResponse, role: Role, stats: SyncStats):
        """Обработка одного учителя с улучшенным логированием"""
        try:
            existing_user = db.query(User).filter(User.external_id == teacher.uid).first()

            if existing_user:
                if self._update_item(existing_user, teacher, role):
                    stats.updated += 1

                    # Детальное логирование изменений для учителей
                    if teacher.email and teacher.email != existing_user.email:
                        print(f"📧 Обновлен email учителя: {teacher.display_name} -> {teacher.email}")
                    else:
                        print(f"🔄 Обновлен учитель: {teacher.display_name}")
            else:
                self._add_item(db, teacher, role)
                stats.added += 1
                db.commit()
                print(f"✅ Добавлен учитель: {teacher.display_name} ({teacher.email})")

        except Exception as e:
            stats.errors.append(f"{teacher.display_name}: {str(e)}")
            print(f"❌ Ошибка учителя: {teacher.display_name} - {e}")