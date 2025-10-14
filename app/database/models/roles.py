from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String
from .associations import user_roles

import enum
from ..database import Base


class RoleName(str, enum.Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"
    PARENT = "parent"


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(String(255))

    users = relationship("User", secondary=user_roles, back_populates="roles")
    def __str__(self):
        return self.name