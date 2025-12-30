-- Migration: Add latency column to RAG test tables
-- This adds latency tracking to measure query performance

-- Add latency to rag_test_as table
ALTER TABLE IF EXISTS public.rag_test_as
ADD COLUMN IF NOT EXISTS latency REAL;

COMMENT ON COLUMN public.rag_test_as.latency IS 'Time taken to process the RAG query in seconds';

-- Add latency to as_rag_v2_test table
ALTER TABLE IF EXISTS public.as_rag_v2_test
ADD COLUMN IF NOT EXISTS latency REAL;

COMMENT ON COLUMN public.as_rag_v2_test.latency IS 'Time taken to process the RAG query in seconds';

-- Add latency to as_rag_v3_test table
ALTER TABLE IF EXISTS public.as_rag_v3_test
ADD COLUMN IF NOT EXISTS latency REAL;

COMMENT ON COLUMN public.as_rag_v3_test.latency IS 'Time taken to process the RAG query in seconds';

-- Create indexes for latency queries (useful for performance analysis)
CREATE INDEX IF NOT EXISTS rag_test_as_latency_idx ON public.rag_test_as(latency);
CREATE INDEX IF NOT EXISTS as_rag_v2_test_latency_idx ON public.as_rag_v2_test(latency);
CREATE INDEX IF NOT EXISTS as_rag_v3_test_latency_idx ON public.as_rag_v3_test(latency);

