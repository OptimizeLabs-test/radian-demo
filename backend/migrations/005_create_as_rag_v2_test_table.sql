-- Migration: Create as_rag_v2_test table for RAG v2 (with re-ranking) testing and evaluation
-- This table stores test results comparing RAG v2 answers against expected requirements

-- Create as_rag_v2_test table
CREATE TABLE IF NOT EXISTS public.as_rag_v2_test (
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
CREATE INDEX IF NOT EXISTS as_rag_v2_test_run_id_idx ON public.as_rag_v2_test(run_id);
CREATE INDEX IF NOT EXISTS as_rag_v2_test_test_id_idx ON public.as_rag_v2_test(test_id);
CREATE INDEX IF NOT EXISTS as_rag_v2_test_created_at_idx ON public.as_rag_v2_test(created_at DESC);

-- Add comment to table
COMMENT ON TABLE public.as_rag_v2_test IS 'RAG v2 (with re-ranking) test evaluation results - stores answers and scores for test questions';

