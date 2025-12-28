"""
Pydantic schemas aligned with the React frontend contracts.
"""

from typing import Literal
from datetime import datetime
from pydantic import BaseModel, Field


class PatientSummary(BaseModel):
    headline: str = Field(..., description="Short status summary (5-10 words)")
    content: list[str] = Field(
        ..., description="Array of paragraphs highlighting trends and observations"
    )

class SpecialtyPerspective(BaseModel):
    specialty: str
    insights: list[str]


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class SystemContext(BaseModel):
    """Hidden system variables for audit and temporal consistency."""
    context_mode: Literal["summary", "rag"]
    patient_scope: str = "locked"
    reference_time: str = Field(..., description="ISO timestamp for temporal anchoring")


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=4, max_length=2000)
    conversationHistory: list[ChatMessage] = Field(default_factory=list)
    systemContext: SystemContext | None = Field(None, description="Hidden system context (auto-generated if not provided)")
    sessionId: str | None = Field(None, description="Session identifier for logging and tracking")


class ChatResponse(BaseModel):
    message: str


class IntroMessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    message: str
    code: str | None = None
    details: dict | None = None

