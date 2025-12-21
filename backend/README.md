## TARA Backend (FastAPI + Supabase + OpenAI)

This backend powers the chat, specialty perspectives, and summary widgets used by the React frontend under `src/lib/api`. All endpoints follow the contracts shown in `API_DOCUMENTATION.md`.

### 1. Environment

Copy `.env.example` to `.env` and fill in Supabase + OpenAI secrets:

```
cp backend/.env.example backend/.env
```

| Variable | Description |
| --- | --- |
| `DATABASE_URL` | Supabase Postgres connection string with `patient_chunks` table |
| `OPENAI_API_KEY` | Key with access to `gpt-4o-mini` + `text-embedding-3-large` |
| `TARA_ENVIRONMENT` | Optional string (`local`, `dev`, `staging`, `prod`) |
| `TARA_SPECIALTY_AGENTS` | JSON array of specialties (defaults to Cardiology/Endocrinology/Nephrology) |

### 2. Install

We use Poetry for dependency management.

```
cd backend
poetry install
```

During bootstrap, run the migration to set up the vector index and optimized search function.

### Option 1: Using Supabase Dashboard (Recommended)

1. Go to your Supabase project dashboard
2. Navigate to **SQL Editor** (left sidebar)
3. Click **New Query**
4. Copy and paste the contents of `backend/migrations/001_add_ivfflat_index_and_function.sql`
5. Click **Run** to execute the migration

### Option 2: Using psql Command Line

**On Windows (PowerShell):**
```powershell
# Navigate to the project root directory
cd "C:\Users\Aarushi Sharma\OneDrive - University of Rhode Island\Documents\tara-backend"

# Get your DATABASE_URL from your .env file or Supabase dashboard
# Then run (replace YOUR_DATABASE_URL with your actual connection string):
$env:DATABASE_URL="your-connection-string-here"
psql $env:DATABASE_URL -f backend\migrations\001_add_ivfflat_index_and_function.sql
```

**On Mac/Linux:**
```bash
# Navigate to the project root directory
cd /path/to/tara-backend

# Run the migration (replace YOUR_DATABASE_URL with your actual connection string):
psql $DATABASE_URL -f backend/migrations/001_add_ivfflat_index_and_function.sql
```

**Note**: If `psql` is not installed, you can:
- Install PostgreSQL client tools, or
- Use Option 1 (Supabase Dashboard) instead

### What the Migration Does

The migration file (`backend/migrations/001_add_ivfflat_index_and_function.sql`) will:
1. Enable the pgvector extension
2. Create an IVFFLAT index for faster vector searches
3. Create an optimized stored function `match_patient_chunks` for similarity search
4. Set up proper indexing for performance

**Note**: The IVFFLAT index should be created after the table has some data (at least 100 rows recommended). The `lists` parameter in the index should be approximately rows/1000, with a minimum of 10.

### 3. Run locally

```
poetry run uvicorn app.main:app --reload --port 8000
```

The frontend expects the API at `http://localhost:8000/api`. Keep `VITE_API_BASE_URL` in the frontend `.env` aligned with this origin and flip `VITE_USE_MOCK_API=false` when ready.

### 4. Architecture Overview

- `app/core` – environment config + shared error helpers.
- `app/models` – pydantic schemas that match the TypeScript contracts.
- `app/repositories/patient_chunks.py` – asyncpg repository with vector similarity search.
- `app/services/rag.py` – OpenAI-powered RAG orchestrator (embeddings, specialty agents, intro message, chat).
- `app/api/routes.py` – `/api/patients/*` endpoints and SSE-compatible chat stream.
- `app/main.py` – FastAPI entrypoint, CORS config, dependency wiring, startup/shutdown hooks.

Each request flows through `RagService`, which:

1. Retrieves relevant context via `PatientChunkRepository`.
2. Formats chunks into deterministic prompts that forbid diagnostic statements.
3. Calls OpenAI (`gpt-4o-mini` for completions, `text-embedding-3-large` for retrieval).
4. Returns responses shaped exactly like the frontend TypeScript interfaces (`string[]` summary content, etc.).

### 5. Extending / Production Hardening

- Replace the placeholder SSE implementation in `post_chat_stream` with native OpenAI streaming by switching to `with client.chat.completions.stream(...)`.
- Add Redis or PostgreSQL caching (e.g., summary memoization) to control spend.
- Emit structured logs (patient_id, chunk_ids, latency) and wire OpenTelemetry exporters for enterprise observability.
- Wrap OpenAI + Supabase calls in circuit breakers/retries if you expect intermittent failures.
- Expand `specialty_agents` via environment config to add more perspectives without code changes.

### 6. Testing

- Unit-test services with pytest + pytest-asyncio (mock OpenAI + repository layer).
- Add integration tests that spin up a test Postgres (e.g., `docker run supabase/postgres`) with sample patient chunks to validate similarity search + response formatting.
- Contract tests should ensure JSON payloads match the frontend expectations before deployments.



### HOW TO RUN THIS PARTICULAR FILE:
For the frontend: npm run dev