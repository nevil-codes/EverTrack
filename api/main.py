"""Application factory.

Run it with:  uvicorn api.main:app --reload
Interactive docs:  http://localhost:8000/docs
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from api.deps import settings
from api.routers import achievements, habits, logs, stats
from core.models import ValidationError

DESCRIPTION = """
HTTP interface to EverTrack.

The desktop app and this API share one domain package (`core/`) and one storage
interface (`core.repository.Repository`), so both see the same data and the same
rules. Nothing in here re-implements business logic.
"""


def create_app() -> FastAPI:
    config = settings()
    app = FastAPI(
        title=config.title,
        version=config.version,
        description=DESCRIPTION,
        openapi_tags=[
            {"name": "habits", "description": "Create, list and delete habits."},
            {"name": "logs", "description": "Log activities, including from plain English."},
            {"name": "stats", "description": "Rollups: totals, streaks, per-day and per-habit."},
            {"name": "achievements", "description": "Badges earned and still to earn."},
        ],
    )

    @app.exception_handler(ValidationError)
    def domain_validation_error(_request: Request, exc: ValidationError) -> JSONResponse:
        """A domain rule rejected the request; report it as a 422, not a 500."""
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.get("/health", tags=["meta"], summary="Liveness probe")
    def health() -> dict:
        return {"status": "ok", "version": config.version, "database": config.database}

    app.include_router(habits.router)
    app.include_router(logs.router)
    app.include_router(stats.router)
    app.include_router(achievements.router)
    return app


app = create_app()
