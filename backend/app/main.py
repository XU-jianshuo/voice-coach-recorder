from collections.abc import Generator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import sessionmaker

from app import models  # noqa: F401
from app.config import Settings, get_settings
from app.db import Base, create_engine_for, get_db
from app.errors import error_response
from app.routers.audio_sessions import router as audio_sessions_router
from app.routers.daily_review import router as daily_review_router
from app.routers.health import router as health_router
from app.routers.hotwords import router as hotwords_router
from app.routers.speaker_profiles import router as speaker_profiles_router
from app.routers.transcript_segments import router as transcript_segments_router
from app.services.hotwords import seed_default_hotwords


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()
    app_engine = create_engine_for(app_settings)
    app_session_local = sessionmaker(
        bind=app_engine, autoflush=False, autocommit=False
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        Base.metadata.create_all(bind=app_engine)
        db = app_session_local()
        try:
            seed_default_hotwords(db)
        finally:
            db.close()
        yield

    app = FastAPI(title=app_settings.app_name, lifespan=lifespan)

    def get_app_settings() -> Settings:
        return app_settings

    def get_app_db() -> Generator:
        db = app_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_settings] = get_app_settings
    app.dependency_overrides[get_db] = get_app_db

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc: HTTPException):
        if isinstance(exc.detail, dict) and "error" in exc.detail:
            return error_response(
                exc.status_code,
                exc.detail["error"]["code"],
                exc.detail["error"]["message"],
            )
        return error_response(exc.status_code, "http_error", str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc: RequestValidationError):
        return error_response(422, "invalid_request", "Request validation failed")

    app.include_router(health_router)
    app.include_router(audio_sessions_router, prefix=app_settings.api_prefix)
    app.include_router(hotwords_router, prefix=app_settings.api_prefix)
    app.include_router(speaker_profiles_router, prefix=app_settings.api_prefix)
    app.include_router(transcript_segments_router, prefix=app_settings.api_prefix)
    app.include_router(daily_review_router, prefix=app_settings.api_prefix)
    return app


app = create_app()
