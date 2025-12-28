/**
 * TARA API Endpoints
 * 
 * This file contains all HTTP calls to the Python backend.
 * When API_CONFIG.useMock is true, mock data is returned instead.
 * 
 * To connect your Python backend:
 * 1. Set VITE_USE_MOCK_API=false in .env
 * 2. Set VITE_API_BASE_URL to your backend URL
 * 3. Ensure your backend implements all endpoints below
 */

import { API_CONFIG } from './config';
import type { 
  PatientSummary, 
  SpecialtyPerspective, 
  ChatMessage,
  ChatResponse,
  IntroMessageResponse,
  ApiError 
} from './types';
import * as mock from './mock';

/**
 * Helper function to handle API responses
 * Throws an error with the backend's error message if the request fails
 */
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error: ApiError = await response.json().catch(() => ({ 
      message: `HTTP ${response.status}: ${response.statusText}` 
    }));
    throw new Error(error.message);
  }
  return response.json();
}

/**
 * Fetch Patient Summary
 * 
 * Endpoint: GET /api/patients/{id}/summary
 * 
 * Python Implementation Notes:
 * - Query vector DB for patient's complete record
 * - Use LLM with system prompt focusing on status, trends, observations
 * - Return headline (short) and content (detailed paragraph)
 * - IMPORTANT: No diagnostic statements
 */
export async function fetchSummary(patientId: string): Promise<PatientSummary> {
  if (API_CONFIG.useMock) {
    return mock.getMockSummary(patientId);
  }
  
  try {
    const response = await fetch(
      `${API_CONFIG.baseUrl}/patients/${patientId}/summary`,
      { signal: AbortSignal.timeout(API_CONFIG.timeout) }
    );
    return await handleResponse<PatientSummary>(response);
  } catch (error) {
    console.error('Fetch summary error:', error);
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error(
        `Failed to connect to server at ${API_CONFIG.baseUrl}. ` +
        `Please check if the backend is running.`
      );
    }
    throw error;
  }
}

/**
 * Fetch Specialty Perspectives
 * 
 * Endpoint: GET /api/patients/{id}/specialties
 * 
 * Python Implementation Notes:
 * - Run multiple specialty-specific LLM agents in parallel
 * - Each agent has its own system prompt (cardiology, endocrinology, etc.)
 * - Return array of perspectives with specialty name and insights list
 * - IMPORTANT: No diagnostic statements
 */
export async function fetchSpecialties(patientId: string): Promise<SpecialtyPerspective[]> {
  if (API_CONFIG.useMock) {
    return mock.getMockSpecialties(patientId);
  }
  
  const response = await fetch(
    `${API_CONFIG.baseUrl}/patients/${patientId}/specialties`,
    { signal: AbortSignal.timeout(API_CONFIG.timeout) }
  );
  return handleResponse<SpecialtyPerspective[]>(response);
}

/**
 * Fetch Intro Message
 * 
 * Endpoint: GET /api/patients/{id}/intro-message
 * 
 * Python Implementation Notes:
 * - RAG agent analyzes patient record
 * - Generate proactive suggestions for what doctor might want to explore
 * - Return a single message string with bullet points
 */
export async function fetchIntroMessage(patientId: string): Promise<string> {
  if (API_CONFIG.useMock) {
    return mock.getMockIntroMessage(patientId);
  }
  
  const response = await fetch(
    `${API_CONFIG.baseUrl}/patients/${patientId}/intro-message`,
    { signal: AbortSignal.timeout(API_CONFIG.timeout) }
  );
  const data = await handleResponse<IntroMessageResponse>(response);
  return data.message;
}

/**
 * Send Chat Question
 * 
 * Endpoint: POST /api/patients/{id}/chat
 * 
 * Request Body:
 * {
 *   "question": "string",
 *   "conversationHistory": [{ "role": "user"|"assistant", "content": "string" }]
 * }
 * 
 * Python Implementation Notes:
 * - Use RAG to retrieve relevant context from vector DB
 * - Include conversation history for context
 * - Generate response using LangChain/LLM
 * - IMPORTANT: No diagnostic statements
 * 
 * Future: For streaming, see streaming.ts
 */
export async function sendChatQuestion(
  patientId: string,
  question: string,
  conversationHistory: ChatMessage[]
): Promise<string> {
  if (API_CONFIG.useMock) {
    return mock.getMockChatResponse(patientId, question);
  }
  
  try {
    const url = `${API_CONFIG.baseUrl}/patients/${patientId}/chat`;
    console.log('Sending chat question to:', url);
    
    const response = await fetch(
      url,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, conversationHistory }),
        signal: AbortSignal.timeout(API_CONFIG.timeout),
      }
    );
    const data = await handleResponse<ChatResponse>(response);
    return data.message;
  } catch (error) {
    console.error('Chat API error:', error);
    // Provide more helpful error messages
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error(
        `Failed to connect to server at ${API_CONFIG.baseUrl}. ` +
        `Please check if the backend is running. ` +
        `You can test the connection by visiting ${API_CONFIG.baseUrl.replace('/api', '')}/healthz`
      );
    }
    if (error instanceof Error && error.message.includes('timeout')) {
      throw new Error('Request timed out. The server may be slow or unresponsive.');
    }
    throw error;
  }
}

/**
 * Transcribe Audio File
 * 
 * Endpoint: POST /api/patients/{id}/transcribe
 * 
 * Request: multipart/form-data with audio file
 * 
 * Uses OpenAI Whisper API to transcribe audio to text.
 */
export async function transcribeAudio(
  patientId: string,
  audioFile: File
): Promise<string> {
  if (API_CONFIG.useMock) {
    // Return mock transcription after a delay
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve("This is a mock transcription of the audio.");
      }, 1000);
    });
  }
  
  const formData = new FormData();
  formData.append('audio_file', audioFile);
  
  try {
    const url = `${API_CONFIG.baseUrl}/patients/${patientId}/transcribe`;
    console.log('Transcribing audio to:', url);
    
    const response = await fetch(
      url,
      {
        method: 'POST',
        body: formData,
        signal: AbortSignal.timeout(API_CONFIG.timeout * 2), // Longer timeout for audio processing
      }
    );
    const data = await handleResponse<ChatResponse>(response);
    return data.message;
  } catch (error) {
    console.error('Transcription error:', error);
    // Provide more helpful error messages
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error(
        `Failed to connect to server at ${API_CONFIG.baseUrl}. ` +
        `Please check if the backend is running.`
      );
    }
    if (error instanceof Error && error.message.includes('timeout')) {
      throw new Error('Transcription request timed out. Please try again.');
    }
    throw error;
  }
}
