"""
API routes consumed by the React frontend.
"""

import json
import logging
import os
import tempfile
from typing import AsyncIterator, Literal
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, UploadFile, File
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


def normalize_patient_id(patient_id: str) -> str:
    """
    Normalize patient ID to consistent format.
    Converts "P1-Sanjeev-Malhotra" -> "Sanjeev" for backward compatibility.
    """
    if patient_id.startswith("P") and "-" in patient_id:
        # Extract first name from format "P1-Sanjeev-Malhotra" or "P1-Sanjeev"
        parts = patient_id.split("-")
        if len(parts) >= 2:
            return parts[1]  # Get "Sanjeev" from "P1-Sanjeev-Malhotra"
    return patient_id


@router.get("/{patient_id}/summary", response_model=PatientSummary)
async def get_summary(patient_id: str, rag: RagService = Depends(get_rag_service)) -> PatientSummary:
    patient_id = normalize_patient_id(patient_id)
    system_context = SystemContext(
        context_mode="summary",
        patient_scope="locked",
        reference_time=datetime.now(timezone.utc).isoformat()
    )
    return await rag.generate_patient_summary(patient_id, system_context)


@router.get("/{patient_id}/summary/stream")
async def get_summary_stream(
    patient_id: str,
    rag: RagService = Depends(get_rag_service),
) -> StreamingResponse:
    """Stream patient summary as it's generated."""
    patient_id = normalize_patient_id(patient_id)
    system_context = SystemContext(
        context_mode="summary",
        patient_scope="locked",
        reference_time=datetime.now(timezone.utc).isoformat()
    )

    async def event_generator() -> AsyncIterator[str]:
        async for chunk in rag.generate_patient_summary_stream(patient_id, system_context):
            yield f"data: {json.dumps({'content': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


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
    patient_id = normalize_patient_id(patient_id)
    message = await rag.generate_intro_message(patient_id)
    return IntroMessageResponse(message=message)


@router.post("/{patient_id}/chat", response_model=ChatResponse)
async def post_chat(patient_id: str, payload: ChatRequest, rag: RagService = Depends(get_rag_service)) -> ChatResponse:
    """Handle chat questions with error handling."""
    try:
        # Normalize patient ID to ensure consistent format
        patient_id = normalize_patient_id(patient_id)
        
        # Log the incoming search query
        logger = logging.getLogger(__name__)
        logger.info(f"[RAG Query] Patient ID: {patient_id}, Question: {payload.question}")
        # print(f"\n{'='*80}")
        # print(f"[RAG QUERY RECEIVED]")
        # print(f"Patient ID: {patient_id}")
        # print(f"Search Query: {payload.question}")
        # print(f"{'='*80}\n")
        
        # Generate system context if not provided (hidden from frontend)
        if payload.systemContext is None:
            system_context = SystemContext(
                context_mode="rag",
                patient_scope="locked",
                reference_time=datetime.now(timezone.utc).isoformat()
            )
        else:
            system_context = payload.systemContext
        
        # Log sessionId for debugging
        logger.info(f"Processing chat request - sessionId: {payload.sessionId}, patientId: {patient_id}")
        
        answer = await rag.answer_question(
            patient_id, 
            payload.question, 
            payload.conversationHistory,
            system_context,
            session_id=payload.sessionId,
        )
        return ChatResponse(message=answer)
    except Exception as e:
        # Log the error for debugging
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
    """Stream chat response using OpenAI streaming API."""
    
    # Normalize patient ID to ensure consistent format
    patient_id = normalize_patient_id(patient_id)
    
    # Log the incoming search query
    logger = logging.getLogger(__name__)
    logger.info(f"[RAG Query Stream] Patient ID: {patient_id}, Question: {payload.question}")
    
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
        async for chunk in rag.answer_question_stream(
            patient_id, 
            payload.question, 
            payload.conversationHistory,
            system_context,
            session_id=payload.sessionId,
        ):
            yield f"data: {json.dumps({'content': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/{patient_id}/transcribe", response_model=ChatResponse)
async def post_transcribe_audio(
    patient_id: str,
    audio_file: UploadFile = File(...),
    rag: RagService = Depends(get_rag_service),
) -> ChatResponse:
    """Transcribe audio file using Whisper and return the transcription."""
    # Normalize patient ID to ensure consistent format
    patient_id = normalize_patient_id(patient_id)
    
    temp_file_path = None
    try:
        # Validate file was uploaded
        if not audio_file.filename:
            from app.core.errors import APIException
            raise APIException(
                message="No audio file provided. Please upload an audio file.",
                details={}
            )
        
        # Read file content
        content = await audio_file.read()
        if not content or len(content) == 0:
            from app.core.errors import APIException
            raise APIException(
                message="Audio file is empty. Please try recording again.",
                details={}
            )
        
        # Get file extension from original filename, or default to .webm
        file_ext = os.path.splitext(audio_file.filename)[1] if audio_file.filename else ".webm"
        if not file_ext:
            file_ext = ".webm"
        
        # Create a temporary file to save the uploaded audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Transcribe the audio
        transcription = await rag.transcribe_audio(temp_file_path)
        
        # Check for transcription errors
        if transcription.startswith("[Transcription error"):
            from app.core.errors import APIException
            raise APIException(
                message="Failed to transcribe audio. Please try recording again.",
                details={"error": transcription}
            )
        
        if not transcription.strip():
            from app.core.errors import APIException
            raise APIException(
                message="No speech detected in the audio. Please try again.",
                details={}
            )
        
        return ChatResponse(message=transcription)
    except Exception as e:
        # Log the error
        logger = logging.getLogger(__name__)
        logger.error(f"Error transcribing audio for patient {patient_id}: {str(e)}", exc_info=True)
        
        # If it's already an APIException, re-raise it
        from app.core.errors import APIException
        if isinstance(e, APIException):
            raise
        
        # Otherwise, wrap it in an APIException
        raise APIException(
            message=f"Failed to transcribe audio: {str(e)}",
            details={"patient_id": patient_id}
        )
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception:
                pass  # Ignore cleanup errors

