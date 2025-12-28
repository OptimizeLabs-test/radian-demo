"""
Data-access layer for the RAG_log table.
"""

from datetime import datetime
import asyncpg
import logging

logger = logging.getLogger(__name__)


class RagLogRepository:
    """Repository responsible for logging RAG queries and responses."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    @classmethod
    async def create(cls, database_url: str, *, min_size: int, max_size: int) -> "RagLogRepository":
        pool = await asyncpg.create_pool(dsn=database_url, min_size=min_size, max_size=max_size)
        return cls(pool)

    async def close(self) -> None:
        await self._pool.close()

    async def log_rag_query(
        self,
        session_id: str,
        patient_id: str,
        user_query: str,
        response: str,
        chunks_extracted: str,
        timestamp: datetime | None = None,
        latency: float | None = None,
    ) -> None:
        """
        Log a RAG query with all relevant information.
        
        Args:
            session_id: Unique session identifier
            patient_id: Patient identifier
            user_query: The user's question/query
            response: The generated response
            chunks_extracted: All retrieved chunks separated by "----" delimiter
            timestamp: Optional timestamp (defaults to now)
            latency: Optional latency in seconds (time taken to process the query)
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        query = """
        INSERT INTO rag_log (session_id, patient_id, user_query, response, chunks_extracted, timestamp, latency)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """
        
        try:
            async with self._pool.acquire() as connection:
                # First, verify the table exists
                table_check = await connection.fetchval("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'rag_log'
                    )
                """)
                
                if not table_check:
                    logger.error("rag_log table does not exist! Please run migration 002_create_rag_log_table.sql")
                    return
                
                await connection.execute(
                    query,
                    session_id,
                    patient_id,
                    user_query,
                    response,
                    chunks_extracted,
                    timestamp,
                    latency,
                )
                logger.debug(f"Successfully inserted RAG log entry for session {session_id} with latency {latency}s")
        except Exception as e:
            # Log error but don't fail the request if logging fails
            logger.error(f"Failed to log RAG query: {str(e)}", exc_info=True)
            # Don't re-raise - we want logging failures to be silent

