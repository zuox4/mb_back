from sqlalchemy.orm import relationship

from ..database import Base
from sqlalchemy import JSON, Column, Integer, String, ForeignKey, DateTime, func


class Achievement(Base):
    __tablename__ = "student_achievements"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # ← вместо student_external_id

    event_id = Column(
        Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False
    )
    stage_id = Column(
        Integer, ForeignKey("stages.id", ondelete="CASCADE"), nullable=False
    )
    result_id = Column(
        Integer, ForeignKey("possible_results.id", ondelete="CASCADE"), nullable=False
    )

    achieved_at = Column(DateTime, server_default=func.now())
    proof_document_path = Column(String(255))

    student_data = Column(JSON, nullable=True)
    teacher = relationship(
        "User", back_populates="achievements_given", foreign_keys=[teacher_id]
    )
    student = relationship(
        "User",
        back_populates="achievements_received",
        foreign_keys=[student_id]
    )
    stage = relationship("Stage", back_populates="achievements")
    event = relationship("Event", back_populates="achievements")
    result = relationship("PossibleResult", back_populates="achievements")

    def __repr__(self):
        return f"<Achievement Student#{self.student_id} Event#{self.event_id}>"
