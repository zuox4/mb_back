from fastapi import APIRouter
from sqlalchemy.orm import Session
from fastapi import Depends

from app.auth.dependencies import get_current_active_teacher
from app.database import get_db
from app.database.models import EventType, Stage
from app.services.sync_service import TeacherSyncService
from app.services.sync_service import StudentSyncService
from sqlalchemy.orm import joinedload
router = APIRouter()



@router.get("/sync_teachers")
def sync_teachers(db: Session = Depends(get_db)):
    teacher_service = TeacherSyncService()
    teacher_result = teacher_service.sync_teachers(db)

    return {"message": f"{teacher_result}"}



@router.get("/sync_students")
def sync_teachers(db: Session = Depends(get_db)):

    sync_service = StudentSyncService()
    student_result = sync_service.sync_students(db)

    return {"message": f"{student_result}"}


@router.get("/all_event_types")
def get_all_events(db: Session = Depends(get_db)):
    events = (
        db.query(EventType)
        .options(
            joinedload(EventType.stages).joinedload(Stage.possible_results),
            joinedload(EventType.leader)
        )
        .all()
    )

    return events