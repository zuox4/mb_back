
from ..database import Base
from sqlalchemy import Column, Integer, String

class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    def __str__(self):
        return f"{self.name}"