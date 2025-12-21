-- Migration: Add IVFFLAT index and optimized vector search function
-- This migration optimizes vector similarity search performance

-- 1. Ensure pgvector extension is enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Create IVFFLAT Vector Index for performance optimization
-- Note: This index should be created after the table has some data (at least 100 rows recommended)
-- The 'lists' parameter should be approximately rows/1000, with a minimum of 10
CREATE INDEX IF NOT EXISTS patient_chunks_embedding_idx
ON public.patient_chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 50);

-- 3. Create optimized vector similarity search function
-- This function uses the IVFFLAT index for faster searches
CREATE OR REPLACE FUNCTION match_patient_chunks (
    query_embedding vector(1536),
    target_patient_id text,
    match_count int DEFAULT 12,
    match_threshold float DEFAULT 0.2
)
RETURNS TABLE (
    chunk_id text,
    document_id text,
    patient_id text,
    file_name text,
    page_number int,
    chunk_index int,
    text text,
    similarity float
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        chunk_id,
        document_id,
        patient_id,
        file_name,
        page_number,
        chunk_index,
        text,
        1 - (embedding <=> query_embedding) AS similarity
    FROM public.patient_chunks
    WHERE patient_id = target_patient_id
      AND embedding IS NOT NULL
      AND 1 - (embedding <=> query_embedding) > match_threshold
    ORDER BY embedding <=> query_embedding
    LIMIT match_count;
$$;

-- 4. Set default ivfflat probes configuration
-- This controls the tradeoff between accuracy and speed
-- Higher values (up to lists) = more accurate but slower
-- Lower values = faster but less accurate
-- Default is 10, which is a good balance
-- Can be adjusted per-query with: SET LOCAL ivfflat.probes = 10;
-- Note: This setting is session-specific and should be set per connection

-- 5. Add comment for documentation
COMMENT ON FUNCTION match_patient_chunks IS 
'Optimized vector similarity search using IVFFLAT index. 
Returns patient chunks ordered by cosine similarity.
Set ivfflat.probes per connection for accuracy/speed tradeoff.';

