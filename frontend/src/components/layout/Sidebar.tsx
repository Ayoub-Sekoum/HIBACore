import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useChatStore } from '../../store/chatStore';
import SkillHub from '../chat/SkillHub';
import { 
  Home, 
  History as HistoryIcon, 
  Folder, 
  LifeBuoy,
  Settings,
  ChevronLeft,
  Cpu,
  Search,
  Plus,
  ShieldCheck,
  FileText,
  LogOut
} from 'lucide-react';
import { useMsal } from "@azure/msal-react";
import { useAuthStore } from '../../store/authStore';
import { chatService } from '../../services/chatService';
import SettingsModal from '../chat/SettingsModal';

interface SidebarItemProps {
  icon: React.ReactNode;
  label: string;
  active?: boolean;
  onClick?: () => void;
  badge?: string | number;
}

const SidebarItem: React.FC<SidebarItemProps> = ({ icon, label, active, onClick, badge }) => (
  <button 
    onClick={onClick}
    className={`h-11 rounded-[14px] flex items-center px-4 gap-3 w-full font-medium transition-all active:scale-95 group ${
      active 
      ? 'bg-[var(--apple-bg)] text-[var(--apple-text)] shadow-sm' 
      : 'text-[var(--apple-text-muted)] hover:text-[var(--apple-text)] hover:bg-gray-50'
    }`}
  >
    <span className={`transition-colors ${active ? 'text-[var(--brand-red)]' : 'group-hover:text-[var(--brand-red)]'}`}>
      {icon}
    </span>
    <span className="text-[14px]">{label}</span>
    {badge && (
      <div className="ml-auto w-5 h-5 rounded-full bg-red-100 flex items-center justify-center text-[10px] font-bold text-red-600">
        {badge}
      </div>
    )}
  </button>
);

