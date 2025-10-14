from sqlalchemy.orm import relationship

from ..database import Base
from sqlalchemy import Column, Integer, String, ForeignKey, Date, Boolean


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    event_type_id = Column(
        Integer, ForeignKey("event_types.id", ondelete="CASCADE"), nullable=False
    )
    description = Column(String(255), nullable=True, index=True)
    academic_year = Column(String(9))
    date_start = Column(Date, nullable=True)
    date_end = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)
    event_type = relationship("EventType", back_populates="events")
    achievements = relationship("Achievement", back_populates="event")

    def __repr__(self):
        return f"<Event {self.title} ({self.academic_year})>"
