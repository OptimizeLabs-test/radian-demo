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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    # Startup
    app.state.settings = settings
    app.state.chunk_repo = await PatientChunkRepository.create(
        settings.database_url,
        min_size=settings.pg_pool_min_size,
        max_size=settings.pg_pool_max_size,
    )
    app.state.log_repo = await RagLogRepository.create(
        settings.database_url,
        min_size=settings.pg_pool_min_size,
        max_size=settings.pg_pool_max_size,
    )
    app.state.rag_service = RagService(settings, app.state.chunk_repo, app.state.log_repo)
    
    # Log that logging is initialized
    import logging
    logger = logging.getLogger(__name__)
    logger.info("RAG logging initialized and ready")
    
    yield  # App runs here
    
    # Shutdown
    if hasattr(app.state, "chunk_repo"):
        await app.state.chunk_repo.close()
    if hasattr(app.state, "log_repo"):
        await app.state.log_repo.close()


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development (change this in production!)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": f"Internal server error: {str(exc)}",
            "code": "INTERNAL_SERVER_ERROR",
            "details": {},
        },
    )


@app.get("/healthz", tags=["system"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}

