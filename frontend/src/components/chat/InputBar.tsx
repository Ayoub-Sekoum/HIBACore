import React, { useState } from 'react';
import { Send, Paperclip } from 'lucide-react';

interface InputBarProps {
  onSend: (text: string) => void;
  disabled?: boolean;
}

/**
 * InputBar — Una versione alternativa e più compatta di ChatInput.
 * Design ultra-minimal stile Apple, ideale per integrazioni rapide.
 */
const InputBar: React.FC<InputBarProps> = ({ onSend, disabled }) => {
  const [text, setText] = useState('');

  const handleSend = () => {
    if (text.trim() && !disabled) {
      onSend(text);
      setText('');
    }
  };

  return (
    <div className="flex items-center gap-2 p-1.5 pl-4 bg-white/80 backdrop-blur-xl border border-gray-100 rounded-full shadow-lg shadow-black/5 w-full max-w-2xl mx-auto ring-1 ring-black/5">
      <button className="p-2 text-gray-400 hover:text-gray-600 transition-colors">
        <Paperclip className="w-5 h-5" />
      </button>
      
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && handleSend()}
        placeholder="Scrivi un messaggio..."
        disabled={disabled}
        className="flex-1 bg-transparent border-none outline-none text-[15px] py-2 text-gray-800 placeholder:text-gray-400"
      />
      
      <button
        onClick={handleSend}
        disabled={!text.trim() || disabled}
        className={`p-2 rounded-full transition-all ${
          text.trim() && !disabled 
          ? 'bg-brand-red text-white shadow-md shadow-red-500/20 active:scale-95' 
          : 'bg-gray-100 text-gray-300'
        }`}
      >
        <Send className="w-5 h-5" />
      </button>
    </div>
  );
};

export default InputBar;
