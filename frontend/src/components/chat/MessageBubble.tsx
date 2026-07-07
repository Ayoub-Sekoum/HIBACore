import React from 'react';
import { Message } from '../../types/chat';
import { motion } from 'framer-motion';
import { 
  Copy, 
  RotateCcw, 
  ThumbsUp, 
  ThumbsDown, 
  ExternalLink,
  ChevronDown,
  BrainCircuit,
  Layout,
  FileCode
} from 'lucide-react';
import { useChatStore } from '../../store/chatStore';

interface MessageBubbleProps {
  message: Message;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === 'user';
  const { setActiveArtifact } = useChatStore();

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      className={`flex w-full mb-8 ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      <div className={`flex max-w-[85%] md:max-w-[80%] gap-4 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        {/* Avatar Area*/}
        <div className="shrink-0 mt-1">
          <div className={`w-9 h-9 rounded-full flex items-center justify-center border shadow-sm ${
            isUser 
            ? 'bg-white border-gray-100' 
            : 'bg-white border-gray-100'
          }`}>
            {isUser ? (
              <img src="https://ui-avatars.com/api/?name=Baki&background=fff&color=E31E24" alt="User" className="w-full h-full rounded-full" />
            ) : (
              <div className="logo-wrapper">
                <svg className="apple-icon w-5 h-auto text-red-600" viewBox="0 0 100 85">
                  <path className="path-main" d="M50 5 L95 80 L78 80 L50 35 L22 80 L5 80 Z" />
                </svg>
              </div>
            )}
          </div>
        </div>

        {/* Content Area*/}
        <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
          <div className={`px-5 py-3.5 rounded-2xl shadow-sm text-[15px] leading-relaxed transition-colors ${
            isUser 
            ? 'bg-red-600 text-white' 
            : 'bg-white border border-gray-100 text-gray-800'
          }`}>
            <div className="prose prose-slate max-w-none prose-sm font-medium">
              {message.content || (message.status === 'streaming' && (
                <span className="flex gap-1 items-center h-5">
                  <span className="w-1.5 h-1.5 bg-red-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                  <span className="w-1.5 h-1.5 bg-red-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                  <span className="w-1.5 h-1.5 bg-red-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                </span>
              ))}
            </div>

            {/* Artifacts Area (Task: Canvas)*/}
            {!isUser && message.artifacts && message.artifacts.length > 0 && (
                <div className="mt-4 flex flex-col gap-2">
                    {message.artifacts.map((art: any, i: number) => (
                        <button 
                            key={i}
                            onClick={() => setActiveArtifact(art)}
                            className="flex items-center gap-3 p-3 rounded-xl border border-gray-100 hover:border-red-200 transition-all bg-gray-50/50 hover:bg-red-50/30 group"
                        >
                            <div className="p-2 bg-white rounded-lg border border-gray-100 text-red-600 shadow-sm transition-transform group-hover:scale-110">
                                <FileCode size={16} />
                            </div>
                            <div className="text-left">
                                <p className="text-[12px] font-bold text-gray-800 truncate max-w-[180px]">
                                    {art.filename || 'Visualizza Artefatto'}
                                </p>
                                <p className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">
                                    Click per aprire nel Canvas
                                </p>
                            </div>
                            <Layout size={14} className="ml-auto text-gray-300 group-hover:text-red-400" />
                        </button>
                    ))}
                </div>
            )}
            
            {/* Reasoning / Thinking section (Task: DeepAgents logs)*/}
            {!isUser && message.reasoning && (
                <div className="mt-3 overflow-hidden border-t border-gray-100">
                    <details className="group">
                        <summary className="flex items-center gap-2 py-2 text-[11px] font-bold text-red-600 cursor-pointer list-none hover:opacity-80 transition-opacity">
                            <BrainCircuit size={14} className="animate-pulse" />
                            <span>Vedi ragionamento dell'agente</span>
                            <ChevronDown size={14} className="group-open:rotate-180 transition-transform ml-auto" />
                        </summary>
                        <div className="pt-1 pb-3 text-[12px] text-gray-500 font-mono whitespace-pre-wrap leading-relaxed opacity-90">
                            {message.reasoning}
                        </div>
                    </details>
                </div>
            )}


            {/* Citations Tag Area*/}
            {!isUser && message.citations && message.citations.length > 0 && (
              <div className="mt-4 pt-3 border-t border-[var(--border-light)] flex flex-wrap gap-2">
                 <p className="w-full text-[10px] font-bold uppercase tracking-wider text-[var(--apple-text-muted)] mb-1">Sources</p>
                {message.citations.map((cite, idx) => (
                  <button 
                    key={cite.id} 
                    className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-[var(--apple-bg)] border border-[var(--border-light)] text-[10px] font-bold text-[var(--apple-text)] hover:border-[var(--brand-red)] hover:text-[var(--brand-red)] transition-all"
                  >
                    <span className="opacity-50">{idx + 1}</span>
                    <span className="truncate max-w-[120px]">{cite.file_name}</span>
                    <ExternalLink size={10} />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Action Bar*/}
          {!isUser && message.content && (
            <div className="flex items-center gap-1 mt-2 px-2">
              <button title="Copy" className="p-1.5 rounded-lg text-gray-400 hover:text-[var(--brand-red)] hover:bg-gray-50 transition-colors">
                <Copy size={14} />
              </button>
              <button title="Regenerate" className="p-1.5 rounded-lg text-gray-400 hover:text-[var(--brand-red)] hover:bg-gray-50 transition-colors">
                <RotateCcw size={14} />
              </button>
              <div className="w-[1px] h-3 bg-gray-200 mx-1"></div>
              <button title="Like" className="p-1.5 rounded-lg text-gray-400 hover:text-emerald-500 hover:bg-gray-50 transition-colors">
                <ThumbsUp size={14} />
              </button>
              <button title="Dislike" className="p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-gray-50 transition-colors">
                <ThumbsDown size={14} />
              </button>
            </div>
          )}
          
          <div className="mt-1.5 px-3">
            <span className="text-[10px] font-semibold text-[var(--apple-text-muted)] opacity-60">
              {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default MessageBubble;
