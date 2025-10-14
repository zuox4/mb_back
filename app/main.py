from fastapi import FastAPI, Depends, APIRouter
from sqlalchemy.orm import Session
from starlette.staticfiles import StaticFiles

from app.admin import setup_admin
from app.database.database import engine, get_db
from app.database import Base
from app.routes import admin_router, api_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Educational Achievement Platform",
    description="API для управления образовательными достижениями",
    version="1.0.0",
)
origins = [
    "http://localhost",
    "http://localhost:8080",
    "https://your-frontend-domain.com",
]

app.mount("/static/logos", StaticFiles(directory="static/logos"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  # List of allowed origins
    allow_credentials=True,  # Allow cookies and authorization headers
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)
admin = setup_admin(app)
app.include_router(api_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn



    uvicorn.run(app, host="0.0.0.0", port=8000)