const Sidebar: React.FC = () => {
  const navigate = useNavigate();
  const { instance } = useMsal();
  const { logout: clearAuthStore, user } = useAuthStore();
  const {
    sessions,
    setSessions,
    setCurrentSession,
    currentSessionId,
    setMessages,
    clearChat
  } = useChatStore();
  const [isSkillHubOpen, setIsSkillHubOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  const handleLogout = () => {
    clearAuthStore();
    instance.logoutRedirect({
      postLogoutRedirectUri: window.location.origin,
    });
  };

  useEffect(() => {
    const fetchSessions = async () => {
      try {
        const data = await chatService.getConversations();
        setSessions(data);
      } catch (error) {
        console.error('Failed to fetch sessions:', error);
      }
    };
    fetchSessions();
  }, [setSessions]);

  const handleSelectSession = async (sessionId: string) => {
    try {
      setCurrentSession(sessionId);
      const history = await chatService.getMessages(sessionId);
      setMessages(history);
    } catch (error) {
      console.error('Failed to load session history:', error);
    }
  };

  return (
    <div className="hidden md:flex flex-col items-center py-6 border-r h-full shrink-0 px-4 bg-white border-[var(--border-light)]" style={{ width: '17rem' }}>
      {/* Logo & New Thread*/}
      <div className="w-full flex flex-col gap-6 mb-8 px-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 flex items-center justify-center rounded-[12px] bg-[var(--apple-bg)] shadow-sm">
              <div className="logo-wrapper scale-75">
                <svg className="apple-icon w-8 h-auto" viewBox="0 0 100 85" xmlns="http://www.w3.org/2000/svg">
                  <path className="path-main" d="M50 5 L95 80 L78 80 L50 35 L22 80 L5 80 Z" />
                </svg>
              </div>
            </div>
            <span className="font-bold text-lg text-[var(--apple-text)]">HOBA AI</span>
          </div>
          <button className="p-1.5 rounded-full border transition-colors border-[var(--border-light)] text-[var(--apple-text-muted)] hover:text-[var(--apple-text)] hover:bg-gray-50">
            <ChevronLeft size={16} />
          </button>
        </div>

        <button 
          onClick={clearChat}
          className="w-full flex items-center justify-center gap-2 py-3 bg-[var(--brand-red)] text-white rounded-[16px] font-bold text-sm shadow-lg shadow-red-500/20 hover:scale-[1.02] transition-all active:scale-95"
        >
          <Plus size={18} />
          Nuova Chat
        </button>
      </div>

      {/* Main Navigation*/}
      <div className="flex flex-col gap-1 w-full flex-1 overflow-y-auto scrollbar-none">
        <SidebarItem 
          icon={<Home size={20} />} 
          label="Dashboard" 
          active={!showHistory}
          onClick={() => setShowHistory(false)}
        />
        
        <SidebarItem 
          icon={<Cpu size={20} />} 
          label="Skill Hub" 
          badge={37}
          onClick={() => setIsSkillHubOpen(true)}
        />

        <div className="mt-4">
          <SidebarItem 
            icon={<HistoryIcon size={20} />} 
            label="History" 
            active={showHistory}
            onClick={() => setShowHistory(!showHistory)}
          />
          
          {showHistory && (
            <div className="ml-4 mt-2 space-y-1 mb-4">
              <div className="relative mb-2 px-2">
                <Search size={12} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
                <input 
                  type="text" 
                  placeholder="Cerca chat..."
                  className="w-full bg-gray-50 border-none rounded-lg py-1.5 pl-8 pr-2 text-[11px] outline-none"
                />
              </div>
              <div className="max-h-[300px] overflow-y-auto scrollbar-thin px-2">
                {sessions.length === 0 ? (
                  <div className="text-[11px] text-gray-400 p-2 italic text-center">Nessuna sessione</div>
                ) : (
                  sessions.map((session) => (
                    <div
                      key={session.id}
                      onClick={() => handleSelectSession(session.id)}
                      className={`p-2.5 rounded-xl text-[12px] cursor-pointer transition-all truncate border border-transparent mb-1 ${
                        currentSessionId === session.id 
                        ? 'bg-red-50 text-[var(--brand-red)] font-semibold border-red-100' 
                        : 'text-gray-500 hover:bg-gray-50'
                      }`}
                    >
                      {session.title || 'Nuova Conversazione'}
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        <SidebarItem 
          icon={<Folder size={20} />} 
          label="Documents" 
          onClick={() => navigate('/documents')}
        />
        <SidebarItem 
          icon={<LifeBuoy size={20} />} 
          label="Support" 
          onClick={() => navigate('/support')}
        />

        {/* Administration Section*/}
        <div className="mt-8 mb-2 px-4">
          <p className="text-[10px] font-bold text-[var(--apple-text-muted)] uppercase tracking-widest opacity-50">Administration</p>
        </div>
        
        <SidebarItem 
          icon={<Settings size={20} />} 
          label="Tenant Admin" 
          onClick={() => navigate('/admin')}
        />
        
        <SidebarItem 
          icon={<ShieldCheck size={20} />} 
          label="Super Admin" 
          onClick={() => navigate('/internal/super-admin')}
        />

        <SidebarItem 
          icon={<Cpu size={20} />} 
          label="Agente" 
          onClick={() => navigate('/agent/zeroclaw')}
        />
      </div>

      {/* Bottom Actions*/}
      <div className="w-full pt-4 mt-4 border-t border-[var(--border-light)] flex flex-col gap-2">
        <SidebarItem 
          icon={<Settings size={20} />} 
          label="Settings" 
          onClick={() => setIsSettingsOpen(true)}
        />

        {/* Legal & Support Links*/}
        <div className="flex flex-col gap-1 mt-1 border-b border-[var(--border-light)] pb-3 mb-2">
          <button 
            onClick={() => navigate('/legal')}
            className="flex items-center gap-2 px-4 py-1.5 text-[11px] font-medium text-[var(--apple-text)] hover:text-[var(--brand-red)] transition-colors"
          >
            <ShieldCheck size={14} />
            <span>Privacy Policy</span>
          </button>
          <button 
            onClick={() => navigate('/legal')}
            className="flex items-center gap-2 px-4 py-1.5 text-[11px] font-medium text-[var(--apple-text)] hover:text-[var(--brand-red)] transition-colors"
          >
            <FileText size={14} />
            <span>Terms of Service</span>
          </button>
          <button 
            onClick={() => navigate('/support')}
            className="flex items-center gap-2 px-4 py-2 text-[11px] font-bold text-white bg-[var(--apple-text)] hover:bg-black transition-all rounded-xl mx-2 shadow-sm"
          >
            <LifeBuoy size={14} />
            <span>Need Help?</span>
          </button>
        </div>
        
        <SidebarItem 
          icon={<LogOut size={20} />} 
          label="Logout" 
          onClick={handleLogout}
        />

        {/* Profile Card*/}
        <div className="w-full flex items-center gap-3 p-2.5 rounded-[18px] border border-gray-100 transition-colors hover:bg-gray-50 cursor-pointer mt-2 bg-white">
          <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-red-500 to-orange-400 overflow-hidden shadow-sm flex items-center justify-center text-white font-bold text-xs uppercase">
            {user?.name?.substring(0, 2) || 'US'}
          </div>
          <div className="flex flex-col overflow-hidden">
            <span className="text-[13px] font-bold truncate text-[var(--apple-text)]">{user?.name || 'User'}</span>
            <span className="text-[10px] text-red-500 font-bold uppercase tracking-wider">Premium</span>
          </div>
        </div>
      </div>

      <SkillHub isOpen={isSkillHubOpen} onClose={() => setIsSkillHubOpen(false)} />
      <SettingsModal isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />
    </div>
  );
};

export default Sidebar;
