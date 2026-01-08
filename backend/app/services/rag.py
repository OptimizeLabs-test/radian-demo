"""
Retrieval augmented generation service using OpenAI + Supabase.
"""

from __future__ import annotations

import logging
import math
import re
import time
from textwrap import dedent
from typing import AsyncIterator, Iterable, Literal, Optional
from datetime import datetime

from openai import AsyncOpenAI

from app.core.config import Settings
from app.models.schemas import ChatMessage, PatientSummary, SpecialtyPerspective, SystemContext
from app.repositories.patient_chunks import PatientChunk, PatientChunkRepository
from app.repositories.rag_log import RagLogRepository

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
    
    CRITICAL: Data Extraction Requirements:
    - Read through ALL provided document chunks thoroughly and completely
    - Extract ALL numerical values, dates, lab results, measurements, and test values from the context
    - Values may appear in various formats: tables, lists, paragraphs, or structured data
    - When searching for specific dates, be flexible with date formats (e.g., "Nov 21, 2025", "2025-11-21", "November 21, 2025", "11/21/2025", "Sep 25", "September 25")
    - Do NOT state that data is missing until you have carefully examined every chunk for the requested information
    - Report ALL matching values found, not just the first one encountered
    - For queries asking for "last N results", find ALL matching values across all chunks and sort them by date
    
    Strict constraints:
    - Do NOT make diagnoses, differential diagnoses, or treatment recommendations
    - Do NOT use language implying clinical conclusions (e.g., "suggestive of", "indicates", "likely")
    - Do NOT infer missing data - but DO thoroughly extract all data that exists in the context
    
    If information is incomplete or unavailable AFTER thorough examination:
    - Explicitly state what data is missing
    - Explain how that limits interpretation
    
    When referencing data:
    - Anchor statements to timeframes (e.g., "over the last 3 months", "most recent value on <date>")
    - Include exact values, dates, and units when available
    - Prefer objective sources in this order when available:
    1. Vitals and labs
    2. Medication records
    3. Clinical notes
    4. Patient-reported information
    
    Response Formatting (adapt to physician's request):
    - Match the format the physician asks for (e.g., if they ask for bullet points, use bullets; if they ask for a table, use a markdown table)
    - For multiple lab values with dates, consider using a markdown table for clarity
    - Use **bold** to emphasize critical values or out-of-range findings
    - Always include units with numerical values (e.g., "52 mg/dL" not just "52")
    - Use bullet points for lists of observations or trends
    - Use numbered lists only for sequential or chronological information
    
    Use clear, clinician-facing language.
    Be concise, factual, and neutral.
    """
).strip()

SUMMARY_PROMPT = dedent(
    """
    You are Radian. Generate a concise, up-to-date patient summary for physician review.

    This summary must reflect the available data across the patient record.
    
    CRITICAL - DATA RECENCY:
    - For each data type (labs, vitals, medications), find the MOST RECENT value by ACTUAL DATE
    - Sort all values by their test/measurement date, NOT by when they appear in the document
    - If you see "HbA1c on Nov 21, 2025" and "HbA1c on Sep 25, 2025", use November as most recent
    - Search ALL provided chunks thoroughly - recent values may appear anywhere in the context
    - Explicitly state the date for the most recent value of each metric
    
    Format STRICTLY as follows:
    
    HEADLINE:
    Overall Status: <1-line neutral summary of current state based on most recent data>
    
    KEY POINTS:
    - <Vital sign trends with **bold values** and specific dates of most recent readings>
    - <Lab trends with **bold values**, dates, and direction of change - prioritize by recency>
    - <Medication adherence or continuity status>
    - <Notable recent changes or stability compared to prior data>
    - <Items that require monitoring or follow-up review>
    
    Rules:
    - Use bullet points only (no paragraphs)
    - Each bullet must be one concise line
    - Use **bold markdown** for all numerical values and test names (e.g., **HbA1c 6.2%**)
    - Include specific values, dates, and trends when available
    - Always show the MOST RECENT date for each metric mentioned
    - Do NOT include diagnoses, interpretations, or treatment suggestions
    - Do NOT speculate beyond documented data
    
    If recent data is missing:
    - Explicitly note the absence (e.g., "No lab results recorded in the last 3 months")
    - State the date of the last available value if older than 3 months
    """
).strip()



class RagService:
    """Coordinates embeddings, retrieval, and OpenAI/OpenRouter completions."""

    def __init__(self, settings: Settings, repository: PatientChunkRepository, log_repository: RagLogRepository | None = None) -> None:
        self._settings = settings
        self._repo = repository
        self._log_repo = log_repository
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
            # Whisper API only works with OpenAI, not OpenRouter
            # Use embedding_client which is always OpenAI
            with open(audio_file_path, "rb") as audio_file:
                transcription = await self._embedding_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            return (transcription.text or "").strip()
        except Exception as e:
            # Log the actual error for debugging
            logger = logging.getLogger(__name__)
            logger.error(f"Whisper transcription error: {str(e)}", exc_info=True)
            return f"[Transcription error: {str(e)}]"

    async def generate_patient_summary(
        self, 
        patient_id: str, 
        system_context: SystemContext
    ) -> PatientSummary:
        """
        Generate a patient summary using hybrid retrieval:
        1. Fetch recent chunks by ingestion time (gets latest documents)
        2. Also search for key medical terms to ensure we don't miss recent lab values
        3. Combine and deduplicate
        """
        # Use configurable chunk limit for summaries
        chunk_limit = self._settings.max_retrieval_chunks_summary
        
        # Get recent chunks by ingestion time
        recent_chunks = await self._repo.fetch_recent_chunks(patient_id, chunk_limit)
        
        # Reduced keyword search for speed - only search top 2 critical terms
        # (hba1c and glucose cover most diabetes monitoring needs)
        critical_terms = ["hba1c", "glucose"]
        keyword_chunks = []
        for term in critical_terms:
            term_chunks = await self._repo.search_chunks_by_keyword(patient_id, term, limit=1)
            keyword_chunks.extend(term_chunks)
        
        # Combine and deduplicate by chunk_id
        chunk_ids_seen = {chunk.chunk_id for chunk in recent_chunks}
        for chunk in keyword_chunks:
            if chunk.chunk_id not in chunk_ids_seen:
                recent_chunks.append(chunk)
                chunk_ids_seen.add(chunk.chunk_id)
        
        # Limit to reasonable size - keep it tight for speed
        chunks = recent_chunks[:chunk_limit + 2]  # Just a couple extra for critical labs
        
        context = self._format_chunks(chunks)
        
        # Enhance prompt with reference_time
        enhanced_prompt = self._add_temporal_context(SUMMARY_PROMPT, system_context)
        headline, paragraphs = await self._structured_completion(enhanced_prompt, context, system_context)
        return PatientSummary(headline=headline, content=paragraphs)

    async def generate_intro_message(self, patient_id: str) -> str:
        # Hardcoded intro message - return immediately without any async operations
        return "Hello, Doctor. What would you like to know today?"

    async def generate_specialty_perspectives(self, patient_id: str) -> list[SpecialtyPerspective]:
        return [
            SpecialtyPerspective(
                specialty="Specialty Perspectives",
                insights=["Coming soon"]
            )
        ]

    def _extract_lab_keywords(self, question: str) -> list[str]:
        """
        Extract lab/test keywords from the question for hybrid search.
        Looks for common lab names and test terms.
        """
        question_lower = question.lower()
        keywords = []
        
        # Common lab names and terms to search for
        lab_patterns = [
            r'\btriglyceride[s]?\b',
            r'\bcholesterol\b',
            r'\bglucose\b',
            r'\bhba1c\b',
            r'\bhpa1c\b',  # Common misspelling/variant
            r'\ba1c\b',  # Shorthand for HbA1c
            r'\bhemoglobin a1c\b',
            r'\bcreatinine\b',
            r'\bhemoglobin\b',
            r'\bplatelet[s]?\b',
            r'\bwbc\b',
            r'\brbc\b',
            r'\blipid[s]?\b',
            r'\bldl\b',
            r'\bhdl\b',
            r'\bbp\b',
            r'\bblood pressure\b',
            r'\bbmi\b',
            r'\bweight\b',
            r'\bheight\b',
            r'\bbun\b',  # Blood Urea Nitrogen
            r'\begfr\b',  # Estimated Glomerular Filtration Rate
            r'\bpotassium\b',
            r'\bsodium\b',
            r'\bcalcium\b',
        ]
        
        for pattern in lab_patterns:
            match = re.search(pattern, question_lower)
            if match:
                keyword = match.group(0).strip()
                # Handle plural/singular - add both forms for better matching
                if keyword.endswith('s') and len(keyword) > 3:
                    keywords.append(keyword[:-1])  # Add singular form
                keywords.append(keyword)
        
        return list(set(keywords))  # Remove duplicates
    
    def _needs_hybrid_search(self, question: str) -> bool:
        """
        Determine if a query would benefit from hybrid search.
        Queries asking for multiple results or "all" results need hybrid search.
        """
        question_lower = question.lower()
        patterns = [
            r'\blast\s+\d+',  # "last 5", "last 10"
            r'\b(all|every|each)\s+',  # "all results", "every test"
            r'\bhow many',  # "how many results"
            r'\blist\s+',  # "list all"
        ]
        return any(re.search(pattern, question_lower) for pattern in patterns)
    
    def _calculate_keyword_score(self, chunk: PatientChunk, question: str) -> float:
        """
        Calculate keyword matching score between chunk text and question.
        Returns a score between 0 and 1.
        """
        if not chunk.text:
            return 0.0
        
        question_lower = question.lower()
        chunk_text_lower = chunk.text.lower()
        
        # Extract keywords from question (remove common stop words)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'what', 'when', 'where', 'how', 
        'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
        
        question_words = [w for w in re.findall(r'\b\w+\b', question_lower) if w not in stop_words and len(w) > 2]
        
        if not question_words:
            return 0.0
        
        # Count matches
        matches = sum(1 for word in question_words if word in chunk_text_lower)
        
        # Calculate score: proportion of question keywords found, with bonus for multiple occurrences
        base_score = matches / len(question_words)
        
        # Bonus for multiple occurrences of keywords
        total_occurrences = sum(chunk_text_lower.count(word) for word in question_words)
        occurrence_bonus = min(0.3, (total_occurrences - matches) * 0.1)
        
        return min(1.0, base_score + occurrence_bonus)
    
    def _calculate_recency_score(self, chunks: list[PatientChunk], chunk: PatientChunk) -> float:
        """
        Calculate recency score based on position in the list.
        Assumes chunks are ordered by recency (most recent first).
        Returns a score between 0 and 1.
        """
        try:
            index = chunks.index(chunk)
            # Normalize: most recent chunk gets 1.0, least recent gets close to 0
            # Use exponential decay for better differentiation
            max_index = len(chunks) - 1
            if max_index == 0:
                return 1.0
            # Exponential decay: score = e^(-index / max_index * 2)
            # This gives more weight to recent chunks
            score = math.exp(-index / max_index * 2)
            return max(0.1, score)  # Ensure minimum score of 0.1
        except ValueError:
            return 0.5  # Default score if chunk not found
    
    def _rerank_chunks(
        self, 
        chunks: list[PatientChunk], 
        question: str,
        top_k: int
    ) -> list[PatientChunk]:
        """
        Re-rank chunks using a hybrid scoring approach.
        
        Combines:
        - Semantic similarity (from vector search)
        - Keyword matching score
        - Recency score
        
        Returns top-K chunks after re-ranking.
        """
        if not chunks or not self._settings.rerank_enabled:
            return chunks[:top_k] if chunks else []
        
        # If we have fewer chunks than top_k, return all
        if len(chunks) <= top_k:
            return chunks
        
        # Calculate composite scores for each chunk
        scored_chunks = []
        for chunk in chunks:
            # Normalize similarity score (assume it's already between 0 and 1)
            similarity_score = chunk.similarity if chunk.similarity is not None else 0.0
            similarity_score = max(0.0, min(1.0, similarity_score))  # Clamp to [0, 1]
            
            # Calculate keyword score
            keyword_score = self._calculate_keyword_score(chunk, question)
            
            # Calculate recency score (based on original position)
            recency_score = self._calculate_recency_score(chunks, chunk)
            
            # If chunk has no similarity score (from keyword search), boost keyword weight
            # and use keyword score as a proxy for similarity
            if chunk.similarity is None:
                # For chunks without similarity, rely more on keyword matching
                # Use keyword score as a proxy for semantic relevance
                adjusted_similarity = keyword_score * 0.8  # Scale keyword score to approximate similarity
                composite_score = (
                    self._settings.rerank_similarity_weight * adjusted_similarity +
                    self._settings.rerank_keyword_weight * keyword_score +
                    self._settings.rerank_recency_weight * recency_score
                )
            else:
                # Standard weighted composite score for chunks with similarity
                composite_score = (
                    self._settings.rerank_similarity_weight * similarity_score +
                    self._settings.rerank_keyword_weight * keyword_score +
                    self._settings.rerank_recency_weight * recency_score
                )
            
            scored_chunks.append((composite_score, chunk))
        
        # Sort by composite score (descending) and return top-K
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        reranked_chunks = [chunk for _, chunk in scored_chunks[:top_k]]
        
        # Log re-ranking results for debugging
        logger = logging.getLogger(__name__)
        logger.debug(
            f"Re-ranked {len(chunks)} chunks to top {len(reranked_chunks)}. "
            f"Top 3 scores: {[f'{score:.3f}' for score, _ in scored_chunks[:3]]}"
        )
        
        return reranked_chunks

    async def answer_question(
        self, 
        patient_id: str, 
        question: str, 
        history: list[ChatMessage],
        system_context: SystemContext,
        session_id: str | None = None,
    ) -> str:
        """Answer a physician's question using RAG."""
        # Start timing for latency measurement
        start_time = time.perf_counter()
        
        question_lower = question.lower()
        
        # Extract "last N" pattern once and reuse throughout
        last_n_match = re.search(r'last\s+(\d+)', question_lower)
        last_n_count = int(last_n_match.group(1)) if last_n_match else None
        
        # Detect if query asks for comprehensive/exhaustive results
        asks_for_all = any(term in question_lower for term in ['all', 'every', 'complete', 'full'])
        needs_comprehensive_retrieval = last_n_count is not None  # Any "last N" query needs comprehensive retrieval
        
        # Adjust chunk limits dynamically based on query intent
        if asks_for_all or needs_comprehensive_retrieval:
            # Comprehensive query: retrieve more chunks
            chunk_limit = 25  # Increased from default for exhaustive searches
            retrieval_limit = 100 if self._settings.rerank_enabled else chunk_limit
            min_sim = 0.15  # Lower threshold
        else:
            # Normal query: use standard limits
            chunk_limit = self._settings.max_retrieval_chunks_chat
            retrieval_limit = self._settings.rerank_top_n if self._settings.rerank_enabled else chunk_limit
            min_sim = self._settings.min_similarity_score_chat
        
        # Create embedding and search in parallel if possible, but embedding is required first
        embedding = await self._create_embedding(question)
        
        # Start with semantic search - retrieve top-N chunks for re-ranking
        chunks = await self._repo.search_similar_chunks(
            patient_id,
            embedding,
            retrieval_limit,  # Retrieve more chunks for re-ranking
            min_similarity=min_sim,  # Use dynamic threshold based on query type
            ivfflat_probes=self._settings.ivfflat_probes,
        )
        
        # For queries asking for multiple results, supplement with keyword search
        if self._needs_hybrid_search(question):
            lab_keywords = self._extract_lab_keywords(question)
            if lab_keywords:
                # Use the most relevant keyword (usually the first/longest one)
                primary_keyword = max(lab_keywords, key=len)
                # Retrieve more chunks via keyword search (2x limit for comprehensive coverage)
                keyword_chunks = await self._repo.search_chunks_by_keyword(
                    patient_id,
                    primary_keyword,
                    chunk_limit * 2,  # Get more chunks from keyword search
                )
                
                # Combine and deduplicate by chunk_id
                chunk_ids_seen = {chunk.chunk_id for chunk in chunks}
                for chunk in keyword_chunks:
                    if chunk.chunk_id not in chunk_ids_seen:
                        chunks.append(chunk)
                        chunk_ids_seen.add(chunk.chunk_id)
                
                # Also fetch related chunks from the same documents that contain the keyword
                # This helps when dates/headers are in one chunk and values in another
                document_ids = list(set(chunk.document_id for chunk in keyword_chunks))
                if document_ids:
                    related_chunks = await self._repo.fetch_chunks_by_documents(
                        patient_id,
                        document_ids,
                        limit_per_document=5,  # Get up to 5 chunks per document
                    )
                    
                    # Add related chunks that aren't already included
                    for chunk in related_chunks:
                        if chunk.chunk_id not in chunk_ids_seen:
                            chunks.append(chunk)
                            chunk_ids_seen.add(chunk.chunk_id)
                
                # Limit total chunks to avoid context overflow (but allow more for comprehensive queries)
                if len(chunks) > retrieval_limit * 2:
                    chunks = chunks[:retrieval_limit * 2]
        
        if not chunks:
            chunks = await self._repo.fetch_recent_chunks(patient_id, retrieval_limit)
        
        # Apply re-ranking if enabled
        if self._settings.rerank_enabled and chunks:
            chunks = self._rerank_chunks(chunks, question, top_k=chunk_limit)
        
        # Print retrieved chunks to console
        # print("\n" + "="*80)
        # print(f"QUERY: {question}")
        # print(f"RETRIEVED {len(chunks)} CHUNK(S):")
        # print("="*80)
        # for i, chunk in enumerate(chunks, 1):
        #     print(f"\n[Chunk {i}]")
        #     print(f"  Document ID: {chunk.document_id}")
        #     print(f"  File Name: {chunk.file_name}")
        #     if chunk.page_number is not None:
        #         print(f"  Page Number: {chunk.page_number}")
        #     if chunk.chunk_index is not None:
        #         print(f"  Chunk Index: {chunk.chunk_index}")
        #     if chunk.text:
        #         # Print first 200 characters of the chunk text
        #         text_preview = chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text
        #         print(f"  Text Preview: {text_preview}")
        #     print("-" * 80)
        # print("="*80 + "\n")
        
        context = self._format_chunks(chunks)
        
        # Enhance chat prompt with temporal context and formatting instructions
        chat_prompt = self._get_chat_prompt(question, last_n_match, last_n_count)
        enhanced_prompt = self._add_temporal_context(chat_prompt, system_context)
        
        message = await self._chat_completion(
            prompt=enhanced_prompt,
            context=context,
            question=question,
            history=history,
            system_context=system_context,
        )
        
        # Calculate latency (time taken to process the query)
        latency = time.perf_counter() - start_time
        
        # Log the RAG query if logging is enabled
        logger = logging.getLogger(__name__)
        if not self._log_repo:
            logger.warning("RAG log repository not initialized - skipping logging")
        else:
            # Generate session_id if not provided (fallback for logging)
            if not session_id:
                import uuid
                session_id = f"auto-{uuid.uuid4().hex[:12]}"
                logger.info(f"Generated session_id for logging: {session_id}")
            
            try:
                logger.info(f"Logging RAG query: session_id={session_id}, patient_id={patient_id}, latency={latency:.2f}s")
                chunks_for_log = self._format_chunks_for_logging(chunks)
                await self._log_repo.log_rag_query(
                    session_id=session_id,
                    patient_id=patient_id,
                    user_query=question,
                    response=message,
                    chunks_extracted=chunks_for_log,
                    latency=latency,
                )
                logger.info(f"Successfully logged RAG query for session {session_id}")
            except Exception as e:
                # Don't fail the request if logging fails
                logger.error(f"Failed to log RAG query: {str(e)}", exc_info=True)
        
        return message

    def _get_chat_prompt(
        self, 
        question: str,
        last_n_match: Optional[re.Match] = None,
        last_n_count: Optional[int] = None
    ) -> str:
        """Generate appropriate chat prompt based on question type."""
        question_lower = question.lower()
        
        # Check for summary requests
        # if any(keyword in question_lower for keyword in ["summarize", "summary", "6 months", "medical history"]):
        #     return dedent(
        #         """
        #         Answer the physician's question using the patient context provided.
        #         Extract specific information, values, trends, or observations from the context.
                
        #         FORMAT YOUR RESPONSE AS FOLLOWS:
                
        #         🏥 [Title with Emoji] - [Brief descriptive title]
                
        #         [Section Header]:
                
        #         [Content organized into clear sections with structured bullet points]
        #         - Each bullet point should be a concise, informative line
        #         - Include specific dates, values, and timeframes when available
        #         - Group related medical conditions or events together
        #         - Use clear, clinical language
                
        #         Example format:
        #         🏥 Summary of Last 6 Months & Top 3 Active Problems
                
        #         Six-Month Medical History Synopsis:
                
        #         - [Condition/Event]: [Description with dates and details]
        #         - [Condition/Event]: [Description with dates and details]
                
        #         If the information is not in the context, state that clearly.
        #         Provide factual, concise answers based on the medical records.
        #         """
        #     ).strip()
        
        # # Check for IFE readings or lab data requests
        # if any(keyword in question_lower for keyword in ["ife", "readings", "lab", "table", "trend"]):
        #     return dedent(
        #         """
        #         Answer the physician's question using the patient context provided.
        #         Extract specific information, values, trends, or observations from the context.
                
        #         FORMAT YOUR RESPONSE AS FOLLOWS:
                
        #         📊 [Title with Emoji] - [Brief descriptive title]
                
        #         Present the data in a MARKDOWN TABLE format. Use appropriate column headers based on the data type.
                
        #         Example format for IFE readings:
        #         | Date | Kappa (mg/L) | Lambda (mg/L) | Ratio | Summary |
        #         |------|--------------|---------------|------|---------|
        #         | [Date] | [Value] | [Value] | [Value] | [Brief description] |
                
        #         Include an "Overall trend" summary paragraph below the table describing the pattern or trend observed.
                
        #         If the information is not in the context, state that clearly.
        #         Provide factual, concise answers based on the medical records.
        #         """
        #     ).strip()
        
        # # Check for risk score or calculation requests
        # if any(keyword in question_lower for keyword in ["risk", "score", "calculate", "decompensation", "instability"]):
        #     return dedent(
        #         """
        #         Answer the physician's question using the patient context provided.
        #         Extract specific information, values, trends, or observations from the context.
                
        #         FORMAT YOUR RESPONSE AS FOLLOWS:
                
        #         ⚠️ [Title with Emoji] - [Score Name]: [Numeric Value] (on a [scale description], e.g., "0-1 scale").
                
        #         Top Contributing Clinical Variables:
                
        #         [Category Name]: [Description of findings and their contribution to risk]
        #         [Category Name]: [Description of findings and their contribution to risk]
        #         [Category Name]: [Description of findings and their contribution to risk]
                
        #         Group variables by category (Vitals, Labs, Medications, etc.).
        #         Include specific values, trends, and observations when available.
        #         Explain how each category contributes to the overall risk assessment.
                
        #         Example format:
        #         ⚠️ Instability Score: 0.62 (on a 0–1 scale).
                
        #         Top Contributing Clinical Variables:
                
        #         Vitals: [Description]
        #         Labs: [Description]
        #         Medications: [Description]
                
        #         If the information is not in the context, state that clearly.
        #         Provide factual, concise answers based on the medical records.
        #         """
        #     ).strip()
        
        # Default formatting for other questions
        # return dedent(
        #     """
        #     Answer the physician's question using the patient context provided.
        #     Extract specific information, values, trends, or observations from the context.
            
        #     FORMAT YOUR RESPONSE AS FOLLOWS:
            
        #     [Use an appropriate emoji] [Title] - [Brief descriptive title]
            
        #     [Organize your answer into clear sections with headers if needed]
        #     - Use bullet points for lists
        #     - Use tables for structured data
        #     - Include specific dates, values, and timeframes when available
            
        #     If the information is not in the context, state that clearly.
        #     Provide factual, concise answers based on the medical records.
        #     """
        # ).strip()
        # Detect explicit format requests
        asks_for_table = 'table' in question_lower or 'tabular' in question_lower
        asks_for_bullets = 'bullet' in question_lower or 'list' in question_lower
        asks_for_sentence = 'brief' in question_lower or 'sentence' in question_lower or 'summary' in question_lower
        
        # Detect multi-value queries (multiple lab values, histories, trends)
        is_multi_value_query = bool(re.search(r'\blast\s+\d+', question_lower)) or \
                               any(term in question_lower for term in ['all', 'history', 'trend', 'over time', 'multiple', 'several'])
        
        # Build base prompt
        base_prompt = dedent(
            """
            Answer the physician's question using the patient context provided.
            
            CRITICAL INSTRUCTIONS FOR DATA EXTRACTION:
            - Carefully read through ALL provided document chunks completely and thoroughly
            - Extract ALL numerical values, dates, lab results, and measurements from the context
            - Look for values even if they appear in tables, lists, paragraphs, or various formats
            - Values may appear in different chunks than their associated dates - search across ALL chunks
            - When a date is mentioned, search ALL chunks for the corresponding numerical value, even if it's not in the same chunk as the date
            - When searching for specific dates, check all date formats (e.g., "Nov 21, 2025", "2025-11-21", "November 21, 2025", "11/21/2025", "Sep 25", "September 25")
            - Do NOT assume data is missing - thoroughly examine every chunk before concluding information is unavailable
            - If multiple values exist for the same metric, extract and report ALL of them, sorted by date (most recent first)
            - For queries asking for "last N results", find ALL matching values across all chunks and sort them by date
            
            IMPORTANT: When chunks contain dates but no values, the values may be in adjacent chunks from the same document. 
            Always check all chunks from documents that contain relevant dates or keywords.
            
            Provide factual, concise answers based on the medical records.
            Include specific values, dates, and measurements when available in the context.
            If the information is truly not in the context after thorough examination, state that clearly.
            Use clear, clinical language.
            Be concise, factual, and neutral.
            """
        ).strip()
        
        # Add smart formatting hint based on query intent
        formatting_hint = ""
        
        if asks_for_table:
            # Explicit request for table
            formatting_hint = "\n\nFORMAT: Use a markdown table as requested."
        elif asks_for_bullets:
            # Explicit request for bullets
            formatting_hint = "\n\nFORMAT: Use bullet points as requested."
        elif asks_for_sentence:
            # Explicit request for brief/sentence format
            formatting_hint = "\n\nFORMAT: Provide a concise response in sentence form as requested."
        elif is_multi_value_query and any(term in question_lower for term in [
            'lab', 'lipid', 'cholesterol', 'glucose', 'hemoglobin', 'creatinine',
            'triglyceride', 'hdl', 'ldl', 'vitals', 'blood pressure', 'results',
            'hba1c', 'hpa1c', 'a1c', 'hemoglobin a1c',  # Diabetes monitoring
            'bun', 'egfr', 'potassium', 'sodium', 'calcium'  # Electrolytes/kidney
        ]):
            # Multiple lab values - suggest table for clarity, but don't force it
            formatting_hint = dedent("""
                
                FORMATTING SUGGESTION: If you find multiple lab values with dates, consider presenting them in a markdown table format for clarity:
                | Test | Value | Date | Reference Range |
                
                However, use your judgment based on the number of values and what would be clearest for the physician.
            """).strip()
        
        # Add exhaustive search instruction ONLY for "all/every/complete/full" queries
        # Do NOT add for "last N" queries as they have their own specific instructions below
        if any(term in question_lower for term in ['all', 'every', 'complete', 'full']) and not last_n_match:
            formatting_hint += dedent("""
                
                CRITICAL - EXHAUSTIVE SEARCH MODE:
                The physician is requesting a comprehensive list. You MUST:
                - Review EVERY SINGLE chunk provided, even if it seems less relevant
                - Extract ALL matching values, dates, and results from ALL chunks
                - Do NOT stop after finding a few results - continue searching ALL chunks
                - Report the TOTAL count of results found
                - If you find fewer than expected, explicitly state "searched N chunks, found M results"
            """).strip()
        
        # Add specific instruction for "last N" queries (using already-extracted match from parameter)
        if last_n_match and last_n_count:
            formatting_hint += dedent(f"""
                
                CRITICAL - "LAST {last_n_count}" QUERY INSTRUCTIONS:
                The physician is asking for the {last_n_count} MOST RECENT results sorted by date.
                
                MANDATORY PROCESS:
                1. Extract ALL matching results from ALL provided chunks (ignore semantic relevance)
                2. Create a list of (date, value) pairs for EVERY result found
                3. Sort this ENTIRE list by date in DESCENDING order (newest first)
                4. Take ONLY the first {last_n_count} items from the sorted list
                5. Present these {last_n_count} results with the most recent at the top
                
                EXAMPLE for "last 3 glucose readings":
                - Found: Jan 15 (120), Dec 10 (115), Nov 5 (110), Oct 1 (105), Sep 20 (100)
                - Sorted: Jan 15, Dec 10, Nov 5, Oct 1, Sep 20
                - Return: ONLY Jan 15 (120), Dec 10 (115), Nov 5 (110)  [First 3 after sorting]
                
                VERIFICATION BEFORE RESPONDING:
                - Count how many results you extracted total (e.g., "Found 15 total results")
                - If found < {last_n_count}, state: "Found only X results (requested {last_n_count})"
                - If found >= {last_n_count}, confirm: "Sorted all results and selected top {last_n_count}"
                - Check the date range of your final {last_n_count} results
                
                CRITICAL: Do NOT return more than {last_n_count} results, even if you found more!
            """).strip()
        
        return base_prompt + formatting_hint

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
        max_tokens = 1000 if is_chat_response else 450  # Increased from 300 to prevent truncation while staying faster
        
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

    async def _chat_completion_stream(
        self,
        *,
        prompt: str,
        context: str,
        question: str | None = None,
        history: list[ChatMessage] | None = None,
        system_context: SystemContext,
    ) -> AsyncIterator[str]:
        """Execute a streaming OpenAI ChatCompletion call."""
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
        max_tokens = 1000 if is_chat_response else 450  # Increased from 300 to prevent truncation while staying faster
        
        try:
            stream = await self._client.chat.completions.create(
                model=self._settings.openai_model,
                temperature=0.2,
                max_tokens=max_tokens,
                messages=messages,  # type: ignore[arg-type]
                stream=True,
            )
            
            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        yield delta.content
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

    async def generate_patient_summary_stream(
        self, 
        patient_id: str, 
        system_context: SystemContext
    ) -> AsyncIterator[str]:
        """Stream patient summary as it's generated with hybrid retrieval."""
        # Use configurable chunk limit for summaries
        chunk_limit = self._settings.max_retrieval_chunks_summary
        
        # Get recent chunks by ingestion time
        recent_chunks = await self._repo.fetch_recent_chunks(patient_id, chunk_limit)
        
        # Reduced keyword search for speed - only search top 2 critical terms
        # (hba1c and glucose cover most diabetes monitoring needs)
        critical_terms = ["hba1c", "glucose"]
        keyword_chunks = []
        for term in critical_terms:
            term_chunks = await self._repo.search_chunks_by_keyword(patient_id, term, limit=1)
            keyword_chunks.extend(term_chunks)
        
        # Combine and deduplicate by chunk_id
        chunk_ids_seen = {chunk.chunk_id for chunk in recent_chunks}
        for chunk in keyword_chunks:
            if chunk.chunk_id not in chunk_ids_seen:
                recent_chunks.append(chunk)
                chunk_ids_seen.add(chunk.chunk_id)
        
        # Limit to reasonable size - keep it tight for speed
        chunks = recent_chunks[:chunk_limit + 2]  # Just a couple extra for critical labs
        
        context = self._format_chunks(chunks)
        
        # Enhance prompt with reference_time
        enhanced_prompt = self._add_temporal_context(SUMMARY_PROMPT, system_context)
        question = dedent(
            f"""
            Instructions: {enhanced_prompt}
            Provide the response in the following format:
            HEADLINE: Overall Status: <status summary>
            BULLETS:
            - <bullet point one>
            - <bullet point two>
            - <bullet point three>
            """
        )
        
        async for chunk in self._chat_completion_stream(
            prompt=question,
            context=context,
            system_context=system_context
        ):
            yield chunk

    async def answer_question_stream(
        self, 
        patient_id: str, 
        question: str, 
        history: list[ChatMessage],
        system_context: SystemContext,
        session_id: str | None = None,
    ) -> AsyncIterator[str]:
        """Stream answer to a physician's question using RAG."""
        # Start timing for latency measurement
        start_time = time.perf_counter()
        
        question_lower = question.lower()
        
        # Extract "last N" pattern once and reuse throughout
        last_n_match = re.search(r'last\s+(\d+)', question_lower)
        last_n_count = int(last_n_match.group(1)) if last_n_match else None
        
        # Detect if query asks for comprehensive/exhaustive results
        asks_for_all = any(term in question_lower for term in ['all', 'every', 'complete', 'full'])
        needs_comprehensive_retrieval = last_n_count is not None  # Any "last N" query needs comprehensive retrieval
        
        # Adjust chunk limits dynamically based on query intent
        if asks_for_all or needs_comprehensive_retrieval:
            # Comprehensive query: retrieve more chunks
            chunk_limit = 25  # Increased from default for exhaustive searches
            retrieval_limit = 100 if self._settings.rerank_enabled else chunk_limit
            min_sim = 0.15  # Lower threshold
        else:
            # Normal query: use standard limits
            chunk_limit = self._settings.max_retrieval_chunks_chat
            retrieval_limit = self._settings.rerank_top_n if self._settings.rerank_enabled else chunk_limit
            min_sim = self._settings.min_similarity_score_chat
        
        # Create embedding and search
        embedding = await self._create_embedding(question)
        
        # Start with semantic search - retrieve top-N chunks for re-ranking
        chunks = await self._repo.search_similar_chunks(
            patient_id,
            embedding,
            retrieval_limit,  # Retrieve more chunks for re-ranking
            min_similarity=min_sim,  # Use dynamic threshold based on query type
            ivfflat_probes=self._settings.ivfflat_probes,
        )
        
        # For queries asking for multiple results, supplement with keyword search
        if self._needs_hybrid_search(question):
            lab_keywords = self._extract_lab_keywords(question)
            if lab_keywords:
                primary_keyword = max(lab_keywords, key=len)
                keyword_chunks = await self._repo.search_chunks_by_keyword(
                    patient_id,
                    primary_keyword,
                    chunk_limit * 2,
                )
                
                chunk_ids_seen = {chunk.chunk_id for chunk in chunks}
                for chunk in keyword_chunks:
                    if chunk.chunk_id not in chunk_ids_seen:
                        chunks.append(chunk)
                        chunk_ids_seen.add(chunk.chunk_id)
                
                document_ids = list(set(chunk.document_id for chunk in keyword_chunks))
                if document_ids:
                    related_chunks = await self._repo.fetch_chunks_by_documents(
                        patient_id,
                        document_ids,
                        limit_per_document=5,
                    )
                    
                    for chunk in related_chunks:
                        if chunk.chunk_id not in chunk_ids_seen:
                            chunks.append(chunk)
                            chunk_ids_seen.add(chunk.chunk_id)
                
                if len(chunks) > retrieval_limit * 2:
                    chunks = chunks[:retrieval_limit * 2]
        
        if not chunks:
            chunks = await self._repo.fetch_recent_chunks(patient_id, retrieval_limit)
        
        # Apply re-ranking if enabled
        if self._settings.rerank_enabled and chunks:
            chunks = self._rerank_chunks(chunks, question, top_k=chunk_limit)
        
        context = self._format_chunks(chunks)
        
        # Enhance chat prompt with temporal context and formatting instructions
        chat_prompt = self._get_chat_prompt(question, last_n_match, last_n_count)
        enhanced_prompt = self._add_temporal_context(chat_prompt, system_context)
        
        # Stream the response and collect it for logging
        full_response = ""
        async for chunk in self._chat_completion_stream(
            prompt=enhanced_prompt,
            context=context,
            question=question,
            history=history,
            system_context=system_context,
        ):
            full_response += chunk
            yield chunk
        
        # Calculate latency and log after streaming completes
        latency = time.perf_counter() - start_time
        
        # Log the RAG query if logging is enabled
        logger = logging.getLogger(__name__)
        if not self._log_repo:
            logger.warning("RAG log repository not initialized - skipping logging")
        else:
            # Generate session_id if not provided (fallback for logging)
            if not session_id:
                import uuid
                session_id = f"auto-{uuid.uuid4().hex[:12]}"
                logger.info(f"Generated session_id for logging: {session_id}")
            
            try:
                logger.info(f"Logging RAG query (stream): session_id={session_id}, patient_id={patient_id}, latency={latency:.2f}s")
                chunks_for_log = self._format_chunks_for_logging(chunks)
                await self._log_repo.log_rag_query(
                    session_id=session_id,
                    patient_id=patient_id,
                    user_query=question,
                    response=full_response,
                    chunks_extracted=chunks_for_log,
                    latency=latency,
                )
                logger.info(f"Successfully logged RAG query (stream) for session {session_id}")
            except Exception as e:
                # Don't fail the request if logging fails
                logger.error(f"Failed to log RAG query (stream): {str(e)}", exc_info=True)

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
            # Use file_name if available, otherwise fall back to document_id
            if chunk.file_name:
                # Clean up the file name (remove path, extension if needed)
                doc_name = chunk.file_name
                # Remove common file extensions for cleaner display
                if doc_name.endswith(('.pdf', '.txt', '.doc', '.docx')):
                    doc_name = doc_name.rsplit('.', 1)[0]
                prefix = f"Document: {doc_name}"
            else:
                prefix = f"Document: {chunk.document_id}"
            if chunk.page_number is not None:
                prefix += f" (page {chunk.page_number})"
            formatted.append(f"{prefix}:\n{chunk.text}")
        return "\n\n".join(formatted) if formatted else "No patient context available."

    @staticmethod
    def _format_chunks_for_logging(chunks: Iterable[PatientChunk]) -> str:
        """
        Format chunks for logging with "----" separator between chunks.
        This format is stored in the database for easy parsing.
        """
        formatted_chunks = []
        for chunk in chunks:
            if not chunk.text or not chunk.text.strip():
                continue
            
            # Build chunk metadata
            chunk_info = []
            if chunk.file_name:
                doc_name = chunk.file_name
                if doc_name.endswith(('.pdf', '.txt', '.doc', '.docx')):
                    doc_name = doc_name.rsplit('.', 1)[0]
                chunk_info.append(f"Document: {doc_name}")
            else:
                chunk_info.append(f"Document ID: {chunk.document_id}")
            
            if chunk.page_number is not None:
                chunk_info.append(f"Page: {chunk.page_number}")
            if chunk.chunk_index is not None:
                chunk_info.append(f"Chunk Index: {chunk.chunk_index}")
            if chunk.similarity is not None:
                chunk_info.append(f"Similarity: {chunk.similarity:.4f}")
            
            # Format: metadata + text, separated by "----" between chunks
            chunk_str = "\n".join(chunk_info) + "\n" + chunk.text
            formatted_chunks.append(chunk_str)
        
        # Join chunks with "----" separator
        return "\n----\n".join(formatted_chunks) if formatted_chunks else "No chunks retrieved"

