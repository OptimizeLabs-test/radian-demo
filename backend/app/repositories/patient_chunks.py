"""
Data-access layer for the Supabase patient_chunks table.
"""

from dataclasses import dataclass
from typing import Iterable, Sequence
import re

import asyncpg
from pgvector.asyncpg import register_vector
from pgvector import Vector  # Add this import
import logging

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PatientChunk:
    chunk_id: str
    document_id: str
    patient_id: str
    file_name: str | None
    page_number: int | None
    chunk_index: int | None
    text: str | None
    similarity: float | None = None


class PatientChunkRepository:
    """Repository responsible for chunk retrieval and similarity search."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    @classmethod
    async def create(cls, database_url: str, *, min_size: int, max_size: int) -> "PatientChunkRepository":
        pool = await asyncpg.create_pool(dsn=database_url, min_size=min_size, max_size=max_size)
        # Register vector type on a connection from the pool
        async with pool.acquire() as conn:
            await register_vector(conn)
        return cls(pool)

    async def close(self) -> None:
        await self._pool.close()

    async def fetch_recent_chunks(self, patient_id: str, limit: int) -> list[PatientChunk]:
        """Return the most recent deterministic set of chunks for summarization."""
        
        query = """
        SELECT chunk_id, document_id, patient_id, file_name, page_number, chunk_index, text
        FROM patient_chunks
        WHERE patient_id = $1
        ORDER BY ingested_at DESC, page_number NULLS LAST, chunk_index NULLS LAST
        LIMIT $2
        """
        rows = await self._fetch(query, patient_id, limit)
        return [PatientChunk(**row) for row in rows]

    async def search_chunks_by_keyword(
        self,
        patient_id: str,
        keyword: str,
        limit: int,
    ) -> list[PatientChunk]:
        """
        Search chunks by keyword in text content (case-insensitive).
        Useful for finding all chunks containing a specific lab name or term.
        """
        query = """
        SELECT chunk_id, document_id, patient_id, file_name, page_number, chunk_index, text
        FROM patient_chunks
        WHERE patient_id = $1
          AND text ILIKE $2
        ORDER BY ingested_at DESC, page_number NULLS LAST, chunk_index NULLS LAST
        LIMIT $3
        """
        # Use %keyword% for partial matching
        search_term = f"%{keyword}%"
        rows = await self._fetch(query, patient_id, search_term, limit)
        return [PatientChunk(**row) for row in rows]

    async def fetch_chunks_by_documents(
        self,
        patient_id: str,
        document_ids: list[str],
        limit_per_document: int = 5,
    ) -> list[PatientChunk]:
        """
        Fetch chunks from specific documents. Useful for retrieving related chunks
        from the same documents that contain the keyword.
        """
        if not document_ids:
            return []
        
        # Use ANY to match any document_id in the list
        query = """
        SELECT chunk_id, document_id, patient_id, file_name, page_number, chunk_index, text
        FROM patient_chunks
        WHERE patient_id = $1
          AND document_id = ANY($2::text[])
        ORDER BY document_id, page_number NULLS LAST, chunk_index NULLS LAST
        LIMIT $3
        """
        # Limit total chunks retrieved
        total_limit = len(document_ids) * limit_per_document
        rows = await self._fetch(query, patient_id, document_ids, total_limit)
        return [PatientChunk(**row) for row in rows]

    async def search_similar_chunks(
        self,
        patient_id: str,
        embedding: Sequence[float],
        limit: int,
        *,
        min_similarity: float,
        ivfflat_probes: int = 10,
    ) -> list[PatientChunk]:
        """
        Vector similarity search scoped to a single patient using optimized stored function.
        
        Uses the match_patient_chunks stored function which leverages the IVFFLAT index
        for faster searches. The ivfflat_probes parameter controls the accuracy/speed tradeoff.
        """
        # Convert embedding list to a format that pgvector understands
        embedding_list = list(embedding) if not isinstance(embedding, list) else embedding
        
        # Convert embedding to Vector type
        embedding_vector = Vector(embedding_list)
        
        # Try to use the optimized stored function first, fallback to direct query if it doesn't exist
        async with self._pool.acquire() as connection:
            await register_vector(connection)
            
            try:
                # Set ivfflat.probes for this connection to control accuracy/speed tradeoff
                # Higher values = more accurate but slower (up to the 'lists' value in index)
                # Lower values = faster but less accurate
                # Using 1 for maximum speed (acceptable accuracy tradeoff)
                await connection.execute(f"SET LOCAL ivfflat.probes = {ivfflat_probes}")
                
                # Try to use the stored function (if migration was run)
                try:
                    rows = await connection.fetch(
                        "SELECT * FROM match_patient_chunks($1, $2, $3, $4)",
                        embedding_vector,
                        patient_id,
                        limit,  # Use full limit for better accuracy
                        min_similarity,
                    )
                except (asyncpg.exceptions.UndefinedFunctionError, asyncpg.exceptions.UndefinedTableError) as e:
                    # Fallback to direct query if stored function doesn't exist
                    # This happens if the migration hasn't been run yet
                    logger.warning(
                        f"Stored function 'match_patient_chunks' not found, using fallback query. "
                        f"Run migration to enable optimized search: {e}"
                    )
                    query = """
                    SELECT chunk_id,
                           document_id,
                           patient_id,
                           file_name,
                           page_number,
                           chunk_index,
                           text,
                           1 - (embedding <-> $2::vector) AS similarity
                    FROM patient_chunks
                    WHERE patient_id = $1
                      AND embedding IS NOT NULL
                    ORDER BY embedding <-> $2::vector
                    LIMIT $3
                    """
                    rows = await connection.fetch(query, patient_id, embedding_vector, limit)
                    # Filter by similarity threshold manually
                    rows = [r for r in rows if r["similarity"] and r["similarity"] >= min_similarity]
            except Exception as e:
                # If anything fails, fallback to direct query without IVFFLAT probes
                query = """
                SELECT chunk_id,
                       document_id,
                       patient_id,
                       file_name,
                       page_number,
                       chunk_index,
                       text,
                       1 - (embedding <-> $2::vector) AS similarity
                FROM patient_chunks
                WHERE patient_id = $1
                  AND embedding IS NOT NULL
                ORDER BY embedding <-> $2::vector
                LIMIT $3
                """
                rows = await connection.fetch(query, patient_id, embedding_vector, limit)
                # Filter by similarity threshold manually
                rows = [r for r in rows if r["similarity"] and r["similarity"] >= min_similarity]
        
        # Optimized: Directly convert rows to chunks without extra filtering loops
        # The stored function already filters by similarity threshold, so we can trust the results
        chunks = []
        for row in rows:
            if row["text"] and row["text"].strip():  # Only include chunks with non-empty text
                chunks.append(PatientChunk(
                    chunk_id=row["chunk_id"],
                    document_id=row["document_id"],
                    patient_id=row["patient_id"],
                    file_name=row["file_name"],
                    page_number=row["page_number"],
                    chunk_index=row["chunk_index"],
                    text=row["text"],
                    similarity=row["similarity"],
                ))
                # Early exit if we have enough chunks
                if len(chunks) >= limit:
                    break
        
        return chunks

    async def _fetch(self, query: str, *args) -> Iterable[asyncpg.Record]:
        async with self._pool.acquire() as connection:
            return await connection.fetch(query, *args)

