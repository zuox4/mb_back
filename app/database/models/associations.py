from sqlalchemy import Table, Column, Integer, String, ForeignKey, Boolean
from app.database.database import Base

# Ассоциативная таблица для групп
p_office_group_association = Table(
    'p_office_group_association',
    Base.metadata,
    Column('p_office_id', Integer, ForeignKey('project_offices.id')),
    Column('group_id', Integer, ForeignKey('groups.id'))
)

# Ассоциативная таблица для событий
p_office_event_association = Table(
    'p_office_event_association',
    Base.metadata,
    Column('p_office_id', Integer, ForeignKey('project_offices.id',ondelete='CASCADE')),
    Column('event_id', Integer, ForeignKey('events.id',ondelete='CASCADE')),
    Column('is_important', Boolean, default=False),  # Добавляем флаг важности
)

# Ассоциативная таблица для ролей пользователей
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)