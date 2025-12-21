/**
 * TARA API Configuration
 * 
 * This file centralizes all API configuration.
 * Modify these values when connecting to your Python backend.
 */

export const API_CONFIG = {
  /**
   * Base URL for the Python backend API
   * 
   * Development: http://localhost:8000/api
   * Production: https://your-domain.com/api
   * 
   * Set via environment variable VITE_API_BASE_URL
   */
  baseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',

  /**
   * Request timeout in milliseconds
   * Increase for slow RAG/LLM responses
   */
  timeout: 30000,

  /**
   * Use mock data instead of real API calls
   * 
   * Set to true for demo/development without backend
   * Set to false when Python backend is ready
   * 
   * Set via environment variable VITE_USE_MOCK_API
   */
  useMock: import.meta.env.VITE_USE_MOCK_API !== 'false',
} as const;

/**
 * Check if we're using mock mode
 * Useful for conditional logic in components
 */
export function isMockMode(): boolean {
  return API_CONFIG.useMock;
}
