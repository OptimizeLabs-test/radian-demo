-- Migration: Create RAG_log table for logging RAG queries and responses
-- This table stores all user queries, responses, session information, and retrieved chunks

-- Create RAG_log table
CREATE TABLE IF NOT EXISTS public.rag_log (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    patient_id TEXT NOT NULL,
    user_query TEXT NOT NULL,
    response TEXT NOT NULL,
    chunks_extracted TEXT NOT NULL,  -- Chunks separated by "----" delimiter
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS rag_log_session_id_idx ON public.rag_log(session_id);
CREATE INDEX IF NOT EXISTS rag_log_patient_id_idx ON public.rag_log(patient_id);
CREATE INDEX IF NOT EXISTS rag_log_timestamp_idx ON public.rag_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS rag_log_created_at_idx ON public.rag_log(created_at DESC);

-- Add comment to table
COMMENT ON TABLE public.rag_log IS 'Logs all RAG queries, responses, and retrieved chunks for audit and analysis';

