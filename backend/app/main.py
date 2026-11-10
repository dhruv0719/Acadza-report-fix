from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings

app = FastAPI(
    title="Acadza AI Report-to-Fix System API",
    description="Backend API powering the triage engine and faculty console for Acadza question defects.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/")
def root():
    return {
        "service": "Acadza AI Report-to-Fix System",
        "docs": "/docs",
        "health": "/api/health",
    }

