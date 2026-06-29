import { useState, useCallback } from 'react';
import { chatService } from '../services/chatService';
import { ChatRequest, Citation, StreamEvent } from '../types/chat';
import { useChatStore } from '../store/chatStore'; // Assuming this path for useChatStore

export const useSSEStream = () => {
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(async (
    payload: ChatRequest,
    onMessageUpdate: (content: string) => void,
    onCitationsReceived: (citations: Citation[]) => void,
    onComplete: () => void
  ) => {
    setIsStreaming(true);
    setError(null);
    let fullContent = '';

    const { enabledSkillIds } = useChatStore.getState();

    try {
      await chatService.sendMessageStream({ ...payload, used_skills: enabledSkillIds }, (event: StreamEvent) => {
        switch (event.type) {
          case 'message':
            fullContent += event.data.text;
            onMessageUpdate(fullContent);
            break;
          case 'citations':
            onCitationsReceived(event.data.citations);
            break;
          case 'error':
            setError(event.data.message || 'Errore sconosciuto');
            break;
          case 'done':
            setIsStreaming(false);
            onComplete();
            break;
        }
      });
    } catch (err: any) {
      console.error('Streaming error hook:', err);
      setError(err.message || 'Errore di connessione');
      setIsStreaming(false);
    }
  }, []);

  return {
    sendMessage,
    isStreaming,
    error,
  };
};
