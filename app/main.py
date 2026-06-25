import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.alerting import send_alert
from app.config import settings
from app.database import Base, engine
from app.logging_config import RequestLoggingMiddleware, configure_logging, logger
from app.routers import auth, documents, dossiers, vehicles
from app.routers.auth import limiter

configure_logging()

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

app.include_router(auth.router)
app.include_router(vehicles.router)
app.include_router(dossiers.router)
app.include_router(documents.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(
        "unhandled_exception",
        exc_info=exc,
        extra={"extra_fields": {"path": request.url.path, "method": request.method}},
    )
    send_alert(
        title="Unhandled exception in M-Motors API",
        detail=f"{request.method} {request.url.path} -> {type(exc).__name__}: {exc}",
    )
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": "Internal server error"})


@app.get("/health")
def health():
    return {"status": "ok", "environment": settings.environment}
