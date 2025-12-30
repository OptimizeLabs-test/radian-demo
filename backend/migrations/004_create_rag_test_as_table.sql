-- Migration: Create rag_test_as table for RAG testing and evaluation
-- This table stores test results comparing RAG answers against expected requirements

-- Create rag_test_as table
CREATE TABLE IF NOT EXISTS public.rag_test_as (
    id BIGSERIAL PRIMARY KEY,
    run_id TEXT NOT NULL,
    test_id TEXT NOT NULL,
    file_name TEXT,
    page_number INTEGER,
    question TEXT NOT NULL,
    answer_must_include TEXT,
    rag_answer TEXT NOT NULL,
    score NUMERIC(5, 2) NOT NULL,
    pass_fail BOOLEAN NOT NULL,
    must_include_score NUMERIC(3, 2) NOT NULL,
    missing_must_include TEXT,
    judge_score INTEGER,
    judge_rationale TEXT,
    top_similarity NUMERIC(5, 4),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS rag_test_as_run_id_idx ON public.rag_test_as(run_id);
CREATE INDEX IF NOT EXISTS rag_test_as_test_id_idx ON public.rag_test_as(test_id);
CREATE INDEX IF NOT EXISTS rag_test_as_created_at_idx ON public.rag_test_as(created_at DESC);

-- Add comment to table
COMMENT ON TABLE public.rag_test_as IS 'RAG test evaluation results - stores answers and scores for test questions';

