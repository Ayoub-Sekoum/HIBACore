import React, { useState, useRef, useEffect } from 'react';
import { 
  Paperclip, 
  Send, 
  ChevronDown, 
  Zap,
  Brain,
  Sparkles
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useChatStore } from '../../store/chatStore';
import { chatService } from '../../services/chatService';

interface ChatInputProps {
  onSend: (text: string) => void;
  disabled?: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({ onSend, disabled }) => {
  const [text, setText] = useState('');
  const [showModelMenu, setShowModelMenu] = useState(false);
  const { 
    isDeepThinking, 
    setDeepThinking, 
    isCitationsEnabled, 
    setCitationsEnabled,
    thinkingLevel,
    setThinkingLevel
  } = useChatStore();
  
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [text]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (text.trim() && !disabled) {
      onSend(text);
      setText('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      try {
        await chatService.uploadDocument(file);
        alert(`File ${file.name} caricato correttamente! Verrà elaborato per il RAG.`);
      } catch (error) {
        console.error('Upload failed:', error);
        alert('Errore durante il caricamento del file.');
      }
    }
  };

  const models = [
    { id: 'fast', name: 'HOBA Mini', desc: 'Fast & Lightweight', icon: <Zap size={14} className="text-amber-500" /> },
    { id: 'normal', name: 'HOBA Pro', desc: 'Balanced & Powerful', icon: <Sparkles size={14} className="text-red-500" /> },
    { id: 'deep', name: 'HOBA 01', desc: 'Deep Reasoning', icon: <Brain size={14} className="text-purple-500" /> }
  ] as const;

  const currentModel = models.find(m => m.id === thinkingLevel) || models[1];

  return (
    <div className="w-full max-w-3xl mx-auto relative group">
      <input 
        type="file" 
        ref={fileInputRef} 
        className="hidden" 
        onChange={handleFileChange}
        accept=".pdf,.docx,.txt,.md"
      />
      
      <div className={`rounded-[24px] shadow-[0_8px_30px_rgb(0,0,0,0.04)] border p-2 px-3 transition-all focus-within:shadow-[0_8px_30px_rgb(0,0,0,0.08)] bg-white border-[var(--border-light)] ${disabled ? 'opacity-70' : ''}`}>
        <div className="flex items-start px-3 pt-3 pb-2">
          <div className="mr-2.5 mt-0.5 shrink-0">
            <div className="logo-wrapper">
              <svg className="apple-icon w-4 h-auto text-[var(--brand-red)]" viewBox="0 0 100 85">
                <path className="path-main" d="M50 5 L95 80 L78 80 L50 35 L22 80 L5 80 Z" />
              </svg>
            </div>
          </div>
          <textarea
            ref={textareaRef}
            rows={1}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Chiedi a HOBA..."
            disabled={disabled}
            className="w-full resize-none outline-none placeholder:text-gray-500 min-h-[44px] text-[15px] leading-relaxed bg-transparent text-[var(--apple-text)] scrollbar-none"
          />
        </div>

        <div className="flex items-center justify-between px-2 pb-1.5 mt-1">
          <div className="flex items-center gap-1 sm:gap-2 relative">
            <button 
              onClick={() => fileInputRef.current?.click()}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-[12px] font-bold transition-all active:scale-95 border-gray-100 text-gray-400 hover:text-gray-900 hover:bg-gray-50"
            >
              <Paperclip size={14} />
              <span className="hidden sm:inline">Attach</span>
            </button>

            {/* Model Selector Dropdown Replacement for Writing Styles*/}
            <div className="relative">
              <button 
                onClick={() => setShowModelMenu(!showModelMenu)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-xl border text-[12px] font-bold transition-all active:scale-95 border-gray-100 text-gray-600 hover:text-gray-900 hover:bg-gray-50"
              >
                {currentModel.icon}
                <span className="hidden sm:inline">{currentModel.name}</span>
                <ChevronDown size={14} className={`opacity-50 transition-transform ${showModelMenu ? 'rotate-180' : ''}`} />
              </button>

              <AnimatePresence>
                {showModelMenu && (
                  <>
                    <div className="fixed inset-0 z-40" onClick={() => setShowModelMenu(false)} />
                    <motion.div 
                      initial={{ opacity: 0, y: 10, scale: 0.95 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, y: 10, scale: 0.95 }}
                      className="absolute bottom-full left-0 mb-2 w-52 bg-white border border-gray-100 rounded-[18px] shadow-2xl z-50 overflow-hidden p-1.5"
                    >
                      {models.map((m) => (
                        <button
                          key={m.id}
                          onClick={() => {
                            setThinkingLevel(m.id);
                            setShowModelMenu(false);
                          }}
                          className={`w-full flex flex-col items-start gap-0.5 px-3 py-2.5 rounded-xl transition-all ${
                            thinkingLevel === m.id 
                            ? 'bg-red-50 text-red-600' 
                            : 'hover:bg-gray-50 text-[var(--apple-text)]'
                          }`}
                        >
                          <div className="flex items-center gap-2 font-bold text-[12px]">
                            {m.icon}
                            {m.name}
                          </div>
                          <div className="text-[10px] opacity-60 ml-5">{m.desc}</div>
                        </button>
                      ))}
                    </motion.div>
                  </>
                )}
              </AnimatePresence>
            </div>
          </div>

          <div className="flex items-center gap-2 sm:gap-4">
            {/* Deep Thinking Toggle*/}
            <div 
              onClick={() => setDeepThinking(!isDeepThinking)}
              className="flex items-center gap-2 cursor-pointer group/toggle active:scale-95 transition-transform"
              title="Attiva Skill Engine (Pensiero Profondo)"
            >
              <div className={`w-8 h-4 rounded-full flex items-center px-0.5 transition-colors ${isDeepThinking ? 'bg-[var(--brand-red)]' : 'bg-gray-200'}`}>
                <motion.div 
                  animate={{ x: isDeepThinking ? 16 : 0 }}
                  className="w-3 h-3 bg-white rounded-full shadow-sm" 
                />
              </div>
              <span className={`text-[12px] font-bold transition-colors ${isDeepThinking ? 'text-[var(--brand-red)]' : 'text-gray-400'}`}>Thinking</span>
            </div>

            {/* Citation Toggle*/}
            <div 
              onClick={() => setCitationsEnabled(!isCitationsEnabled)}
              className="hidden sm:flex items-center gap-2 cursor-pointer group/toggle active:scale-95 transition-transform"
              title="Attiva Recupero Documenti (RAG)"
            >
              <div className={`w-8 h-4 rounded-full flex items-center px-0.5 transition-colors ${isCitationsEnabled ? 'bg-[var(--brand-red)]' : 'bg-gray-200'}`}>
                <motion.div 
                  animate={{ x: isCitationsEnabled ? 16 : 0 }}
                  className="w-3 h-3 bg-white rounded-full shadow-sm" 
                />
              </div>
              <span className={`text-[12px] font-bold transition-colors ${isCitationsEnabled ? 'text-[var(--brand-red)]' : 'text-gray-400'}`}>Citation</span>
            </div>

            <button
              onClick={handleSubmit}
              disabled={!text.trim() || disabled}
              className={`w-9 h-9 rounded-[14px] flex items-center justify-center transition-all active:scale-95 ${
                text.trim() && !disabled 
                ? 'bg-red-600 text-white shadow-lg shadow-red-500/10 hover:scale-105' 
                : 'bg-gray-100 text-gray-300 cursor-not-allowed'
              }`}
            >
              <Send size={18} strokeWidth={2.5} />
            </button>
          </div>
        </div>
      </div>

    </div>
  );
};

export default ChatInput;
