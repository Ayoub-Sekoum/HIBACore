import React from 'react';
import { motion } from 'framer-motion';
import { useChatStore } from '../../store/chatStore';
import { 
  X, 
  Copy, 
  Download, 
  FileCode, 
  FileText
} from 'lucide-react';

const Canvas: React.FC = () => {
  const { activeArtifact, setActiveArtifact } = useChatStore();

  if (!activeArtifact) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(activeArtifact.content);
    // Could add a toast here
  };

  return (
    <motion.div
      initial={{ x: '100%' }}
      animate={{ x: 0 }}
      exit={{ x: '100%' }}
      transition={{ type: 'spring', damping: 25, stiffness: 200 }}
      className="fixed inset-y-0 right-0 w-full md:w-[50%] lg:w-[45%] bg-white dark:bg-[#1d1d1f] border-l border-gray-100 dark:border-[#333] z-50 shadow-2xl flex flex-col"
    >
      {/* Canvas Header */}
      <div className="h-16 flex items-center justify-between px-6 border-b border-gray-50 dark:border-[#333]">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-red-50 dark:bg-red-950/30 rounded-lg text-red-600">
            {activeArtifact.type === 'code' ? <FileCode size={18} /> : <FileText size={18} />}
          </div>
          <div>
            <h2 className="text-[14px] font-bold text-gray-800 dark:text-gray-100 truncate max-w-[200px]">
              {activeArtifact.filename || 'Senza nome'}
            </h2>
            <p className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">
              Artifact {activeArtifact.type}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button 
            onClick={handleCopy}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-[#2d2d2f] text-gray-500 transition-colors" 
            title="Copia"
          >
            <Copy size={16} />
          </button>
          <button className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-[#2d2d2f] text-gray-500 transition-colors" title="Download">
            <Download size={16} />
          </button>
          <div className="w-[1px] h-4 bg-gray-200 dark:bg-[#333] mx-1"></div>
          <button 
            onClick={() => setActiveArtifact(null)}
            className="p-2 rounded-lg hover:bg-red-50 hover:text-red-500 dark:hover:bg-red-950/30 transition-colors"
          >
            <X size={20} />
          </button>
        </div>
      </div>

      {/* Canvas Body */}
      <div className="flex-1 overflow-auto p-6 md:p-10 font-mono text-[13px] leading-relaxed">
        <div className="max-w-4xl mx-auto">
          {activeArtifact.type === 'code' ? (
            <div className="relative group">
               <pre className="bg-gray-50 dark:bg-[#0d0d0f] p-6 rounded-2xl border border-gray-100 dark:border-[#222] overflow-x-auto">
                 <code className="text-gray-800 dark:text-gray-300">
                   {activeArtifact.content}
                 </code>
               </pre>
            </div>
          ) : (
            <div className="prose prose-slate dark:prose-invert max-w-none">
              {activeArtifact.content}
            </div>
          )}
        </div>
      </div>

      {/* Canvas Footer */}
      <div className="p-4 border-t border-gray-50 dark:border-[#333] flex justify-end gap-3 px-6">
        <button className="px-4 py-2 text-[12px] font-bold text-gray-500 hover:text-gray-800 transition-colors">
          Pubblica
        </button>
        <button className="px-4 py-2 bg-red-600 text-white rounded-xl text-[12px] font-bold shadow-sm shadow-red-200 hover:bg-red-700 active:scale-95 transition-all">
          Applica modifiche
        </button>
      </div>
    </motion.div>
  );
};

export default Canvas;
