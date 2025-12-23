"""
Retrieval augmented generation service using OpenAI + Supabase.
"""

from __future__ import annotations

import asyncio
from textwrap import dedent
from typing import Iterable, Literal
from datetime import datetime

from openai import AsyncOpenAI

from app.core.config import Settings
from app.models.schemas import ChatMessage, PatientSummary, SpecialtyPerspective, SystemContext
from app.repositories.patient_chunks import PatientChunk, PatientChunkRepository

SYSTEM_PROMPT = dedent(
    """
   You are Radian, a clinical insights assistant supporting physicians.
   You must respond using ONLY the patient data provided in the current context.
    Do not use general medical knowledge or assumptions beyond the supplied data.
 
    Your role is to:
    - Surface observations, trends, patterns, and monitoring-relevant signals
    - Highlight changes over time with dates and values when available
    - Comment on medication adherence or continuity when documented
    - Identify areas that may warrant closer review or follow-up (without clinical judgment)
    
    Strict constraints:
    - Do NOT make diagnoses, differential diagnoses, or treatment recommendations
    - Do NOT use language implying clinical conclusions (e.g., "suggestive of", "indicates", "likely")
    - Do NOT infer missing data
    
    If information is incomplete or unavailable:
    - Explicitly state what data is missing
    - Explain how that limits interpretation
    
    When referencing data:
    - Anchor statements to timeframes (e.g., "over the last 3 months", "most recent value on <date>")
    - Prefer objective sources in this order when available:
    1. Vitals and labs
    2. Medication records
    3. Clinical notes
    4. Patient-reported information
    
    Use clear, clinician-facing language.
    Be concise, factual, and neutral.
    """
).strip()

SUMMARY_PROMPT = dedent(
    """
    You are Radian. Generate a concise, up-to-date patient summary for physician review.
 
    This summary must reflect the available data across the patient record.
    If multiple data points exist, prioritize the latest dated entry for each category.
    
    Format STRICTLY as follows:
    
    HEADLINE:
    Overall Status: <1-line neutral summary of current state based on available data>
    
    KEY POINTS:
    - <Vital sign trends with values and timeframes>
    - <Relevant lab trends with values, dates, and direction of change>
    - <Medication adherence or continuity status>
    - <Notable recent changes or stability compared to prior data>
    - <Items that require monitoring or follow-up review>
    
    Rules:
    - Use bullet points only (no paragraphs)
    - Each bullet must be one concise line
    - Include specific values, dates, and trends when available
    - Do NOT include diagnoses, interpretations, or treatment suggestions
    - Do NOT speculate beyond documented data
    
    If recent data is missing:
    - Explicitly note the absence (e.g., "No lab results recorded in the last 3 months")
    """
).strip()


# SPECIALTY_PROMPT_TEMPLATE = (
#     "You are a {specialty} specialist. Highlight 3 focused observations or monitoring "
#     "considerations related to your specialty. Avoid diagnoses."
# )


