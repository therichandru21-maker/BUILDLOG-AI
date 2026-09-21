from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.activities import router as activities_router
from app.api.github import router as github_router
from app.api.reports import router as reports_router
from app.config import settings
from app.database.connection import test_database_connection


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "AI-powered personal developer intelligence platform "
        "that tracks engineering activity, learning, skills, "
        "projects, and growth."
    ),
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(github_router)
app.include_router(activities_router)
app.include_router(reports_router)


@app.get("/")
def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }


@app.get("/health")
def health():
    database_connected = test_database_connection()

    return {
        "status": "healthy" if database_connected else "degraded",
        "database": (
            "connected" if database_connected else "disconnected"
        ),
    }