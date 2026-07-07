import React, { useState, useEffect } from 'react';
import { Cpu, Terminal, Play, BarChart3, Clock, Wifi, WifiOff } from 'lucide-react';
// @ts-ignore
import { apiFetch } from '../services/api';

interface AgentStatus {
  status: 'online' | 'offline';
  detail: Record<string, unknown>;
}

const ZeroClawConsole: React.FC = () => {
  const [agentStatus, setAgentStatus] = useState<AgentStatus | null>(null);
  const [prompt, setPrompt] = useState('');
  const [logs, setLogs] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [showSplash, setShowSplash] = useState(true);
  const [activeSkill, setActiveSkill] = useState<string | null>(null);

  // Splash times out
  useEffect(() => {
    const timer = setTimeout(() => setShowSplash(false), 2800);
    return () => clearTimeout(timer);
  }, []);

  // Polling status every 10 seconds
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const data = await apiFetch<AgentStatus>('/api/v1/agent/status', { method: 'GET' });
        setAgentStatus(data);
      } catch {
        setAgentStatus({ status: 'offline', detail: {} });
      }
    };
    fetchStatus();
    const interval = setInterval(fetchStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleRun = async () => {
    if (!prompt.trim()) return;
    setLoading(true);
    setActiveSkill('Neural Processing');
    const ts = new Date().toLocaleTimeString();
    setLogs(prev => [...prev, `[${ts}] → ${prompt}`]);
    try {
      const data = await apiFetch<any>('/api/v1/agent/run', { 
        method: 'POST',
        body: JSON.stringify({ prompt })
      });
      const reply = data?.response || JSON.stringify(data);
      setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ← ${reply}`]);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Errore sconosciuto';
      setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ERROR: ${msg}`]);
    } finally {
      setLoading(false);
      setActiveSkill(null);
      setPrompt('');
    }
  };

  const isOnline = agentStatus?.status === 'online';

  if (showSplash) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-black overflow-hidden relative">
        <div className="absolute inset-0 bg-radial-gradient from-red-600/20 to-transparent opacity-30 animate-pulse" />
        <div className="relative flex flex-col items-center scale-110">
            {/* Spinning Neural Core*/}
            <div className="relative w-32 h-32 mb-12">
                <div className="absolute inset-0 rounded-[40px] border-4 border-red-600/20 animate-[spin_8s_linear_infinite]" />
                <div className="absolute inset-4 rounded-[30px] border-4 border-orange-500/20 animate-[spin_4s_linear_infinite_reverse]" />
                <div className="absolute inset-0 flex items-center justify-center">
                    <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-red-600 to-orange-500 shadow-[0_0_60px_rgba(220,38,38,0.8)] flex items-center justify-center animate-bounce">
                        <Cpu size={32} className="text-white" />
                    </div>
                </div>
            </div>
            <h2 className="text-4xl font-black text-white tracking-[0.3em] bg-clip-text">HOBA AGENT</h2>
            <div className="h-[2px] w-48 bg-gray-900 mt-8 relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-red-600 to-transparent animate-[scan_2s_linear_infinite]" />
            </div>
            <p className="text-red-500/60 text-[10px] mt-6 font-mono uppercase tracking-[0.5em] animate-pulse">Establishing Secure Neural Link...</p>
        </div>
        <style>{`
            @keyframes scan {
                0% { transform: translateX(-100%); }
                100% { transform: translateX(100%); }
            }
        `}</style>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col p-8 overflow-y-auto min-h-screen bg-[var(--apple-bg-light)] animate-in fade-in zoom-in-95 duration-1000">
      <div className="max-w-6xl mx-auto w-full space-y-12">
        <div className="flex items-end justify-between border-b border-gray-200 pb-10">
          <div className="relative">
            <div className="flex items-center gap-4 mb-3">
               <span className="px-3 py-1 bg-red-100 text-red-600 text-[10px] font-black rounded-full tracking-widest uppercase">Autonomous</span>
               <span className="text-gray-300">/</span>
               <span className="text-[var(--apple-text-muted)] text-[10px] font-bold tracking-widest uppercase">v0.5.1 Official</span>
            </div>
            <h1 className="text-6xl font-black tracking-tighter text-[var(--apple-text)] leading-none">
               Agente <span className="text-red-600">HOBA</span>
            </h1>
            <p className="text-[var(--apple-text-muted)] mt-4 text-xl font-medium max-w-xl leading-relaxed">
              Il gateway ufficiale ZeroClaw integrato in HOBA. Esegue task complessi, gestisce file e interagisce con le API.
            </p>
          </div>
          <div className={`group flex flex-col items-end gap-3 px-8 py-5 rounded-[32px] transition-all duration-500 hover:scale-105 ${
            isOnline 
            ? 'bg-white shadow-2xl shadow-green-500/10 border-2 border-green-50' 
            : 'bg-white border-2 border-red-50 opacity-50 grayscale'
          }`}>
            <span className={`text-[10px] font-black tracking-widest uppercase ${isOnline ? 'text-green-500' : 'text-red-500'}`}>Status Link</span>
            <div className="flex items-center gap-3">
                <div className={`w-3 h-3 rounded-full ${isOnline ? 'bg-green-500 shadow-[0_0_15px_#22c55e]' : 'bg-red-500'} animate-pulse`} />
                <span className="text-2xl font-black lowercase tracking-tighter">{isOnline ? 'online' : 'unreachable'}</span>
            </div>
          </div>
        </div>

        {/* Neural Skills Visualization*/}
        <div className="space-y-6">
            <div className="flex items-center gap-3 px-2">
                <Terminal size={14} className="text-red-600" />
                <h3 className="text-xs font-black uppercase tracking-[0.2em] text-gray-400">Integrated Neural Skills</h3>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                {[
                    { id: 'vision', label: 'Vision AI', active: true, color: 'from-blue-500 to-cyan-400' },
                    { id: 'memory', label: 'MCP Memory', active: true, color: 'from-purple-600 to-indigo-500' },
                    { id: 'voice', label: 'VoiceLive', active: false, color: 'from-green-500 to-emerald-400' },
                    { id: 'safety', label: 'Safety Net', active: true, color: 'from-orange-500 to-red-400' },
                    { id: 'search', label: 'Web Search', active: true, color: 'from-pink-500 to-rose-400' },
                    { id: 'code', label: 'Executor', active: true, color: 'from-gray-700 to-gray-900' },
                ].map((skill) => (
                    <div key={skill.id} className={`p-4 rounded-[24px] border border-gray-100 bg-white transition-all hover:-translate-y-1 hover:shadow-xl group cursor-help ${!skill.active && 'opacity-30'}`}>
                        <div className={`w-10 h-10 rounded-xl bg-gradient-to-tr ${skill.color} mb-3 flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform`}>
                            <div className="w-4 h-4 rounded-full border-2 border-white/30" />
                        </div>
                        <div className="text-[11px] font-bold text-gray-800">{skill.label}</div>
                        <div className="text-[9px] text-gray-400 mt-1 uppercase tracking-tighter">{skill.active ? 'Ready' : 'Locked'}</div>
                    </div>
                ))}
            </div>
        </div>

        {/* Action Command Center - High Tech Version*/}
        <div className="bg-[#111] rounded-[48px] p-10 shadow-[0_40px_100px_rgba(0,0,0,0.3)] relative overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-tr from-red-600/10 via-transparent to-transparent pointer-events-none" />
          <div className="flex flex-col gap-8 relative z-10">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <div className="w-1.5 h-6 bg-red-600 rounded-full" />
                    <span className="font-mono text-[10px] text-gray-500 uppercase tracking-[0.3em]">Direct Neural Input</span>
                </div>
                {activeSkill && <div className="text-red-500 text-[10px] font-black animate-pulse uppercase tracking-widest">{activeSkill}...</div>}
            </div>
            <div className="flex gap-4 p-2 bg-white/5 rounded-[40px] focus-within:bg-white/10 transition-all border border-white/5">
              <input
                value={prompt}
                onChange={e => setPrompt(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleRun()}
                placeholder="Inserisci un comando (es: 'Analizza il repo', 'Esegui il build')..."
                className="flex-1 bg-transparent border-none rounded-full px-8 py-6 text-xl font-medium text-white outline-none placeholder:text-white/20"
              />
              <button
                onClick={handleRun}
                disabled={loading || !isOnline}
                className="h-[76px] px-12 rounded-[34px] bg-red-600 text-white font-black text-lg shadow-2xl hover:bg-red-500 hover:scale-105 active:scale-95 transition-all disabled:opacity-20 flex items-center gap-4"
              >
                {loading ? <div className="w-6 h-6 border-4 border-white/30 border-t-white rounded-full animate-spin" /> : <Play fill="white" size={24} />}
                {loading ? 'PROCESSING' : 'INITIATE'}
              </button>
            </div>
          </div>
        </div>

        {/* Real-time Telemetry Log - Full Terminal*/}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 h-[600px]">
            <div className="lg:col-span-2 bg-black rounded-[48px] border border-white/10 flex flex-col overflow-hidden shadow-2xl">
                <div className="flex items-center justify-between px-8 py-6 border-b border-white/5 bg-gray-900/40">
                    <div className="flex items-center gap-4">
                        <Terminal size={16} className="text-gray-600" />
                        <span className="text-[10px] font-mono text-gray-500 uppercase tracking-[0.2em]">Neural Logs | Sweden Central</span>
                    </div>
                </div>
                <div className="flex-1 p-8 font-mono text-[14px] overflow-y-auto space-y-4 custom-scrollbar bg-[radial-gradient(circle_at_50%_0%,#111_0%,#000_100%)]">
                    {logs.length === 0
                        ? <div className="flex flex-col items-center justify-center h-full opacity-20 filter grayscale">
                            <Cpu size={48} className="mb-4" />
                            <div className="text-sm tracking-widest">NO TELEMETRY DETECTED</div>
                          </div>
                        : logs.map((l, i) => (
                            <div key={i} className={`group animate-in slide-in-from-left-4 duration-500 ${l.includes('→') ? 'text-white' : 'text-green-400'}`}>
                                <div className="flex items-start gap-4">
                                    <span className="text-[10px] opacity-30 mt-1">{new Date().toLocaleTimeString()}</span>
                                    <div className={`p-4 rounded-2xl ${l.includes('→') ? 'bg-white/5' : 'bg-green-500/5 border border-green-500/10'}`}>
                                        <span className="font-bold mr-2 text-xs opacity-50">{l.includes('→') ? 'USR>' : 'SYS>'}</span>
                                        {l}
                                    </div>
                                </div>
                            </div>
                        ))
                    }
                    <div id="log-end" />
                </div>
            </div>

            {/* Side Status Panel*/}
            <div className="space-y-6">
                <div className="bg-white rounded-[40px] p-8 border border-gray-100 shadow-xl overflow-hidden relative">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/5 blur-3xl" />
                    <h3 className="text-[10px] font-black uppercase text-gray-400 tracking-widest mb-6">Device Params</h3>
                    <div className="space-y-6">
                        {[
                            { label: 'Latency', value: isOnline ? '8ms' : '--', trend: 'down', color: 'text-green-500' },
                            { label: 'Neural Load', value: isOnline ? '1.2%' : '0%', trend: 'up', color: 'text-gray-800' },
                            { label: 'Context', value: '128k', trend: 'even', color: 'text-gray-800' },
                        ].map((m) => (
                            <div key={m.label} className="flex items-center justify-between">
                                <span className="text-sm font-medium text-gray-500">{m.label}</span>
                                <span className={`text-xl font-black ${m.color}`}>{m.value}</span>
                            </div>
                        ))}
                    </div>
                </div>
                <div className="bg-gradient-to-br from-red-600 to-orange-500 rounded-[40px] p-8 text-white shadow-2xl relative overflow-hidden group">
                    <div className="absolute -right-10 -bottom-10 w-40 h-40 bg-white/10 rounded-full group-hover:scale-150 transition-transform duration-700" />
                    <h3 className="text-[10px] font-black uppercase text-white/60 tracking-widest mb-4">Neural Gateway</h3>
                    <p className="text-2xl font-black leading-tight mb-4">Pronto per il Go-Live.</p>
                    <button className="px-6 py-2 bg-white text-red-600 rounded-full font-bold text-xs uppercase tracking-widest shadow-xl">Audit Health</button>
                </div>
            </div>
        </div>
      </div>
    </div>
  );
};

export default ZeroClawConsole;