class RagService:
    """Coordinates embeddings, retrieval, and OpenAI/OpenRouter completions."""

    def __init__(self, settings: Settings, repository: PatientChunkRepository) -> None:
        self._settings = settings
        self._repo = repository
        # self._client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=settings.openai_timeout_seconds)
                # Use OpenRouter if configured, otherwise use OpenAI
        if settings.use_openrouter and settings.openrouter_api_key:
            self._client = AsyncOpenAI(
                api_key=settings.openrouter_api_key,
                base_url=settings.openrouter_base_url,
                timeout=settings.openai_timeout_seconds,
            )
        else:
            self._client = AsyncOpenAI(
                api_key=settings.openai_api_key,
                timeout=settings.openai_timeout_seconds
            )
        
        # Embeddings always use OpenAI (OpenRouter doesn't support embeddings)
        self._embedding_client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.openai_timeout_seconds
        )

    async def transcribe_audio(self, audio_file_path: str) -> str:
        """Transcribe audio file using OpenAI Whisper API."""
        if not audio_file_path:
            return ""
        
        try:
            with open(audio_file_path, "rb") as audio_file:
                transcription = await self._client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            return (transcription.text or "").strip()
        except Exception as e:
            return f"[Transcription error: {str(e)}]"

    async def generate_patient_summary(
        self, 
        patient_id: str, 
        system_context: SystemContext
    ) -> PatientSummary:
        # Use fewer chunks for summary to speed up processing (8 instead of 12)
        chunk_limit = min(8, self._settings.max_retrieval_chunks)
        chunks = await self._repo.fetch_recent_chunks(patient_id, chunk_limit)
        context = self._format_chunks(chunks)
        
        # Enhance prompt with reference_time
        enhanced_prompt = self._add_temporal_context(SUMMARY_PROMPT, system_context)
        headline, paragraphs = await self._structured_completion(enhanced_prompt, context, system_context)
        return PatientSummary(headline=headline, content=paragraphs)

    async def generate_intro_message(self, patient_id: str) -> str:
        # Hardcoded intro message - return immediately without any async operations
        return "Hello, Doctor. What would you like to know today?"

    # async def generate_specialty_perspectives(self, patient_id: str) -> list[SpecialtyPerspective]:
        # chunks = await self._repo.fetch_recent_chunks(patient_id, self._settings.max_retrieval_chunks)
        # context = self._format_chunks(chunks)

        # async def run_agent(specialty: str) -> SpecialtyPerspective:
            # prompt = SPECIALTY_PROMPT_TEMPLATE.format(specialty=specialty)
            # content = await self._chat_completion(prompt=prompt, context=context)
            # insights = [line.strip("-• ").strip() for line in content.splitlines() if line.strip()]
            # insights = [i for i in insights if i]
            # return SpecialtyPerspective(specialty=specialty, insights=insights[:5])

        # results = await asyncio.gather(*(run_agent(name) for name in self._settings.specialty_agents))
        # return list(results)
    async def generate_specialty_perspectives(self, patient_id: str) -> list[SpecialtyPerspective]:
        return [
            SpecialtyPerspective(
                specialty="Specialty Perspectives",
                insights=["Coming soon"]
            )
        ]

    async def answer_question(
        self, 
        patient_id: str, 
        question: str, 
        history: list[ChatMessage],
        system_context: SystemContext
    ) -> str:
        """Answer a physician's question using RAG."""
        # Use fewer chunks for faster retrieval
        chunk_limit = min(6, self._settings.max_retrieval_chunks)
        
        # Create embedding and search in parallel if possible, but embedding is required first
        embedding = await self._create_embedding(question)
        
        chunks = await self._repo.search_similar_chunks(
            patient_id,
            embedding,
            chunk_limit,
            min_similarity=self._settings.min_similarity_score_chat,  # Use chat-specific threshold
            ivfflat_probes=self._settings.ivfflat_probes,
        )
        
        if not chunks:
            chunks = await self._repo.fetch_recent_chunks(patient_id, chunk_limit)
        
        # Print retrieved chunks to console
        print("\n" + "="*80)
        print(f"QUERY: {question}")
        print(f"RETRIEVED {len(chunks)} CHUNK(S):")
        print("="*80)
        for i, chunk in enumerate(chunks, 1):
            print(f"\n[Chunk {i}]")
            print(f"  Document ID: {chunk.document_id}")
            print(f"  File Name: {chunk.file_name}")
            if chunk.page_number is not None:
                print(f"  Page Number: {chunk.page_number}")
            if chunk.chunk_index is not None:
                print(f"  Chunk Index: {chunk.chunk_index}")
            if chunk.text:
                # Print first 200 characters of the chunk text
                text_preview = chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text
                print(f"  Text Preview: {text_preview}")
            print("-" * 80)
        print("="*80 + "\n")
        
        context = self._format_chunks(chunks)
        
        # Enhance chat prompt with temporal context and formatting instructions
        chat_prompt = self._get_chat_prompt(question)
        enhanced_prompt = self._add_temporal_context(chat_prompt, system_context)
        
        message = await self._chat_completion(
            prompt=enhanced_prompt,
            context=context,
            question=question,
            history=history,
            system_context=system_context,
        )
        return message

    def _get_chat_prompt(self, question: str) -> str:
        """Generate appropriate chat prompt based on question type."""
        question_lower = question.lower()
        
        # Check for summary requests
        if any(keyword in question_lower for keyword in ["summarize", "summary", "6 months", "medical history"]):
            return dedent(
                """
                Answer the physician's question using the patient context provided.
                Extract specific information, values, trends, or observations from the context.
                
                FORMAT YOUR RESPONSE AS FOLLOWS:
                
                🏥 [Title with Emoji] - [Brief descriptive title]
                
                [Section Header]:
                
                [Content organized into clear sections with structured bullet points]
                - Each bullet point should be a concise, informative line
                - Include specific dates, values, and timeframes when available
                - Group related medical conditions or events together
                - Use clear, clinical language
                
                Example format:
                🏥 Summary of Last 6 Months & Top 3 Active Problems
                
                Six-Month Medical History Synopsis:
                
                - [Condition/Event]: [Description with dates and details]
                - [Condition/Event]: [Description with dates and details]
                
                If the information is not in the context, state that clearly.
                Provide factual, concise answers based on the medical records.
                """
            ).strip()
        
        # Check for IFE readings or lab data requests
        if any(keyword in question_lower for keyword in ["ife", "readings", "lab", "table", "trend"]):
            return dedent(
                """
                Answer the physician's question using the patient context provided.
                Extract specific information, values, trends, or observations from the context.
                
                FORMAT YOUR RESPONSE AS FOLLOWS:
                
                📊 [Title with Emoji] - [Brief descriptive title]
                
                Present the data in a MARKDOWN TABLE format. Use appropriate column headers based on the data type.
                
                Example format for IFE readings:
                | Date | Kappa (mg/L) | Lambda (mg/L) | Ratio | Summary |
                |------|--------------|---------------|------|---------|
                | [Date] | [Value] | [Value] | [Value] | [Brief description] |
                
                Include an "Overall trend" summary paragraph below the table describing the pattern or trend observed.
                
                If the information is not in the context, state that clearly.
                Provide factual, concise answers based on the medical records.
                """
            ).strip()
        
        # Check for risk score or calculation requests
        if any(keyword in question_lower for keyword in ["risk", "score", "calculate", "decompensation", "instability"]):
            return dedent(
                """
                Answer the physician's question using the patient context provided.
                Extract specific information, values, trends, or observations from the context.
                
                FORMAT YOUR RESPONSE AS FOLLOWS:
                
                ⚠️ [Title with Emoji] - [Score Name]: [Numeric Value] (on a [scale description], e.g., "0-1 scale").
                
                Top Contributing Clinical Variables:
                
                [Category Name]: [Description of findings and their contribution to risk]
                [Category Name]: [Description of findings and their contribution to risk]
                [Category Name]: [Description of findings and their contribution to risk]
                
                Group variables by category (Vitals, Labs, Medications, etc.).
                Include specific values, trends, and observations when available.
                Explain how each category contributes to the overall risk assessment.
                
                Example format:
                ⚠️ Instability Score: 0.62 (on a 0–1 scale).
                
                Top Contributing Clinical Variables:
                
                Vitals: [Description]
                Labs: [Description]
                Medications: [Description]
                
                If the information is not in the context, state that clearly.
                Provide factual, concise answers based on the medical records.
                """
            ).strip()
        
        # Default formatting for other questions
        return dedent(
            """
            Answer the physician's question using the patient context provided.
            Extract specific information, values, trends, or observations from the context.
            
            FORMAT YOUR RESPONSE AS FOLLOWS:
            
            [Use an appropriate emoji] [Title] - [Brief descriptive title]
            
            [Organize your answer into clear sections with headers if needed]
            - Use bullet points for lists
            - Use tables for structured data
            - Include specific dates, values, and timeframes when available
            
            If the information is not in the context, state that clearly.
            Provide factual, concise answers based on the medical records.
            """
        ).strip()

    def _add_temporal_context(self, prompt: str, system_context: SystemContext) -> str:
        """Add temporal anchoring instructions to prompt."""
        reference_time = datetime.fromisoformat(system_context.reference_time.replace('Z', '+00:00'))
        reference_date = reference_time.strftime("%Y-%m-%d %H:%M:%S UTC")
        
        temporal_instruction = dedent(
            f"""
            TEMPORAL CONTEXT (CRITICAL):
            - Reference time: {reference_date}
            - When using terms like "most recent", "latest", "last", or "recent", 
              these MUST be relative to the reference time above.
            - Do NOT use data points that are newer than the reference time.
            - Always anchor temporal statements to the reference time 
              (e.g., "most recent value as of {reference_date}").
            - If asked about "current" status, interpret this as "as of {reference_date}".
            """
        ).strip()
        
        return f"{prompt}\n\n{temporal_instruction}"

    async def _structured_completion(
        self, 
        prompt: str, 
        context: str,
        system_context: SystemContext
    ) -> tuple[str, list[str]]:
        """Ask the model to return a headline and bullet paragraphs."""
        question = dedent(
            f"""
            Instructions: {prompt}
            Provide the response in the following format:
            HEADLINE: Overall Status: <status summary>
            BULLETS:
            - <bullet point one>
            - <bullet point two>
            - <bullet point three>
            """
        )
        content = await self._chat_completion(
            prompt=question, 
            context=context,
            system_context=system_context
        )
        
        headline = "Overall Status: Clinical Update"
        bullets: list[str] = []
        
        in_bullets_section = False
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            
            if line.upper().startswith("HEADLINE:"):
                headline_text = line.split(":", 1)[1].strip()
                if not headline_text.startswith("Overall Status:"):
                    headline = f"Overall Status: {headline_text}"
                else:
                    headline = headline_text
            elif line.upper().startswith("BULLETS:"):
                in_bullets_section = True
            elif in_bullets_section:
                bullet = line.lstrip("-•*0123456789. ").strip()
                if bullet:
                    bullets.append(bullet)
        
        if not bullets:
            for line in content.splitlines():
                line = line.strip()
                if line and (line.startswith("-") or line.startswith("•") or 
                            (line[0].isdigit() and "." in line[:3])):
                    bullet = line.lstrip("-•*0123456789. ").strip()
                    if bullet:
                        bullets.append(bullet)
        
        if not bullets:
            content_lines = [l.strip() for l in content.splitlines() 
                           if l.strip() and not l.upper().startswith("HEADLINE:")]
            if content_lines:
                bullets = content_lines
            else:
                bullets = [content.strip()]
        
        return headline, bullets

    async def _chat_completion(
        self,
        *,
        prompt: str,
        context: str,
        question: str | None = None,
        history: list[ChatMessage] | None = None,
        system_context: SystemContext,
    ) -> str:
        """Execute an OpenAI ChatCompletion call with shared guardrails."""
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        # Add system context as hidden metadata in system message
        context_metadata = (
            f"\n[System Context: mode={system_context.context_mode}, "
            f"scope={system_context.patient_scope}, "
            f"reference_time={system_context.reference_time}]"
        )
        
        if context and context != "No patient context available.":
            messages.append({
                "role": "system", 
                "content": f"Patient Context:\n{context}{context_metadata}"
            })
        
        messages.append({"role": "system", "content": prompt})
        
        if history:
            for item in history:
                messages.append({"role": item.role, "content": item.content})
        
        if question:
            messages.append({"role": "user", "content": question})

        # Determine max_tokens based on whether this is a chat response (needs more tokens for formatting)
        # or summary (can be shorter)
        is_chat_response = question is not None or history is not None
        max_tokens = 800 if is_chat_response else 400  # More tokens for formatted chat responses
        
        try:
            completion = await self._client.chat.completions.create(
                model=self._settings.openai_model,
                temperature=0.2,
                max_tokens=max_tokens,
                messages=messages,  # type: ignore[arg-type]
            )
        except Exception as e:
            # Provide more helpful error messages
            error_msg = str(e)
            if "model" in error_msg.lower() or "not found" in error_msg.lower():
                provider = "OpenRouter" if self._settings.use_openrouter and self._settings.openrouter_api_key else "OpenAI"
                if provider == "OpenRouter":
                    raise ValueError(
                        f"Invalid OpenRouter model: {self._settings.openai_model}. "
                        f"Please check your model setting. "
                        f"Valid Gemini models include: google/gemini-2.0-flash-exp, google/gemini-pro, google/gemini-1.5-pro, etc."
                    ) from e
                else:
                    raise ValueError(
                        f"Invalid OpenAI model: {self._settings.openai_model}. "
                        f"Please check your OPENAI_MODEL setting. "
                        f"Valid models include: gpt-4o-mini, gpt-4o, gpt-4-turbo, etc."
                    ) from e
            raise
        
        # TODO: Log system_context for audit trail
        # logger.info(f"RAG completion: {system_context.model_dump()}")
        
        return completion.choices[0].message.content or ""

    async def _create_embedding(self, text: str) -> list[float]:
        """Create embeddings using OpenAI (OpenRouter doesn't support embeddings)."""
        try:
            embedding = await self._embedding_client.embeddings.create(
                model=self._settings.openai_embedding_model,
                input=text,
            )
            return embedding.data[0].embedding
        except Exception as e:
            error_msg = str(e)
            if "model" in error_msg.lower() or "not found" in error_msg.lower():
                raise ValueError(
                    f"Invalid OpenAI embedding model: {self._settings.openai_embedding_model}. "
                    f"Please check your embedding model setting."
                ) from e
            raise

    @staticmethod
    def _format_chunks(chunks: Iterable[PatientChunk]) -> str:
        formatted = []
        for chunk in chunks:
            # Skip chunks without text
            if not chunk.text or not chunk.text.strip():
                continue
            prefix = f"Document {chunk.document_id}"
            if chunk.page_number is not None:
                prefix += f" page {chunk.page_number}"
            formatted.append(f"{prefix}:\n{chunk.text}")
        return "\n\n".join(formatted) if formatted else "No patient context available."

