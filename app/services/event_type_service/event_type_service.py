# app/services/event_type_service.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from typing import List, Optional
from app.database.models import EventType, Stage, PossibleResult, User,Event
from app.services.event_type_service.schemas import EventTypeResponse

class EventTypeService:
    def __init__(self, db: Session):
        self.db = db

    def get_all_event_types_with_details(self) -> List[EventType]:
        """
        Получение всех типов мероприятий с полной информацией
        включая стадии, возможные результаты и руководителя
        """
        try:
            event_types = (
                self.db.query(EventType)
                .options(
                    joinedload(EventType.stages).joinedload(Stage.possible_results),
                    joinedload(EventType.leader)
                )
                .order_by(EventType.title)
                .all()
            )
            return event_types
        except Exception as e:
            raise Exception(f"Ошибка при получении типов мероприятий: {str(e)}")

    def get_event_type_by_id(self, event_type_id: int) -> Optional[EventType]:
        """
        Получение типа мероприятия по ID с полной информацией
        """
        try:
            event_type = (
                self.db.query(EventType)
                .options(
                    joinedload(EventType.stages).joinedload(Stage.possible_results),
                    joinedload(EventType.leader)
                )
                .filter(EventType.id == event_type_id)
                .first()
            )
            return event_type
        except Exception as e:
            raise Exception(f"Ошибка при получении типа мероприятия: {str(e)}")

    def create_event_type(self, event_type_data: dict) -> EventType:
        """
        Создание нового типа мероприятия
        """
        try:
            # Проверяем уникальность названия
            existing = (
                self.db.query(EventType)
                .filter(EventType.title == event_type_data["title"])
                .first()
            )
            if existing:
                raise ValueError("Тип мероприятия с таким названием уже существует")

            # Проверяем руководителя (если указан)
            if event_type_data.get("leader_id"):
                leader = self.db.query(User).filter(User.id == event_type_data["leader_id"]).first()
                if not leader:
                    raise ValueError("Указанный руководитель не найден")

            # Создаем тип мероприятия
            event_type = EventType(
                title=event_type_data["title"],
                description=event_type_data.get("description"),
                leader_id=event_type_data.get("leader_id"),
                min_stages_for_completion=event_type_data.get("min_stages_for_completion", 0)
            )

            self.db.add(event_type)
            self.db.flush()  # Получаем ID для создания стадий

            # Создаем стадии и результаты
            if event_type_data.get("stages"):
                for stage_data in event_type_data["stages"]:
                    stage = Stage(
                        event_type_id=event_type.id,
                        title=stage_data["title"],
                        min_score_for_finished=stage_data["min_score_for_finished"],
                        stage_order=stage_data["stage_order"]
                    )
                    self.db.add(stage)
                    self.db.flush()

                    # Создаем возможные результаты
                    if stage_data.get("possible_results"):
                        for result_data in stage_data["possible_results"]:
                            result = PossibleResult(
                                stage_id=stage.id,
                                title=result_data["title"],
                                points_for_done=result_data["points_for_done"]
                            )
                            self.db.add(result)

            self.db.commit()
            self.db.refresh(event_type)

            # Возвращаем созданный объект с полной информацией
            return self.get_event_type_by_id(event_type.id)

        except ValueError:
            raise
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Ошибка при создании типа мероприятия: {str(e)}")

    def update_event_type(self, event_type_id: int, update_data: dict) -> Optional[EventType]:
        """
        Обновление типа мероприятия
        """
        try:
            event_type = self.get_event_type_by_id(event_type_id)
            if not event_type:
                return None

            # Проверяем уникальность названия
            if "title" in update_data and update_data["title"] != event_type.title:
                existing = (
                    self.db.query(EventType)
                    .filter(
                        and_(
                            EventType.title == update_data["title"],
                            EventType.id != event_type_id
                        )
                    )
                    .first()
                )
                if existing:
                    raise ValueError("Тип мероприятия с таким названием уже существует")

            # Проверяем руководителя
            if "leader_id" in update_data and update_data["leader_id"] != event_type.leader_id:
                if update_data["leader_id"]:
                    leader = self.db.query(User).filter(User.id == update_data["leader_id"]).first()
                    if not leader:
                        raise ValueError("Указанный руководитель не найден")

            # Обновляем основные поля
            for field, value in update_data.items():
                if field not in ["stages"]:  # Стадии обрабатываем отдельно
                    setattr(event_type, field, value)

            # TODO: Добавить логику обновления стадий и результатов при необходимости

            self.db.commit()
            self.db.refresh(event_type)

            return self.get_event_type_by_id(event_type_id)

        except ValueError:
            raise
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Ошибка при обновлении типа мероприятия: {str(e)}")

    def delete_event_type(self, event_type_id: int) -> bool:
        """
        Удаление типа мероприятия
        """
        try:
            event_type = self.get_event_type_by_id(event_type_id)
            if not event_type:
                return False

            # Проверяем, есть ли связанные мероприятия
            if event_type.events:
                raise ValueError("Нельзя удалить тип мероприятия, к которому привязаны мероприятия")

            self.db.delete(event_type)
            self.db.commit()
            return True

        except ValueError:
            raise
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Ошибка при удалении типа мероприятия: {str(e)}")

    def get_event_types_by_leader(self, leader_id: int) -> List[EventTypeResponse]:
        """
        Получение типов мероприятий по ID руководителя
        """
        try:
            event_types = (
                self.db.query(EventType)
                .options(
                    joinedload(EventType.stages).joinedload(Stage.possible_results),
                    joinedload(EventType.leader)
                )
                .filter(EventType.leader_id == leader_id)
                .order_by(EventType.title)
                .all()
            )
            return event_types
        except Exception as e:
            raise Exception(f"Ошибка при получении типов мероприятий руководителя: {str(e)}")