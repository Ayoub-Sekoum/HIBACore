/**
 * API Configuration — Centralized URLs and Endpoints.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const apiConfig = {
  baseUrl: API_BASE_URL,
  endpoints: {
    chat: `${API_BASE_URL}/chat/chat`,
    stream: `${API_BASE_URL}/chat/stream`,
    upload: `${API_BASE_URL}/upload`,
    sessions: `${API_BASE_URL}/sessions`,
    voice: `${API_BASE_URL}/voice`,
  },
};
