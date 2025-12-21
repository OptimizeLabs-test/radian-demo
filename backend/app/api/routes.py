"""
API routes consumed by the React frontend.
"""

import json
from typing import AsyncIterator, Literal
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from pydantic import BaseModel, Field

from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    IntroMessageResponse,
    PatientSummary,
    SpecialtyPerspective,
    SystemContext,
)
from app.services.rag import RagService

router = APIRouter(prefix="/patients", tags=["patients"])


def get_rag_service(request: Request) -> RagService:
    return request.app.state.rag_service  # type: ignore[attr-defined]


@router.get("/{patient_id}/summary", response_model=PatientSummary)
async def get_summary(patient_id: str, rag: RagService = Depends(get_rag_service)) -> PatientSummary:
    system_context = SystemContext(
        context_mode="summary",
        patient_scope="locked",
        reference_time=datetime.now(timezone.utc).isoformat()
    )
    return await rag.generate_patient_summary(patient_id, system_context)


@router.get("/{patient_id}/specialties", response_model=list[SpecialtyPerspective])
async def get_specialties(
    patient_id: str, rag: RagService = Depends(get_rag_service)
) -> list[SpecialtyPerspective]:
    return [
        SpecialtyPerspective(
            specialty="Specialty Perspectives",
            insights=["Coming soon"]
        )
    ]


@router.get("/{patient_id}/intro-message", response_model=IntroMessageResponse)
async def get_intro_message(patient_id: str, rag: RagService = Depends(get_rag_service)) -> IntroMessageResponse:
    message = await rag.generate_intro_message(patient_id)
    return IntroMessageResponse(message=message)


@router.post("/{patient_id}/chat", response_model=ChatResponse)
async def post_chat(patient_id: str, payload: ChatRequest, rag: RagService = Depends(get_rag_service)) -> ChatResponse:
    """Handle chat questions with error handling."""
    try:
        # Generate system context if not provided (hidden from frontend)
        if payload.systemContext is None:
            system_context = SystemContext(
                context_mode="rag",
                patient_scope="locked",
                reference_time=datetime.now(timezone.utc).isoformat()
            )
        else:
            system_context = payload.systemContext
        
        answer = await rag.answer_question(
            patient_id, 
            payload.question, 
            payload.conversationHistory,
            system_context
        )
        return ChatResponse(message=answer)
    except Exception as e:
        # Log the error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error processing chat request for patient {patient_id}: {str(e)}", exc_info=True)
        
        # Return a user-friendly error message
        from app.core.errors import APIException
        raise APIException(
            message=f"Failed to process chat request: {str(e)}",
            details={"patient_id": patient_id, "question": payload.question[:100]}
        )


@router.post("/{patient_id}/chat/stream")
async def post_chat_stream(
    patient_id: str,
    payload: ChatRequest,
    rag: RagService = Depends(get_rag_service),
) -> StreamingResponse:
    """Simple SSE wrapper that chunks the final answer."""
    
    # Generate system context if not provided
    if payload.systemContext is None:
        system_context = SystemContext(
            context_mode="rag",
            patient_scope="locked",
            reference_time=datetime.now(timezone.utc).isoformat()
        )
    else:
        system_context = payload.systemContext

    async def event_generator() -> AsyncIterator[str]:
        answer = await rag.answer_question(
            patient_id, 
            payload.question, 
            payload.conversationHistory,
            system_context
        )
        for sentence in answer.split(". "):
            chunk = sentence.strip()
            if not chunk:
                continue
            yield f"data: {json.dumps({'content': chunk + '. '})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

