/**
 * Chat Service — Handles communication with the Backend AI API.
 * Supports standard chat and SSE streaming.
 */

import { 
  ChatRequest, 
  Message, 
  ModelInfo, 
  ModelsResponse, 
  SkillInfo, 
  ChatResponse, 
  StreamEvent, 
  ChatSession,
  APIResponse
} from '../types/chat';

import { getAuthHeader } from './api';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Internal helper for auth headers — now unified with the global api client
const getAuthHeaders = async () => {
    return await getAuthHeader();
};

// Result type pattern as per skill
type Result<T, E = Error> = { ok: true; value: T } | { ok: false; error: E };

async function safeFetch<T>(url: string, options?: RequestInit): Promise<Result<T>> {
  try {
    const authHeaders = await getAuthHeaders();
    const headers = { ...authHeaders, ...(options?.headers || {}), 'Content-Type': 'application/json' };
    const response = await fetch(url, { ...options, headers });
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        return { ok: false, error: new Error(errorData.message || `HTTP error! status: ${response.status}`) };
    }
    const data = await response.json();
    return { ok: true, value: data };
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error : new Error(String(error)) };
  }
}

export const chatService = {
  /**
   * Standard non-streaming chat.
   */
  async sendMessage(payload: ChatRequest): Promise<ChatResponse> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/chat/chat`, {
      method: 'POST',
      headers: { ...headers, 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const result = await response.json();
    if (!result.success) {
      throw new Error(result.error?.message || 'Chat API error');
    }

    return result.data;
  },

  /**
   * SSE Streaming Chat.
   * Calls onEvent for each SSE event (message, citations, done, error).
   */
  async sendMessageStream(
    payload: ChatRequest,
    onEvent: (event: StreamEvent) => void
  ): Promise<void> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/chat/stream`, {
      method: 'POST',
      headers: { ...headers, 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`Streaming API error: ${response.statusText}`);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) throw new Error('ReadableStream not supported');

    let buffer = '';

    const _running = true;
    while (_running) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      
      const parts = buffer.split('\n\n');
      buffer = parts.pop() || '';

      for (const part of parts) {
        if (!part.trim()) continue;

        const lines = part.split('\n');
        let eventType = 'message';
        let dataStr = '';

        for (const line of lines) {
          if (line.startsWith('event: ')) {
            eventType = line.replace('event: ', '').trim();
          } else if (line.startsWith('data: ')) {
            dataStr = line.replace('data: ', '').trim();
          }
        }

        if (dataStr) {
          try {
            const data = JSON.parse(dataStr);
            onEvent({ type: eventType as any, data });
          } catch (e) {
            console.error('Failed to parse SSE data:', e);
          }
        }
      }
    }
  },

  /**
   * Fetches the list of available models.
   */
  async getModels(): Promise<ModelInfo[]> {
    const result = await safeFetch<APIResponse<ModelsResponse>>(`${API_BASE_URL}/chat/models`);
    if (!result.ok) {
        console.error("Failed to load models:", result.error);
        return [];
    }
    return result.value.data?.models || [];
  },

  async getSkills(): Promise<SkillInfo[]> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/chat/skills`, {
      headers
    });
    const result = await response.json();
    
    if (!result.success) {
      throw new Error(result.error?.message || 'Failed to fetch skills');
    }
    
    return result.data.skills;
  },

  async getConversations(): Promise<ChatSession[]> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/conversations`, {
      headers
    });
    const result = await response.json();
    
    if (!result.success) {
      throw new Error(result.error?.message || 'Failed to fetch conversations');
    }
    
    return result.data;
  },

  async getMessages(sessionId: string): Promise<Message[]> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/chat/history?session_id=${sessionId}`, {
      headers
    });
    const result = await response.json();
    
    if (!result.success) {
      throw new Error(result.error?.message || 'Failed to fetch history');
    }
    
    return result.data;
  },

  async uploadDocument(file: File): Promise<Record<string, unknown>> {
    const formData = new FormData();
    formData.append('file', file);
    
    // We don't set the Content-Type manually for FormData, the browser does it with the correct boundary.
    // But let's add Authorization and TenantId.
    const headers = await getAuthHeaders();
    // We remove Content-Type if present to let the browser decide (FormData)
    delete (headers as any)['Content-Type'];

    const response = await fetch(`${API_BASE_URL}/documents/upload`, {
      method: 'POST',
      headers,
      body: formData,
    });
    
    const result = await response.json();
    if (!result.success) {
      throw new Error(result.error?.message || 'Upload failed');
    }
    
    return result.data;
  }
};
