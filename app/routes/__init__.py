from fastapi import APIRouter

from .admin import router as admin_router
from .auth import router as auth_router
from .user import router as user_router
from .student import router as student_router
from .event_types import router as event_type_router
from .event_leader import router as event_leader_router
from .groups import router as groups_router
from .dailary import router as daily_router
from .group_leader import router as group_leader_router
from .project_office import router as project_office_router
from .events import router as events_router

"""Тут регистрируем все роутеры с префиксами"""

api_router = APIRouter()

api_router.include_router(admin_router, prefix="/admin", tags=["admin"])
api_router.include_router(auth_router, prefix="/auth", tags=["authentification"])
api_router.include_router(user_router, prefix="/users", tags=["users"])
api_router.include_router(student_router, prefix="/student", tags=["student"])
api_router.include_router(event_type_router, prefix="/event-types", tags=["event-types"])
api_router.include_router(event_leader_router, prefix="/event-leader", tags=["event-leader"])
api_router.include_router(groups_router, prefix="/groups", tags=["groups"])
api_router.include_router(daily_router, prefix="/journal", tags=["journal"])
api_router.include_router(group_leader_router, prefix="/group-leader", tags=["group-leader"])
api_router.include_router(project_office_router, prefix="/project-office", tags=["project"])
api_router.include_router(events_router, prefix="/events", tags=["events"])

@api_router.get("/health", tags=["health"])
def api_health_check():

    return {"status": "healthy", "message": "API is running 14.10"}
