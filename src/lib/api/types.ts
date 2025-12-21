/**
 * TARA API Type Definitions
 * 
 * These TypeScript interfaces define the data contracts between
 * the frontend and Python backend. Your backend MUST return data
 * matching these structures exactly.
 */

/**
 * Patient Summary
 * Endpoint: GET /api/patients/{id}/summary
 * 
 * Contains a headline and detailed content summarizing the patient's
 * current status, trends, and relevant observations.
 * IMPORTANT: No diagnostic statements - focus on status updates and trends.
 */
export interface PatientSummary {
  headline: string;
  content: string[];
}

/**
 * Specialty Perspective
 * Endpoint: GET /api/patients/{id}/specialties
 * 
 * Each specialty (e.g., Cardiology, Endocrinology) provides its own
 * list of insights based on specialized analysis of the patient record.
 * IMPORTANT: No diagnostic statements - focus on observations and monitoring.
 */
export interface SpecialtyPerspective {
  specialty: string;
  insights: string[];
}

/**
 * Chat Message
 * Used in conversation history for the RAG agent
 * 
 * role: "user" for doctor messages, "assistant" for AI responses
 * content: The message text
 */
export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

/**
 * Chat Request Body
 * Endpoint: POST /api/patients/{id}/chat
 * 
 * Sent to the backend when the doctor asks a question
 */
export interface ChatRequest {
  question: string;
  conversationHistory: ChatMessage[];
}

/**
 * Chat Response
 * Returned by POST /api/patients/{id}/chat
 */
export interface ChatResponse {
  message: string;
}

/**
 * Intro Message Response
 * Returned by GET /api/patients/{id}/intro-message
 */
export interface IntroMessageResponse {
  message: string;
}

/**
 * API Error Response
 * Standard error format returned by the backend
 */
export interface ApiError {
  message: string;
  code?: string;
  details?: Record<string, unknown>;
}
