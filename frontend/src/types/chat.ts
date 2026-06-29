export interface ChatRequest {
  text: string;
  isPensieroProfondoAttivo?: boolean;
  session_id?: string;
  image_url?: string;
  thinking_level?: 'fast' | 'normal' | 'deep';
  isCitationsEnabled?: boolean;
  used_skills?: string[];
}

export interface Citation {
  id: string;
  file_name: string;
  page?: number;
  score: number;
  excerpt: string;
}

export interface APIResponse<T> {
  success: boolean;
  data: T | null;
  error: {
    error_code: string;
    message: string;
    request_id: string;
    timestamp: string;
  } | null;
}

export interface ChatResponse {
  response: string;
  used_skills?: string[];
  citations?: Citation[];
  reasoning?: string;
  artifacts?: Array<{
    type: 'code' | 'text' | 'markdown';
    content: string;
    filename?: string;
  }>;
}

export interface ModelInfo {
  id: string;
  name: string;
  description: string;
}

export interface ModelsResponse {
  models: ModelInfo[];
}

export interface SkillInfo {
  id: string;
  name: string;
  description: string;
  category?: string;
}

export interface SkillsResponse {
  skills: SkillInfo[];
}

export type StreamEventType = 'message' | 'citations' | 'done' | 'error';

export interface StreamEvent {
  type: StreamEventType;
  data: any;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  citations?: Citation[];
  status?: 'sending' | 'streaming' | 'completed' | 'error';
  reasoning?: string;
  artifacts?: Array<{
    type: 'code' | 'text' | 'markdown';
    content: string;
    filename?: string;
  }>;
}

export interface ChatSession {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}
