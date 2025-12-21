"""
Shared exception types and response helpers.
"""

from fastapi import status
from fastapi.responses import JSONResponse


class APIException(Exception):
    """Base API exception."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    error_code: str = "BAD_REQUEST"

    def __init__(self, message: str, *, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_response(self) -> JSONResponse:
        """Convert to FastAPI JSON response."""
        return JSONResponse(
            status_code=self.status_code,
            content={
                "message": self.message,
                "code": self.error_code,
                "details": self.details,
            },
        )


class NotFoundError(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "NOT_FOUND"


class ServiceUnavailableError(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code = "SERVICE_UNAVAILABLE"


class ValidationError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "VALIDATION_ERROR"

