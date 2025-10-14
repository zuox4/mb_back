from typing import List, TypeVar, Generic
from sqlalchemy.orm import Session
from datetime import datetime
from app.database.models import User, Role

from app.services.sync_service.schemas.sync_schemas import SyncStats

T = TypeVar('T')


class BaseSyncService(Generic[T]):
    """Базовый класс для сервисов синхронизации"""

    def __init__(self, role_name: str):
        self.role_name = role_name

    def sync(self, db: Session, external_data: List[T]) -> SyncStats:
        """Базовый метод синхронизации"""
        stats = SyncStats(total_external=len(external_data))

        try:
            role = self._get_role(db)
            if not role:
                stats.errors.append(f"Роль '{self.role_name}' не найдена")
                return stats

            external_ids = [item.uid for item in external_data]

            # Синхронизация данных
            for item in external_data:
                self._process_single_item(db, item, role, stats)

            # Архивирование отсутствующих
            stats.archived = self._archive_missing(db, external_ids)

            db.commit()
            self._print_stats(stats)

        except Exception as e:
            db.rollback()
            stats.errors.append(f"Критическая ошибка: {str(e)}")

        return stats

    def _get_role(self, db: Session) -> Role:
        """Получение роли"""
        return db.query(Role).filter_by(name=self.role_name).first()

    def _process_single_item(self, db: Session, item: T, role: Role, stats: SyncStats):
        """Обработка одного элемента"""
        try:
            existing_user = db.query(User).filter(User.external_id == item.uid).first()

            if existing_user:
                if self._update_item(existing_user, item, role):
                    stats.updated += 1
                    print(f"🔄 Обновлен: {item.display_name}")
            else:
                self._add_item(db, item, role)
                stats.added += 1
                db.commit()  # Коммитим каждую новую запись
                print(f"✅ Добавлен: {item.display_name}")

        except Exception as e:
            stats.errors.append(f"{item.display_name}: {str(e)}")
            print(f"❌ Ошибка: {item.display_name} - {e}")

    def _update_item(self, user: User, item: T, role: Role) -> bool:
        """Обновление существующего пользователя"""
        has_changes = False

        # Обновление email
        if self._should_update_email(user, item):
            user.email = self._get_item_email(item)
            has_changes = True

        # Обновление display_name
        if item.display_name and user.display_name != item.display_name:
            user.display_name = item.display_name
            has_changes = True

        # Обновление специфичных полей
        has_changes |= self._update_specific_fields(user, item)

        # Добавление роли если нужно
        if role not in user.roles:
            user.roles.append(role)
            has_changes = True

        # Восстановление из архива
        if user.archived:
            user.archived = False
            has_changes = True

            print(f"♻️  Восстановлен: {user.display_name}")

        if has_changes:
            user.updated_at = datetime.now()


        return has_changes

    def _add_item(self, db: Session, item: T, role: Role):
        """Добавление нового пользователя"""
        email = self._get_item_email(item)
        if not email:
            raise ValueError("Отсутствует email")

        user_data = {
            'external_id': item.uid,
            'email': email,
            'display_name': item.display_name,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'archived': False
        }

        # Добавляем специфичные поля
        user_data.update(self._get_specific_fields(item))

        user = User(**user_data)
        user.roles.append(role)
        db.add(user)

    def _archive_missing(self, db: Session, external_ids: List[str]) -> int:
        """Архивация отсутствующих пользователей"""
        try:
            missing_users = db.query(User).join(User.roles).filter(
                Role.name == self.role_name,
                User.archived == False,
                ~User.external_id.in_(external_ids)
            ).all()

            for user in missing_users:
                user.archived = True
                user.updated_at = datetime.now()
                print(f"🚫 Архивирован: {user.display_name}")

            db.commit()
            return len(missing_users)

        except Exception as e:
            db.rollback()
            print(f"❌ Ошибка архивации: {e}")
            return 0

    def _print_stats(self, stats: SyncStats):
        """Вывод статистики"""
        print(f"\n📊 Синхронизация {self.role_name} завершена:")
        print(f"   Добавлено: {stats.added}")
        print(f"   Обновлено: {stats.updated}")
        print(f"   Архивировано: {stats.archived}")
        print(f"   Ошибок: {len(stats.errors)}")

    # Абстрактные методы для реализации в дочерних классах
    def _should_update_email(self, user: User, item: T) -> bool:
        raise NotImplementedError

    def _get_item_email(self, item: T) -> str:
        raise NotImplementedError

    def _update_specific_fields(self, user: User, item: T) -> bool:
        raise NotImplementedError

    def _get_specific_fields(self, item: T) -> dict:
        raise NotImplementedError