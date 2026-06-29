import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useChatStore } from '../../store/chatStore';
import { chatService } from '../../services/chatService';
import { SkillInfo } from '../../types/chat';
import { X, Search, Cpu, FlaskConical } from 'lucide-react';

interface SkillHubProps {
  isOpen: boolean;
  onClose: () => void;
}

const SkillHub: React.FC<SkillHubProps> = ({ isOpen, onClose }) => {
  const [skills, setSkills] = useState<SkillInfo[]>([]);
  const [search, setSearch] = useState('');
  const { enabledSkillIds, toggleSkill } = useChatStore();

  useEffect(() => {
    if (isOpen) {
      const fetchSkills = async () => {
        try {
          const data = await chatService.getSkills();
          setSkills(data);
        } catch (error) {
          console.error('Failed to fetch skills:', error);
        }
      };
      fetchSkills();
    }
  }, [isOpen]);

  const filteredSkills = skills.filter(s => 
    s.name.toLowerCase().includes(search.toLowerCase()) || 
    s.id.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/40 backdrop-blur-md" 
            onClick={onClose}
          />
          <motion.div 
            initial={{ scale: 0.9, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.9, opacity: 0, y: 20 }}
            className="relative w-full max-w-2xl bg-white dark:bg-[#111] border border-[var(--border-light)] dark:border-[#333] rounded-[28px] shadow-2xl overflow-hidden flex flex-col h-[80vh]"
          >
            {/* Header */}
            <div className="p-6 border-b dark:border-[#333] flex items-center justify-between shrink-0">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-red-600 flex items-center justify-center text-white shadow-lg shadow-red-500/20">
                  <Cpu size={22} />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-[var(--apple-text)]">Skill Hub</h2>
                  <p className="text-[13px] text-[var(--apple-text-muted)] font-medium">{skills.length} Funzioni Rilevate</p>
                </div>
              </div>
              <button 
                onClick={onClose}
                className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-[#222] transition-colors"
              >
                <X size={20} className="text-[var(--apple-text-muted)]" />
              </button>
            </div>

            {/* Search */}
            <div className="px-6 py-4 border-b dark:border-[#333] shrink-0 bg-gray-50/50 dark:bg-[#161618]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
                <input 
                  type="text" 
                  placeholder="Cerca tra le funzioni AI..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full h-11 bg-white dark:bg-[#1d1d1f] border border-[var(--border-light)] dark:border-[#333] rounded-xl pl-10 pr-4 text-sm outline-none focus:border-red-500 transition-colors shadow-sm"
                />
              </div>
            </div>

            {/* Skills List */}
            <div className="flex-1 overflow-y-auto p-4 scrollbar-thin">
              <div className="grid grid-cols-1 gap-2">
                {filteredSkills.map((skill) => {
                  const isEnabled = enabledSkillIds.includes(skill.id);
                  return (
                    <div 
                      key={skill.id}
                      onClick={() => toggleSkill(skill.id)}
                      className={`group flex items-center justify-between p-4 rounded-2xl border transition-all cursor-pointer select-none ${
                        isEnabled 
                        ? 'bg-red-50/50 border-red-200 dark:bg-red-950/10 dark:border-red-900/30' 
                        : 'bg-white border-[var(--border-light)] hover:border-gray-300 dark:bg-[#1d1d1f] dark:border-[#333] dark:hover:border-[#444]'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <div className={`w-10 h-10 rounded-xl flex items-center justify-center transition-colors ${
                          isEnabled ? 'bg-red-600 text-white shadow-md' : 'bg-gray-100 text-gray-400 dark:bg-[#222] dark:text-gray-600'
                        }`}>
                          <FlaskConical size={18} />
                        </div>
                        <div>
                          <h4 className={`text-[14px] font-bold transition-colors ${isEnabled ? 'text-red-700 dark:text-red-400' : 'text-[var(--apple-text)]'}`}>
                            {skill.name}
                          </h4>
                          <p className="text-[11px] text-[var(--apple-text-muted)] leading-tight mt-0.5">
                            {skill.id} • {skill.category || 'System'}
                          </p>
                        </div>
                      </div>
                      
                      <div className={`w-10 h-5 rounded-full flex items-center px-0.5 transition-colors ${isEnabled ? 'bg-red-600' : 'bg-gray-200 dark:bg-gray-800'}`}>
                        <motion.div 
                          animate={{ x: isEnabled ? 20 : 0 }}
                          className="w-4 h-4 bg-white rounded-full shadow-sm" 
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Footer */}
            <div className="p-4 px-6 border-t dark:border-[#333] bg-gray-50/50 dark:bg-[#161618] flex items-center justify-between">
              <span className="text-[12px] text-[var(--apple-text-muted)] font-medium">
                {enabledSkillIds.length} Funzioni Attive
              </span>
              <button 
                onClick={onClose}
                className="px-6 h-10 bg-[var(--apple-text)] text-white dark:bg-white dark:text-black rounded-full text-sm font-bold shadow-sm active:scale-95 transition-all"
              >
                Applica
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

export default SkillHub;
