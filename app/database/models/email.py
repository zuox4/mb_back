from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.sql import func
from app.database.database import Base


class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=False)
    template_name = Column(String(100), nullable=True)
    status = Column(String(20), nullable=False)  # sent, failed, pending
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<EmailLog {self.email} - {self.status}>"
