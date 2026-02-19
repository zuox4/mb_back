from sqlalchemy.orm import relationship

from ..database import Base
from sqlalchemy import Column, Integer, String, ForeignKey,Text, Boolean


class EventType(Base):
    __tablename__ = "event_types"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text)

    events = relationship("Event", back_populates="event_type")
    stages = relationship("Stage", back_populates="event_type")
    leader_id = Column(Integer, ForeignKey("users.id"))
    min_stages_for_completion = Column(Integer, default=0)
    is_archived = Column(Boolean, default=False)

    leader = relationship("User", back_populates="event_types")

    def __repr__(self):
        return f"<EventType {self.title}>"


class Stage(Base):
    __tablename__ = "stages"

    id = Column(Integer, primary_key=True, index=True)
    event_type_id = Column(
        Integer, ForeignKey("event_types.id", ondelete="CASCADE"), nullable=False
    )
    title = Column(String(255), nullable=False)
    event_type = relationship("EventType", back_populates="stages")
    stage_order = Column(Integer, default=0)  # Порядок этапов
    min_score_for_finished = Column(Integer, default=0)

    possible_results = relationship(
        "PossibleResult", back_populates="stage", cascade="all, delete-orphan"
    )
    achievements = relationship("Achievement", back_populates="stage")  # ДОБАВЛЕНО

    def __repr__(self):
        return f"<{self.title}>"


class PossibleResult(Base):
    __tablename__ = "possible_results"

    id = Column(Integer, primary_key=True, index=True)
    stage_id = Column(
        Integer, ForeignKey("stages.id", ondelete="CASCADE"), nullable=False
    )
    points_for_done = Column(Integer, default=0)
    title = Column(String(255), nullable=False)
    stage = relationship("Stage", back_populates="possible_results")
    achievements = relationship("Achievement", back_populates="result")

    def __repr__(self):
        return f"<PossibleResult {self.title}>"
