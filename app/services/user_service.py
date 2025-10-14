import secrets
from sqlalchemy.orm import Session
from app.database.models import User, Role
from app.auth.utils import get_password_hash, verify_password
from app.services.SchoolServices import SchoolService
from typing import Optional
class UserService:
    # @staticmethod
    # def create_user(db: Session, user_data: dict) -> User:
    #     """Создание нового пользователя"""
    #     # Проверяем существует ли пользователь
    #     existing_user = db.query(User).filter(User.email == user_data['email']).first()
    #     if existing_user:
    #         raise ValueError("Пользователь с таким Email Уже существует")
    #     user_from_school_db = SchoolService().check_user_in_school_db(user_data.get('email'))
    #
    #     if user_from_school_db.status_code == 400:
    #         raise ValueError("User not found")
    #     if user_from_school_db.status_code == 500:
    #         raise ValueError("Error db")
    #     school_user = user_from_school_db.user
    #     print('Создаю пользователя_____________________')
    #     print(school_user)
    #     user = User(
    #         email=user_data['email'],
    #         password_hash=get_password_hash(user_data['password']),
    #         external_id=school_user.uid,
    #         display_name=school_user.display_name,
    #     )
    #
    #     # Назначаем роль на основе типа пользователя
    #     user_type = user_data.get('user_type', school_user.role)
    #     role = UserService._get_role_by_type(db, user_type)
    #     if role:
    #         user.roles.append(role)
    #
    #     db.add(user)
    #     db.commit()
    #     db.refresh(user)
    #
    #     return user
    #
    # @staticmethod
    # def _get_role_by_type(db: Session, user_type: str) -> Role:
    #     """Получение роли по типу пользователя"""
    #     role_name_map = {
    #         'student': 'student',
    #         'teacher': 'teacher',
    #         'parent': 'parent',
    #         'staff': 'staff',
    #         'admin': 'admin'
    #     }
    #
    #     role_name = role_name_map.get(user_type, 'student')
    #     return db.query(Role).filter(Role.name == role_name).first()

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """Аутентификация пользователя"""
        user = db.query(User).filter(User.email == email).first()
        print(user)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        # if not user.is_active:
        #     return None
        # if user.requires_password:
        #     return None
        return user

    # @staticmethod
    # def generate_verification_code() -> str:
    #     """Генерация кода верификации"""
    #     return str(secrets.randbelow(900000) + 100000)  # 6-значный код