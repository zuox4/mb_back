from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database.database import Base
from app.database.models.associations import p_office_event_association, p_office_group_association


class ProjectOffice(Base):
    __tablename__ = "project_offices"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    description = Column(String(500))
    logo_url = Column(String(500))
    is_active = Column(Boolean, default=True)

    # Внешний ключ для связи с владельцем проекта
    leader_uid = Column(Integer, ForeignKey('users.id'))

    # Отношение многие-ко-многим для классов
    accessible_classes = relationship(
        "Group",
        secondary=p_office_group_association,
        back_populates="project_offices",  # добавляем back_populates
        lazy="selectin"
    )
    # Отношение к владельцу проекта
    leader = relationship("User", back_populates="p_office")

    # Отношение многие-ко-многим для событий
    accessible_events = relationship("Event", secondary=p_office_event_association)

    def __repr__(self):
        return f"<ProjectOffice {self.title}>"