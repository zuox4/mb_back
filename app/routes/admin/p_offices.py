from fastapi import APIRouter
from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db
from app.database.models import Event, EventType, Stage, Group, ProjectOffice, p_office_group_association
from sqlalchemy.orm import Session
router = APIRouter()

