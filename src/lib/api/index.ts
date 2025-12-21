/**
 * TARA API Module
 * 
 * This is the main entry point for all API functionality.
 * Import from here for clean, consistent imports throughout the app.
 * 
 * Usage:
 * ```typescript
 * import { fetchSummary, fetchSpecialties } from '@/lib/api';
 * import type { PatientSummary, ChatMessage } from '@/lib/api';
 * ```
 */

// Types - Data contracts for Python backend
export type {
  PatientSummary,
  SpecialtyPerspective,
  ChatMessage,
  ChatRequest,
  ChatResponse,
  IntroMessageResponse,
  ApiError,
} from './types';

// Configuration
export { API_CONFIG, isMockMode } from './config';

// API Endpoints - Main functions to call
export {
  fetchSummary,
  fetchSpecialties,
  fetchIntroMessage,
  sendChatQuestion,
} from './endpoints';

// Streaming utilities (for future Python SSE integration)
export { streamChatResponse, createStreamController } from './streaming';
