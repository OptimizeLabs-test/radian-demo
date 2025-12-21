/**
 * TARA Streaming API
 * 
 * This file provides utilities for streaming chat responses from Python.
 * Use this when you're ready to implement real-time streaming with SSE.
 * 
 * Currently, the frontend uses "fake streaming" (displays full response
 * with a typing animation). When you implement Python SSE streaming,
 * you can switch to these functions for real-time token streaming.
 */

import { API_CONFIG } from './config';
import type { ChatMessage } from './types';

/**
 * Stream Chat Response using Server-Sent Events (SSE)
 * 
 * Endpoint: POST /api/patients/{id}/chat/stream
 * 
 * Python Implementation Notes (FastAPI example):
 * 
 * ```python
 * from fastapi import FastAPI
 * from fastapi.responses import StreamingResponse
 * from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
 * 
 * @app.post("/api/patients/{patient_id}/chat/stream")
 * async def stream_chat(patient_id: str, request: ChatRequest):
 *     async def generate():
 *         async for chunk in rag_chain.astream(request.question):
 *             yield f"data: {json.dumps({'content': chunk})}\n\n"
 *         yield "data: [DONE]\n\n"
 *     
 *     return StreamingResponse(generate(), media_type="text/event-stream")
 * ```
 * 
 * @param patientId - The patient ID
 * @param question - The doctor's question
 * @param conversationHistory - Previous messages for context
 * @param onChunk - Callback fired for each streamed text chunk
 * @param onComplete - Callback fired when streaming is complete
 * @param onError - Callback fired if an error occurs
 */
export async function streamChatResponse(
  patientId: string,
  question: string,
  conversationHistory: ChatMessage[],
  onChunk: (text: string) => void,
  onComplete: () => void,
  onError: (error: Error) => void
): Promise<void> {
  try {
    const response = await fetch(
      `${API_CONFIG.baseUrl}/patients/${patientId}/chat/stream`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, conversationHistory }),
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    if (!response.body) {
      throw new Error('No response body for streaming');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      
      if (done) {
        break;
      }
      
      const chunk = decoder.decode(value, { stream: true });
      
      // Parse SSE format: "data: {...}\n\n"
      const lines = chunk.split('\n').filter(line => line.startsWith('data: '));
      
      for (const line of lines) {
        const dataStr = line.slice(6); // Remove "data: " prefix
        
        if (dataStr === '[DONE]') {
          onComplete();
          return;
        }
        
        try {
          const data = JSON.parse(dataStr);
          if (data.content) {
            onChunk(data.content);
          }
        } catch {
          // Skip malformed JSON chunks
          console.warn('Skipping malformed SSE chunk:', dataStr);
        }
      }
    }
    
    onComplete();
  } catch (error) {
    onError(error instanceof Error ? error : new Error('Stream failed'));
  }
}

/**
 * Helper to create an AbortController for cancelling streams
 * 
 * Usage:
 * ```typescript
 * const { controller, abort } = createStreamController();
 * 
 * streamChatResponse(...).catch(() => {});
 * 
 * // To cancel:
 * abort();
 * ```
 */
export function createStreamController() {
  const controller = new AbortController();
  return {
    controller,
    signal: controller.signal,
    abort: () => controller.abort(),
  };
}
