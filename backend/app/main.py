"""
FastAPI entrypoint for the TARA backend.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router as patient_router
from app.core.config import get_settings
from app.core.errors import APIException
from app.repositories.patient_chunks import PatientChunkRepository
from app.repositories.rag_log import RagLogRepository
from app.services.rag import RagService

settings = get_settings()

# Global state for serverless (reused across invocations)
_app_state = {
    "chunk_repo": None,
    "log_repo": None,
    "rag_service": None,
    "initialized": False,
}


async def initialize_app_state():
    """Initialize app state (lazy initialization for serverless)."""
    if _app_state["initialized"]:
        return
    
    _app_state["chunk_repo"] = await PatientChunkRepository.create(
        settings.database_url,
        min_size=settings.pg_pool_min_size,
        max_size=settings.pg_pool_max_size,
    )
    _app_state["log_repo"] = await RagLogRepository.create(
        settings.database_url,
        min_size=settings.pg_pool_min_size,
        max_size=settings.pg_pool_max_size,
    )
    _app_state["rag_service"] = RagService(settings, _app_state["chunk_repo"], _app_state["log_repo"])
    _app_state["initialized"] = True
    
    import logging
    logger = logging.getLogger(__name__)
    logger.info("RAG logging initialized and ready")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    # Startup - only for non-serverless environments
    await initialize_app_state()
    app.state.settings = settings
    app.state.chunk_repo = _app_state["chunk_repo"]
    app.state.log_repo = _app_state["log_repo"]
    app.state.rag_service = _app_state["rag_service"]
    
    yield  # App runs here
    
    # Shutdown - only for non-serverless environments
    # Note: In serverless, we don't close connections as they may be reused


app = FastAPI(title=settings.app_name, lifespan=lifespan)

# Middleware to ensure state is initialized (for serverless)
@app.middleware("http")
async def ensure_initialized(request: Request, call_next):
    """Ensure app state is initialized before handling requests."""
    if not _app_state["initialized"]:
        await initialize_app_state()
        request.app.state.chunk_repo = _app_state["chunk_repo"]
        request.app.state.log_repo = _app_state["log_repo"]
        request.app.state.rag_service = _app_state["rag_service"]
    return await call_next(request)

# Configure CORS based on settings
if settings.cors_allow_all_origins:
    cors_origins = ["*"]
else:
    cors_origins = [str(origin) for origin in settings.cors_origins]
    # Add additional origins from environment variable
    if settings.cors_additional_origins:
        additional = [origin.strip() for origin in settings.cors_additional_origins.split(",")]
        cors_origins.extend(additional)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Restrict methods
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],  # Restrict headers
)

app.include_router(patient_router, prefix=settings.api_prefix)


@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    return exc.to_response()


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler for unhandled errors."""
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    # Don't expose internal error details in production
    if settings.environment == "prod":
        error_message = "An internal server error occurred. Please try again later."
    else:
        error_message = f"Internal server error: {str(exc)}"
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": error_message,
            "code": "INTERNAL_SERVER_ERROR",
            "details": {},
        },
    )


@app.get("/healthz", tags=["system"])
async def health_check() -> dict[str, str]:
    """Health check endpoint. Does not expose sensitive information."""
    return {"status": "ok"}


# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Only add HSTS in production
    if settings.environment == "prod":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response

