import React from 'react';

interface ProgressBarProps {
  progress: number; // 0-100
  label?: string;
}

/**
 * ProgressBar Component
 * Elegant Apple style to show upload or document processing progress.
 */
const ProgressBar: React.FC<ProgressBarProps> = ({ progress, label }) => {
  return (
    <div className="w-full max-w-xs mb-4">
      {label && (
        <div className="flex justify-between text-xs text-gray-400 mb-1.5 font-medium px-0.5 uppercase tracking-wider">
          <span>{label}</span>
          <span>{Math.round(progress)}%</span>
        </div>
      )}
      <div className="h-1.5 w-full bg-gray-200 rounded-full overflow-hidden">
        <div 
          className="h-full bg-brand-red transition-all duration-500 ease-out" 
          style={{ width: `${progress}%` }} 
        />
      </div>
    </div>
  );
};

export default ProgressBar;
