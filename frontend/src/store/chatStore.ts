import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Message, ChatSession, ModelInfo } from '../types/chat';

interface ChatState {
  currentSessionId: string | null;
  messages: Message[];
  isLoading: boolean;
  isStreaming: boolean;
  thinkingLevel: 'fast' | 'normal' | 'deep';
  isDeepThinking: boolean;
  isCitationsEnabled: boolean;
  availableModels: ModelInfo[];
  enabledSkillIds: string[];
  sessions: ChatSession[];
  activeArtifact: {
    type: 'code' | 'text' | 'markdown';
    content: string;
    filename?: string;
  } | null;
  
  // Actions
  addMessage: (message: Message) => void;
  updateMessage: (id: string, updates: Partial<Message>) => void;
  setMessages: (messages: Message[]) => void;
  setThinkingLevel: (level: 'fast' | 'normal' | 'deep') => void;
  setDeepThinking: (active: boolean) => void;
  setCitationsEnabled: (enabled: boolean) => void;
  setAvailableModels: (models: ModelInfo[]) => void;
  toggleSkill: (skillId: string) => void;
  setSessions: (sessions: ChatSession[]) => void;
  setCurrentSession: (sessionId: string | null) => void;
  setActiveArtifact: (artifact: ChatState['activeArtifact']) => void;
  clearChat: () => void;
}

export const useChatStore = create<ChatState>()(
  persist(
    (set) => ({
      messages: [],
      currentSessionId: null,
      isStreaming: false,
      isLoading: false,
      thinkingLevel: 'normal',
      isDeepThinking: true,
      isCitationsEnabled: true,
      availableModels: [],
      enabledSkillIds: [],
      sessions: [],
      activeArtifact: null,

      addMessage: (message) => set((state) => ({ 
        messages: [...state.messages, message] 
      })),

      updateMessage: (id, updates) => set((state) => ({
        messages: state.messages.map((m) => m.id === id ? { ...m, ...updates } : m)
      })),

      setMessages: (messages) => set({ messages }),

      setThinkingLevel: (level) => set({ thinkingLevel: level }),

      setDeepThinking: (active) => set({ isDeepThinking: active }),

      setCitationsEnabled: (active) => set({ isCitationsEnabled: active }),

      setAvailableModels: (models) => set({ availableModels: models }),

      toggleSkill: (skillId) => set((state) => ({
        enabledSkillIds: state.enabledSkillIds.includes(skillId)
          ? state.enabledSkillIds.filter(id => id !== skillId)
          : [...state.enabledSkillIds, skillId]
      })),

      setSessions: (sessions) => set({ sessions }),

      setCurrentSession: (sessionId) => set({ currentSessionId: sessionId }),
      
      setActiveArtifact: (artifact) => set({ activeArtifact: artifact }),

      clearChat: () => set({ 
        messages: [], 
        currentSessionId: null,
        activeArtifact: null
      }),
    }),
    {
      name: 'meteora-chat-storage',
      partialize: (state) => ({
        thinkingLevel: state.thinkingLevel,
        isDeepThinking: state.isDeepThinking,
        isCitationsEnabled: state.isCitationsEnabled,
        currentSessionId: state.currentSessionId,
      }),
    }
  )
);
