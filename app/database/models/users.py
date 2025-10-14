import enum

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from .associations import user_roles
from ..database import Base
from sqlalchemy import (
    Column,
    Text,
    DateTime,
    Integer,
    String,
    ForeignKey,
    Date,
    Boolean,
    Enum,
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=True)

    # поля регистрации
    is_active = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)

    # нужно пройти регистрацию
    requires_password = Column(Boolean, default=True)

    verification_token = Column(String(100), nullable=True, index=True)
    verification_sent_at = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    email_verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

    # Дополнительные поля
    display_name = Column(String(255), nullable=True)
    phone = Column(String, nullable=True)  # Новое поле
    image = Column(String(500), nullable=True)
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    about = Column(Text, nullable=True)
    max_link_url = Column(String(255), nullable=True)
    archived = Column(Boolean, nullable=False, default=False)


    # поля ученика
    group_name = Column(String(255), nullable=True)
    achievements_received = relationship(
        "Achievement",
        back_populates="student",
        foreign_keys="Achievement.student_id"
    )

    # поля сотрудника
    groups_leader = Column(JSONB, nullable=True) # строка из классов где он классный
    p_office = relationship("ProjectOffice", back_populates="leader") # строка из оффисов, где он руководитель
    event_types = relationship("EventType", back_populates="leader") # строка из типов мероприятий, где он ответственный
    achievements_given = relationship(
        "Achievement", back_populates="teacher", foreign_keys="Achievement.teacher_id"
    ) # результаты, которые проставил


    def __str__(self):
        return self.display_name