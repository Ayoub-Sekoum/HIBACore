import React from 'react';
import Sidebar from './Sidebar';

interface AppShellProps {
  children: React.ReactNode;
}

const AppShell: React.FC<AppShellProps> = ({ children }) => {
  return (
    <div className="h-[100dvh] flex items-center justify-center font-sans bg-[var(--apple-bg)] p-0 md:p-8">
      <div className="w-full h-full md:max-h-[90vh] md:rounded-[24px] shadow-[0_20px_60px_-15px_rgba(0,0,0,0.05)] overflow-hidden flex border-0 md:border relative bg-[var(--wrapper-bg)] border-[var(--border-light)]">
        {/* Sidebar Expansion */}
        <Sidebar />

        {/* Main Workspace */}
        <main className="flex-1 flex flex-col h-full relative overflow-hidden bg-[var(--wrapper-bg)]">
          {children}
        </main>
      </div>

      {/* Global Bottom Credit */}
      <div className="fixed bottom-3 left-0 w-full flex justify-center pointer-events-none z-50">
        <p className="text-[10px] tracking-widest uppercase font-semibold text-[var(--apple-text-muted)] opacity-60">
          © 2026 METEORA ENTERPRISE SOLUTIONS • v0.0.14
        </p>
      </div>
    </div>
  );
};

export default AppShell;
