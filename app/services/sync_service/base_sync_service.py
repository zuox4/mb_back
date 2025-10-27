from typing import List, TypeVar, Generic
from sqlalchemy.orm import Session
from datetime import datetime
import random
import string
from app.database.models import User, Role
from app.services.sync_service.schemas.sync_schemas import SyncStats

T = TypeVar('T')


class BaseSyncService(Generic[T]):
    """Базовый класс для сервисов синхронизации"""

    def __init__(self, role_name: str):
        self.role_name = role_name

    def sync(self, db: Session, external_data: List[T]) -> SyncStats:
        """Базовый метод синхронизации"""
        stats = SyncStats(
            total_external=len(external_data),
            added=0,
            updated=0,
            errors=[],
            archived=0
        )

        try:
            role = self._get_role(db)
            if not role:
                stats.errors.append(f"Роль '{self.role_name}' не найдена")
                return stats

            external_ids = [item.uid for item in external_data]

            # ПРЕДВАРИТЕЛЬНАЯ ОБРАБОТКА: собираем все email и находим конфликты
            email_mapping = self._prepare_email_mapping(db, external_data)

            # Синхронизация данных - ОДНОЙ ТРАНЗАКЦИЕЙ
            for item in external_data:
                self._process_single_item(db, item, role, stats, email_mapping)

            # Архивирование отсутствующих
            stats.archived = self._archive_missing(db, external_ids)

            db.commit()
            self._print_stats(stats)

        except Exception as e:
            db.rollback()
            stats.errors.append(f"Критическая ошибка: {str(e)}")
            print(f"💥 Транзакция откатана: {e}")

        return stats

    def _get_role(self, db: Session) -> Role:
        """Получение роли"""
        return db.query(Role).filter_by(name=self.role_name).first()

    def _prepare_email_mapping(self, db: Session, external_data: List[T]) -> dict:
        """Подготовка маппинга email для избежания конфликтов"""
        email_mapping = {}

        # Собираем все email из внешних данных
        all_emails = []
        for item in external_data:
            email = self._get_item_email(item)
            if email:
                all_emails.append(email)

        # Находим дубликаты во внешних данных
        from collections import Counter
        email_counts = Counter(all_emails)
        duplicates = {email for email, count in email_counts.items() if count > 1}

        # Обрабатываем каждый email
        for item in external_data:
            original_email = self._get_item_email(item)
            if not original_email:
                continue

            # Если email дублируется во внешних данных, генерируем уникальный
            if original_email in duplicates:
                unique_email = self._generate_unique_email(original_email, db)
                email_mapping[item.uid] = unique_email
                print(f"⚠️ Дубликат email: {original_email} -> {unique_email}")
            else:
                # Проверяем конфликт с существующими пользователями
                existing_user = db.query(User).filter(User.email == original_email).first()
                if existing_user and existing_user.external_id != item.uid:
                    # Конфликт - генерируем уникальный email
                    unique_email = self._generate_unique_email(original_email, db)
                    email_mapping[item.uid] = unique_email
                    print(f"⚠️ Конфликт email: {original_email} занят {existing_user.display_name} -> {unique_email}")
                else:
                    # Email валиден
                    email_mapping[item.uid] = original_email

        return email_mapping

    def _process_single_item(self, db: Session, item: T, role: Role, stats: SyncStats, email_mapping: dict):
        """Обработка одного элемента"""
        try:
            existing_user = db.query(User).filter(User.external_id == item.uid).first()

            if existing_user:
                if self._update_existing_user(db, existing_user, item, role, email_mapping):
                    stats.updated += 1
                    print(f"🔄 Обновлен: {item.display_name}")
            else:
                self._add_new_user(db, item, role, email_mapping)
                stats.added += 1
                print(f"✅ Добавлен: {item.display_name}")

        except Exception as e:
            stats.errors.append(f"{item.display_name}: {str(e)}")
            print(f"❌ Ошибка: {item.display_name} - {e}")

    def _update_existing_user(self, db: Session, user: User, item: T, role: Role, email_mapping: dict) -> bool:
        """Обновление существующего пользователя"""
        has_changes = False

        # Обновление email из маппинга
        final_email = email_mapping.get(item.uid)
        if final_email and user.email != final_email:
            user.email = final_email
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
            print(f"♻️ Восстановлен: {user.display_name}")

        if has_changes:
            user.updated_at = datetime.now()

        return has_changes

    def _add_new_user(self, db: Session, item: T, role: Role, email_mapping: dict):
        """Добавление нового пользователя"""
        final_email = email_mapping.get(item.uid)
        if not final_email:
            raise ValueError("Отсутствует email")

        user_data = {
            'external_id': item.uid,
            'email': final_email,
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

    def _generate_unique_email(self, base_email: str, db: Session) -> str:
        """Генерация гарантированно уникального email"""
        name_part = base_email.split('@')[0]
        domain = base_email.split('@')[1]

        # Генерируем уникальный суффикс на основе timestamp и случайных чисел
        timestamp = int(datetime.now().timestamp() % 1000000)  # Берем последние 6 цифр
        random_suffix = random.randint(1000, 9999)
        unique_email = f"{name_part}.{timestamp}{random_suffix}@{domain}"

        return unique_email

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

            return len(missing_users)

        except Exception as e:
            print(f"❌ Ошибка архивации: {e}")
            return 0

    def _print_stats(self, stats: SyncStats):
        """Вывод статистики"""
        print(f"\n📊 Синхронизация {self.role_name} завершена:")
        print(f"   Всего во внешней системе: {stats.total_external}")
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