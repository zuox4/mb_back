from sqlalchemy.orm import relationship


from ..database import Base
from sqlalchemy import Column, Integer, String

class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    # Добавляем relationship с back_populates
    project_offices = relationship(
        "ProjectOffice",
        secondary="p_office_group_association",
        back_populates="accessible_classes",  # связываем с существующим relationship
        lazy="selectin"
    )

    def __str__(self):
        return f"{self.name}"
