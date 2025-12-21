# TARA API Documentation

This document describes the API endpoints that the Python backend must implement to connect with the TARA frontend.

## Overview

- **Authentication**: Handled by Supabase (frontend only). Backend endpoints do not require auth tokens for this demo.
- **Base URL**: Configurable via `VITE_API_BASE_URL` environment variable (default: `http://localhost:8000/api`)
- **Content-Type**: All endpoints use `application/json`

## Important Constraints

All backend responses **MUST** avoid diagnostic statements. Focus on:
- Status updates and observations
- Trends and patterns
- Risk factors to monitor
- Suggested follow-ups
- Key clinical observations

---

## Endpoints

### 1. Get Patient Summary

Retrieve a high-level summary of the patient's current status.

```
GET /api/patients/{patient_id}/summary
```

**Response:**
```json
{
  "headline": "Overall Status - Stable with Monitoring Required",
  "content": "Patient shows stable vital trends over the past 3 months with consistent medication adherence. Recent lab work indicates HbA1c levels trending upward from 6.8% to 7.2%, suggesting need for dietary review..."
}
```

**Python Implementation Notes:**
- Query vector database for patient's complete longitudinal record
- Use LLM with system prompt: "Summarize the patient's current status, recent trends, and key observations. Do NOT provide diagnoses."
- `headline`: Short (5-10 words) status summary
- `content`: Detailed paragraph (100-200 words) with trends and observations

---

### 2. Get Specialty Perspectives

Retrieve specialty-specific insights from multiple clinical perspectives.

```
GET /api/patients/{patient_id}/specialties
```

**Response:**
```json
[
  {
    "specialty": "Cardiology",
    "insights": [
      "Blood pressure control has been stable on current ACE inhibitor",
      "ECG from last visit shows normal sinus rhythm, no ST changes",
      "Consider lipid profile review given diabetes management changes"
    ]
  },
  {
    "specialty": "Diabetes / Endocrinology",
    "insights": [
      "HbA1c trending upward from 6.8% to 7.2% - requires attention",
      "Patient adherent to metformin but may benefit from dosage review",
      "Recommend dietary consultation"
    ]
  }
]
```

**Python Implementation Notes:**
- Run multiple specialty-specific LLM agents in parallel
- Each specialty has its own system prompt:
  - **Cardiology**: "You are a cardiology specialist. Highlight cardiac-related insights, trends, and monitoring recommendations. Do NOT diagnose."
  - **Endocrinology**: "You are an endocrinology specialist. Review glycemic control, complications risk, and provide monitoring guidance. Do NOT diagnose."
- Return 3-5 insights per specialty as bullet points

---

### 3. Get Intro Message

Retrieve the proactive RAG agent's initial message with suggested queries.

```
GET /api/patients/{patient_id}/intro-message
```

**Response:**
```json
{
  "message": "Based on the patient's recent lab trends and clinical notes, you may want to explore:\n\n• Changes in glycemic control over the last 6 months\n• Current cardiac medication adherence and effectiveness\n• Correlation between exercise routine and blood pressure readings"
}
```

**Python Implementation Notes:**
- RAG agent analyzes patient record to identify key areas of interest
- Generate 3-5 proactive suggestions as bullet points
- Phrase as questions or areas to explore, not statements

---

### 4. Send Chat Message

Send a question to the RAG conversational agent.

```
POST /api/patients/{patient_id}/chat
```

**Request Body:**
```json
{
  "question": "What's the trend in HbA1c over the last 6 months?",
  "conversationHistory": [
    { "role": "user", "content": "Tell me about the patient's medications" },
    { "role": "assistant", "content": "The patient is currently on..." }
  ]
}
```

**Response:**
```json
{
  "message": "Looking at the longitudinal data, HbA1c has shown an upward trend from 6.8% (3 months ago) to 7.0% (6 weeks ago) to 7.2% (current). This coincides with patient-reported increased work stress..."
}
```

**Python Implementation Notes:**
- Use RAG to retrieve relevant context from vector database
- Include conversation history for context continuity
- Generate response using LangChain/LLM
- Focus on providing information, observations, and guidance
- **IMPORTANT**: Do NOT provide diagnostic statements

---

### 5. Stream Chat Message (Future)

Stream chat response in real-time using Server-Sent Events.

```
POST /api/patients/{patient_id}/chat/stream
```

**Request Body:** Same as `/chat`

**Response:** Server-Sent Events stream
```
data: {"content": "Looking at "}

data: {"content": "the longitudinal "}

data: {"content": "data..."}

data: [DONE]
```

**Python Implementation (FastAPI example):**
```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import json

@app.post("/api/patients/{patient_id}/chat/stream")
async def stream_chat(patient_id: str, request: ChatRequest):
    async def generate():
        async for chunk in rag_chain.astream(request.question):
            yield f"data: {json.dumps({'content': chunk})}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate(), 
        media_type="text/event-stream"
    )
```

---

## Error Handling

All endpoints should return errors in this format:

```json
{
  "message": "Human-readable error message",
  "code": "ERROR_CODE",
  "details": { }
}
```

**HTTP Status Codes:**
- `400` - Bad request (invalid input)
- `404` - Patient not found
- `500` - Internal server error
- `503` - Service unavailable (LLM/vector DB issues)

---

## TypeScript Types

The frontend expects these exact TypeScript interfaces. See `src/lib/api/types.ts` for the complete type definitions.

```typescript
interface PatientSummary {
  headline: string;
  content: string;
}

interface SpecialtyPerspective {
  specialty: string;
  insights: string[];
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

interface ChatRequest {
  question: string;
  conversationHistory: ChatMessage[];
}

interface ChatResponse {
  message: string;
}
```

---

## Environment Configuration

Create a `.env` file in the frontend project:

```env
# Python backend URL
VITE_API_BASE_URL=http://localhost:8000/api

# Set to "false" to use real API instead of mock data
VITE_USE_MOCK_API=true
```

---

## Testing

The frontend includes mock data that mirrors expected backend responses. To test:

1. Keep `VITE_USE_MOCK_API=true` (default) for demo mode
2. Set `VITE_USE_MOCK_API=false` when Python backend is ready
3. Mock responses are in `src/lib/api/mock.ts` - use as reference

---

## CORS Configuration

Your Python backend must allow CORS from the frontend origin:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://your-frontend-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
