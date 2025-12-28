-- Migration: Add latency column to rag_log table
-- This column stores the time taken to process each RAG query (in seconds)

-- Add latency column (REAL type to store decimal seconds)
ALTER TABLE public.rag_log 
ADD COLUMN IF NOT EXISTS latency REAL;

-- Add comment to column
COMMENT ON COLUMN public.rag_log.latency IS 'Time taken to process the RAG query in seconds';

-- Create index for latency queries (useful for performance analysis)
CREATE INDEX IF NOT EXISTS rag_log_latency_idx ON public.rag_log(latency);

