# Performance Optimization Guide

This document outlines the optimizations implemented to improve vector search and overall RAG performance.

## Implemented Optimizations

### 1. IVFFLAT Index Configuration
- **Probes reduced to 1**: Changed from 10 to 1 for maximum speed
  - Tradeoff: Slightly less accurate but significantly faster
  - Can be adjusted via `IVFFLAT_PROBES` environment variable
  - Range: 1 (fastest) to lists value in index (most accurate)

### 2. Reduced Chunk Retrieval
- **Max chunks reduced**: From 12 to 8 (configurable)
- **Chat queries use 6 chunks**: Further reduced for chat responses
- **Capped at 10 in query**: Database query limits to 10 max

### 3. Lower Similarity Thresholds
- **Chat threshold**: Reduced from 0.3 to 0.2 for faster retrieval
- **Summary threshold**: Kept at 0.2

### 4. Connection Pool Optimization
- **Min pool size**: Increased from 2 to 5
- **Max pool size**: Increased from 10 to 20
- Better connection availability and concurrency

### 5. Query Optimization
- **Removed redundant filtering**: Stored function already filters by similarity
- **Early exit**: Stop processing once we have enough chunks
- **Direct conversion**: Eliminated extra loops and filtering

### 6. Reduced LLM Token Limits
- **Summary**: 400 tokens (reduced from 600)
- **Chat**: 800 tokens (for formatted responses)

## Configuration

Adjust these settings in your `.env` file:

```env
# Speed vs Accuracy Tradeoff
IVFFLAT_PROBES=1              # 1 = fastest, higher = more accurate (max = lists in index)

# Retrieval Settings
MAX_RETRIEVAL_CHUNKS=8        # Number of chunks to retrieve
MIN_SIMILARITY_SCORE=0.2      # Minimum similarity threshold
MIN_SIMILARITY_SCORE_CHAT=0.2 # Chat-specific threshold

# Connection Pool
PG_POOL_MIN_SIZE=5            # Minimum database connections
PG_POOL_MAX_SIZE=20           # Maximum database connections
```

## Performance Tuning Tips

### If searches are still slow:

1. **Verify index exists**:
   ```sql
   SELECT indexname, indexdef 
   FROM pg_indexes 
   WHERE tablename = 'patient_chunks' 
   AND indexname LIKE '%embedding%';
   ```

2. **Check if stored function exists**:
   ```sql
   SELECT proname FROM pg_proc WHERE proname = 'match_patient_chunks';
   ```

3. **Reduce probes further** (if index exists):
   - Set `IVFFLAT_PROBES=1` (already done)
   - This is the fastest setting

4. **Reduce chunk count**:
   - Set `MAX_RETRIEVAL_CHUNKS=6` or lower
   - Fewer chunks = faster queries

5. **Increase connection pool**:
   - If you have many concurrent users, increase `PG_POOL_MAX_SIZE`

### If accuracy is too low:

1. **Increase probes**:
   - Set `IVFFLAT_PROBES=5` or `10` for better accuracy
   - Slower but more accurate

2. **Increase similarity threshold**:
   - Set `MIN_SIMILARITY_SCORE=0.3` for stricter matching

3. **Increase chunk count**:
   - Set `MAX_RETRIEVAL_CHUNKS=12` for more context

## Monitoring Performance

To check if optimizations are working:

1. **Check query execution time** in Supabase dashboard
2. **Monitor connection pool usage** in application logs
3. **Track embedding generation time** (OpenAI API latency)
4. **Measure end-to-end response time** for chat queries

## Expected Performance

With these optimizations:
- **Vector search**: Should be < 100ms (with index)
- **Embedding generation**: ~200-500ms (OpenAI API)
- **LLM response**: ~1-3 seconds (OpenAI API)
- **Total chat response**: ~2-4 seconds

If performance is still slow, the bottleneck is likely:
1. OpenAI API latency (embedding + LLM calls)
2. Network latency to Supabase
3. Missing IVFFLAT index (verify migration was run)

