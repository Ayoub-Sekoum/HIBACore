import React from 'react';
import { Sparkles } from 'lucide-react';

/**
 * ThinkingBadge
 * Displays the "reasoning" state of the AI ​​(e.g. for o1 or GPT-5 models).
 */
const ThinkingBadge: React.FC = () => {
  return (
    <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-gray-100 rounded-full text-xs font-medium text-gray-500 ai-pulse mb-3">
      <Sparkles className="w-3.5 h-3.5 text-brand-red" />
      <span>L'AI sta ragionando...</span>
    </div>
  );
};

export default ThinkingBadge;
