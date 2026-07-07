import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Save, Shield, Terminal, Settings } from 'lucide-react';
// Removed unused chatService import for now as we use mock save

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose }) => {
  const [systemPrompt, setSystemPrompt] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    let mounted = true;
    if (isOpen && mounted) {
      // Fetch current prompt - assuming an endpoint exists or we use admin service
      // For now, let's simulate fetching
      setTimeout(() => {
        if(mounted) setSystemPrompt("Sei HOBA AI, un assistante avanzato basato su architettura Azure Zero Trust...");
      }, 0);
    }
    return () => { mounted = false; };
  }, [isOpen]);

  const handleSave = async () => {
    setIsLoading(true);
    // Simulate save
    await new Promise(r => setTimeout(r, 1000));
    setIsLoading(false);
    onClose();
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="w-full max-w-2xl bg-white dark:bg-[#1d1d1f] rounded-[24px] shadow-2xl overflow-hidden border border-gray-100 dark:border-[#333]"
          >
            <div className="flex items-center justify-between p-6 border-b border-gray-100 dark:border-[#333]">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-red-50 dark:bg-red-900/20 flex items-center justify-center text-red-600">
                  <Settings size={22} />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-[var(--apple-text)]">Settings</h2>
                  <p className="text-[11px] text-gray-400 font-medium uppercase tracking-wider">Tenant Configuration</p>
                </div>
              </div>
              <button 
                onClick={onClose}
                className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-[#2d2d2f] transition-colors"
              >
                <X size={20} className="text-gray-400" />
              </button>
            </div>

            <div className="p-8 space-y-8">
              {/* System Prompt Section*/}
              <div className="space-y-4">
                <div className="flex items-center gap-2 text-[var(--apple-text)]">
                  <Terminal size={18} className="text-red-500" />
                  <span className="font-bold text-[14px]">System Prompt</span>
                </div>
                <textarea
                  value={systemPrompt}
                  onChange={(e) => setSystemPrompt(e.target.value)}
                  className="w-full h-40 p-4 rounded-2xl bg-gray-50 dark:bg-[#111] border border-gray-100 dark:border-[#333] text-[13px] outline-none focus:ring-2 focus:ring-red-500/20 transition-all resize-none"
                  placeholder="Definisci il comportamento del chatbot..."
                />
                <p className="text-[11px] text-gray-400">
                  Questo prompt definisce l'identità e le regole base di HOBA AI per tutti gli utenti di questo tenant.
                </p>
              </div>

              {/* Security Status*/}
              <div className="p-4 rounded-2xl bg-emerald-50 dark:bg-emerald-900/10 border border-emerald-100 dark:border-emerald-900/20 flex items-center gap-4">
                <div className="w-10 h-10 rounded-full bg-emerald-500 flex items-center justify-center text-white">
                  <Shield size={20} />
                </div>
                <div>
                  <div className="text-[13px] font-bold text-emerald-800 dark:text-emerald-400">Azure Zero Trust Active</div>
                  <div className="text-[11px] text-emerald-600/80">Tutti i dati sono criptati e isolati per tenant.</div>
                </div>
              </div>
            </div>

            <div className="p-6 bg-gray-50 dark:bg-[#151517] flex justify-end gap-3">
              <button 
                onClick={onClose}
                className="px-6 py-2.5 rounded-xl font-bold text-sm text-gray-500 hover:text-gray-900 transition-colors"
              >
                Annulla
              </button>
              <button 
                onClick={handleSave}
                disabled={isLoading}
                className="px-8 py-2.5 rounded-xl bg-black text-white dark:bg-white dark:text-black font-bold text-sm shadow-lg hover:scale-105 transition-all active:scale-95 flex items-center gap-2"
              >
                {isLoading ? 'Salvataggio...' : (
                  <>
                    <Save size={16} />
                    Salva Modifiche
                  </>
                )}
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

export default SettingsModal;
