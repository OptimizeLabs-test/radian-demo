# Database Migrations

This directory contains SQL migration files for setting up and optimizing the TARA backend database.

## Migration 001: IVFFLAT Index and Optimized Vector Search

**File**: `001_add_ivfflat_index_and_function.sql`

This migration optimizes vector similarity search performance by:

1. **Creating an IVFFLAT index** on the `embedding` column for faster vector searches
2. **Creating a stored function** `match_patient_chunks` that uses the index for optimized queries
3. **Setting up proper indexing** for performance

### Running the Migration

```bash
# Using psql
psql $DATABASE_URL -f backend/migrations/001_add_ivfflat_index_and_function.sql

# Or execute the SQL directly in your Supabase SQL editor
```

### Important Notes

- **Embedding Dimension**: The function is configured for 1536-dimensional embeddings (text-embedding-3-small). If you change the embedding model, update the vector dimension in the function.
- **Index Creation**: The IVFFLAT index should be created after the table has some data (at least 100 rows recommended).
- **Lists Parameter**: The `lists` parameter in the index should be approximately `rows/1000`, with a minimum of 10. The migration uses 50 as a default.
- **IVFFLAT Probes**: The `ivfflat.probes` setting controls the accuracy/speed tradeoff:
  - Higher values (up to `lists`) = more accurate but slower
  - Lower values = faster but less accurate
  - Default is 10, which is a good balance
  - Can be configured via `IVFFLAT_PROBES` environment variable

### Performance Benefits

- **Faster searches**: IVFFLAT index significantly speeds up vector similarity searches
- **Optimized queries**: Stored function reduces query overhead
- **Configurable accuracy**: Adjust probes based on your needs

### Configuration

The `ivfflat_probes` setting can be configured in your `.env` file:

```
IVFFLAT_PROBES=10
```

Or via the `Settings` class in `app/core/config.py`.

