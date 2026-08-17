from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.infrastructure.database import Base, engine
from app.interfaces.routers import (
    auth,
    health,
    messages,
    sender_identities,
    smtp_providers,
    templates,
)
from app.interfaces.routers.contacts import lists_router, router as contacts_router
from app.interfaces.routers.suppression import router as suppression_router
from app.interfaces.routers.import_jobs import router as import_jobs_router
from app.logging import configure_logging
from app.rate_limit import limiter
from app.settings import get_settings


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Phase 1 scaffold for the AegisMail Pro email operations platform.",
        lifespan=lifespan,
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(smtp_providers.router, prefix="/api/v1")
    app.include_router(sender_identities.router, prefix="/api/v1")
    app.include_router(messages.router, prefix="/api/v1")
    app.include_router(templates.router, prefix="/api/v1")
    app.include_router(contacts_router, prefix="/api/v1")
    app.include_router(lists_router, prefix="/api/v1")
    app.include_router(suppression_router, prefix="/api/v1")
    app.include_router(import_jobs_router, prefix="/api/v1")
    Instrumentator().instrument(app).expose(app, include_in_schema=False, should_gzip=True)
    return app


app = create_app()
