# Fixes Applied for Summary and RAG Retrieval

## Issues Found and Fixed

### 1. ❌ Invalid OpenAI Model Name
**Problem**: `openai_model: str = "gpt-4.1"` - This model doesn't exist
**Fix**: Changed to `"gpt-4o-mini"` (valid OpenAI model)
**File**: `backend/app/core/config.py`

### 2. ❌ Missing Fallback for Stored Function
**Problem**: Code would fail if migration wasn't run (stored function doesn't exist)
**Fix**: Added fallback to direct SQL query if stored function is missing
**File**: `backend/app/repositories/patient_chunks.py`

### 3. ❌ Timeout Too Short
**Problem**: 30 second timeout might be too short for RAG operations
**Fix**: Increased to 60 seconds in both frontend and backend
**Files**: 
- `src/lib/api/config.ts` (frontend timeout)
- `backend/app/core/config.py` (backend timeout)

### 4. ❌ Poor Error Handling
**Problem**: Generic errors didn't help identify issues
**Fix**: Added specific error messages for:
- Invalid model names
- Missing stored functions
- Better logging
**Files**: 
- `backend/app/services/rag.py`
- `backend/app/repositories/patient_chunks.py`

## Changes Made

### Backend Changes

1. **`backend/app/core/config.py`**:
   - Fixed model name: `"gpt-4.1"` → `"gpt-4o-mini"`
   - Increased timeout: `30` → `60` seconds

2. **`backend/app/repositories/patient_chunks.py`**:
   - Added fallback query if stored function doesn't exist
   - Added logging for warnings
   - Better error handling for missing functions

3. **`backend/app/services/rag.py`**:
   - Added error handling for invalid model names
   - Better error messages for debugging

### Frontend Changes

1. **`src/lib/api/config.ts`**:
   - Increased timeout: `30000` → `60000` milliseconds

## Testing Checklist

To verify everything works:

1. ✅ **Check Backend is Running**:
   ```bash
   cd backend
   poetry run uvicorn app.main:app --reload --port 8000
   ```

2. ✅ **Verify Environment Variables**:
   - `DATABASE_URL` is set correctly
   - `OPENAI_API_KEY` is set correctly
   - Check `.env` file in `backend/` directory

3. ✅ **Test Summary Endpoint**:
   ```bash
   curl http://localhost:8000/api/patients/P1-Sanjeev-Malhotra/summary
   ```

4. ✅ **Test Chat Endpoint**:
   ```bash
   curl -X POST http://localhost:8000/api/patients/P1-Sanjeev-Malhotra/chat \
     -H "Content-Type: application/json" \
     -d '{"question": "What are the patient's vitals?", "conversationHistory": []}'
   ```

5. ✅ **Check Frontend Configuration**:
   - Ensure `VITE_USE_MOCK_API=false` in frontend `.env`
   - Ensure `VITE_API_BASE_URL=http://localhost:8000/api` is set

## Common Issues and Solutions

### Issue: "Invalid OpenAI model" error
**Solution**: Check your `.env` file has correct model name. Should be `gpt-4o-mini`, `gpt-4o`, or `gpt-4-turbo`

### Issue: "Stored function not found" warning
**Solution**: Run the migration in Supabase SQL Editor:
```sql
-- Copy contents from backend/migrations/001_add_ivfflat_index_and_function.sql
```

### Issue: Timeout errors
**Solution**: 
- Check network connection
- Verify backend is running
- Increase timeout if needed (already set to 60s)

### Issue: No chunks returned
**Solution**:
- Verify patient data exists in database
- Check patient ID format matches (e.g., "P1-Sanjeev-Malhotra")
- Verify embeddings exist for chunks

## Next Steps

1. **Run the migration** (if not already done):
   - Go to Supabase Dashboard → SQL Editor
   - Run `backend/migrations/001_add_ivfflat_index_and_function.sql`

2. **Restart the backend**:
   ```bash
   cd backend
   poetry run uvicorn app.main:app --reload --port 8000
   ```

3. **Test the frontend**:
   - Make sure `VITE_USE_MOCK_API=false`
   - Navigate to a patient page
   - Check that summary loads
   - Test chat functionality

## Notes

- The code now gracefully handles missing stored functions (falls back to direct queries)
- Error messages are more descriptive to help with debugging
- Timeouts are increased to handle slower RAG operations
- Model name is fixed to a valid OpenAI model

