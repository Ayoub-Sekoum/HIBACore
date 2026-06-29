import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useChatStore } from '../../store/chatStore';
import ChatInput from './ChatInput';
import MessageList from './MessageList';
import Canvas from './Canvas';
import { useSSEStream } from '../../hooks/useSSEStream';
import { chatService } from '../../services/chatService';
import { v4 as uuidv4 } from 'uuid';
import { 
  Plus, 
  ChevronDown, 
  Mail,
  FileText,
  Code2
} from 'lucide-react';

const ChatContainer: React.FC = () => {
  const { 
    messages, 
    addMessage, 
    updateMessage, 
    currentSessionId,
    availableModels,
    thinkingLevel,
    isDeepThinking,
    isCitationsEnabled,
    setThinkingLevel,
    setAvailableModels,
    clearChat,
    activeArtifact
  } = useChatStore();
  
  const { sendMessage, isStreaming } = useSSEStream();
  const [showModelMenu, setShowModelMenu] = useState(false);
  // Fetch models on mount
  useEffect(() => {
    const fetchModels = async () => {
      try {
        const models = await chatService.getModels();
        setAvailableModels(models);
      } catch (error) {
        console.error('Failed to fetch real models:', error);
      }
    };
    fetchModels();
  }, [setAvailableModels]);

  const handleSend = async (text: string) => {
    const userMessageId = uuidv4();
    const assistantMessageId = uuidv4();

    addMessage({
      id: userMessageId,
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
      status: 'completed'
    });

    addMessage({
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
      status: 'streaming'
    });

    const request = { 
      text, 
      session_id: currentSessionId || undefined,
      thinking_level: thinkingLevel,
      isPensieroProfondoAttivo: isDeepThinking,
      isCitationsEnabled: isCitationsEnabled
    };

    try {
      if (thinkingLevel === 'deep') {
        try {
          const response = await chatService.sendMessage(request);
          updateMessage(assistantMessageId, {
            content: response.response,
            status: 'completed',
            citations: response.citations,
            reasoning: response.reasoning,
            artifacts: response.artifacts
          });
        } catch (err: any) {
          updateMessage(assistantMessageId, {
            content: `Error: ${err.message}`,
            status: 'error'
          });
        }
        return;
      }

      await sendMessage(
        request,
        (content) => {
          updateMessage(assistantMessageId, { content });
        },
        (citations) => {
          updateMessage(assistantMessageId, { citations });
        },
        () => {
          updateMessage(assistantMessageId, { status: 'completed' });
        }
      );
    } catch (err: any) {
        console.error("Failed to send message:", err);
        updateMessage(assistantMessageId, {
          content: `Error: Failed to send message. ${err.message || ''}`,
          status: 'error'
        });
    }
  };

  const selectedModelName = availableModels.find(m => m.id === thinkingLevel)?.name || 'HOBA Pro';

  return (
    <div className="flex-1 flex flex-col h-full relative overflow-hidden bg-[var(--wrapper-bg)]">
      {/* Premium Header */}
      <header className="h-16 flex items-center justify-between px-4 md:px-8 shrink-0 border-b md:border-none border-[var(--border-light)] dark:border-[#333] transition-colors">
        <div className="flex items-center gap-2">
          <div className="relative group">
            <button 
              onClick={() => setShowModelMenu(!showModelMenu)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg border text-[13px] font-medium transition-all shadow-sm active:scale-95 bg-white border-[var(--border-light)] text-[var(--apple-text)] hover:bg-gray-50 dark:bg-[#1d1d1f] dark:border-[#333]"
            >
              <div className="logo-wrapper">
                <svg className="apple-icon w-3.5 h-auto text-[var(--brand-red)]" viewBox="0 0 100 85">
                  <path className="path-main" d="M50 5 L95 80 L78 80 L50 35 L22 80 L5 80 Z" />
                </svg>
              </div>
              <span className="capitalize">
                {selectedModelName}
              </span>
              <ChevronDown size={14} className={`text-gray-400 transition-transform ${showModelMenu ? 'rotate-180' : ''}`} />
            </button>

            {/* Model Dropdown Menu */}
            <AnimatePresence>
              {showModelMenu && (
                <>
                  <div 
                    className="fixed inset-0 z-40" 
                    onClick={() => setShowModelMenu(false)}
                  />
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 10 }}
                    className="absolute top-full left-0 mt-2 w-48 rounded-xl border bg-white shadow-xl z-50 p-1.5 dark:bg-[#1d1d1f] dark:border-[#333]"
                  >
                    {(availableModels.length > 0 ? availableModels : [
                      { id: 'fast', name: 'HOBA Mini', description: 'Fast & Lightweight' },
                      { id: 'normal', name: 'HOBA Pro', description: 'Balanced & Powerful' },
                      { id: 'deep', name: 'HOBA O1', description: 'Deep Reasoning' }
                    ]).map((model) => (
                      <button
                        key={model.id}
                        onClick={() => {
                          setThinkingLevel(model.id as any);
                          setShowModelMenu(false);
                        }}
                        className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                          thinkingLevel === model.id 
                            ? 'bg-red-50 text-red-600 dark:bg-red-950/30' 
                            : 'hover:bg-gray-50 dark:hover:bg-[#2d2d2f] text-[var(--apple-text)]'
                        }`}
                      >
                        <div className="text-[13px] font-semibold">{model.name}</div>
                        <div className="text-[11px] opacity-60 font-normal">{model.description}</div>
                      </button>
                    ))}
                  </motion.div>
                </>
              )}
            </AnimatePresence>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <button className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-[13px] font-medium transition-all active:scale-95 bg-white border-[var(--border-light)] text-[var(--apple-text-muted)] dark:bg-[#1d1d1f] dark:border-[#333]">
            <div className={`w-1.5 h-1.5 rounded-full ${isStreaming ? 'bg-amber-500' : 'bg-emerald-500'} animate-pulse`}></div>
            {isStreaming ? 'Thinking...' : 'Status'}
          </button>
          <button 
            onClick={() => clearChat()} 
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-white text-[13px] font-medium transition-all shadow-sm active:scale-95 bg-red-600 hover:bg-red-700"
          >
            <Plus size={14} /> 
            <span className="hidden sm:inline">New Thread</span>
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <div className={`flex-1 flex overflow-hidden transition-all duration-500 ${activeArtifact ? 'mr-0 md:mr-[50%] lg:mr-[45%]' : ''}`}>
        <main className="flex-1 overflow-y-auto flex flex-col items-center pt-12 px-6 pb-32">
          <AnimatePresence>
            {messages.length === 0 ? (
              <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="w-full flex flex-col items-center"
              >
                <div className="mb-8 scale-110 logo-wrapper">
                  <svg className="apple-icon w-20 h-auto" viewBox="0 0 100 85">
                    <path className="path-main" d="M50 5 L95 80 L78 80 L50 35 L22 80 L5 80 Z" />
                    <path className="path-star" d="M50 48 L53 56 L61 56 L55 61 L57 69 L50 64 L43 69 L45 61 L39 56 L47 56 Z" />
                  </svg>
                </div>
                
                <h1 className="text-[28px] md:text-[36px] font-semibold text-center mb-10 tracking-tight text-[var(--apple-text)] leading-tight animate-reveal">
                  Good Afternoon, Baki<br />
                  <span className="text-red-600">What's on your mind?</span>
                </h1>
  
                {/* Quick Actions Grid */}
                <div className="w-full max-w-[800px] grid grid-cols-1 md:grid-cols-4 gap-4 mt-8">
                  {[
                    { icon: Plus, text: "Write a to-do list for a personal project" },
                    { icon: Mail, text: "Generate an email to reply to a job offer" },
                    { icon: FileText, text: "Summarize this article in one paragraph" },
                    { icon: Code2, text: "How does AI work in a technical capacity" }
                  ].map((action, i) => {
                    const Icon = action.icon;
                    return (
                      <button 
                        key={i}
                        onClick={() => handleSend(action.text)}
                        className="flex flex-col justify-between p-5 h-[120px] rounded-2xl text-left group border transition-all active:scale-95 bg-gray-50 border-gray-100 hover:bg-gray-100/80 text-gray-700 dark:bg-[#1d1d1f] dark:border-[#333] dark:hover:bg-[#222]"
                      >
                        <span className="text-[13px] leading-snug font-medium transition-colors group-hover:text-red-500">{action.text}</span>
                        <Icon size={18} className="text-gray-400 group-hover:text-red-500 transition-colors" />
                      </button>
                    );
                  })}
                </div>
              </motion.div>
            ) : (
              <div className="w-full max-w-3xl flex-1 flex flex-col">
                <MessageList messages={messages} />
              </div>
            )}
          </AnimatePresence>
        </main>
      </div>

      <AnimatePresence>
        {activeArtifact && <Canvas />}
      </AnimatePresence>


      {/* Floating Input Area */}
      <div className={`absolute bottom-0 left-0 w-full p-6 transition-all duration-500 ${activeArtifact ? 'pr-0 md:pr-[50%] lg:pr-[45%]' : ''} bg-gradient-to-t from-[var(--wrapper-bg)] via-[var(--wrapper-bg)] to-transparent`}>
        <div className="max-w-3xl mx-auto">
          <ChatInput onSend={handleSend} disabled={isStreaming} />
          <p className="text-[10px] text-center mt-4 text-[var(--apple-text-muted)] tracking-tight uppercase font-medium">
            HOBA can make mistakes. Check important info.
          </p>
        </div>
      </div>
    </div>
  );
};

export default ChatContainer;
