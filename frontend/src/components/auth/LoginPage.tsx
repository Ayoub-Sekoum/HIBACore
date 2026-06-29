import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTeams } from '../../context/TeamsContext';
import { useMsal } from "@azure/msal-react";
import { loginRequest } from "../../config/msalConfig";
import * as microsoftTeams from "@microsoft/teams-js";
import { Moon, Sun, X } from 'lucide-react';

const LoginPage: React.FC = () => {
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [showHelp, setShowHelp] = useState(false);
    const { inTeams } = useTeams();
    const { instance } = useMsal();
    const [theme, setTheme] = useState<'light' | 'dark'>(() => 
        (localStorage.getItem('meteora-theme') as 'light' | 'dark') || 'light'
    );

    const toggleTheme = () => {
        const newTheme = theme === 'light' ? 'dark' : 'light';
        setTheme(newTheme);
        localStorage.setItem('meteora-theme', newTheme);
        document.documentElement.classList.toggle('dark');
    };

    const handleLogin = async () => {
        setIsLoading(true);
        setError(null);
        
        try {
            if (inTeams) {
                // Teams silent/popup login
                await microsoftTeams.authentication.authenticate({
                    url: window.location.origin + "/auth-start.html",
                    width: 600,
                    height: 535
                });
            } else {
                // Standard MSAL Popup (more resilient for debugging)
                await instance.loginPopup(loginRequest);
                window.location.reload(); // Refresh to trigger auth state
            }
        } catch (e: any) {
            console.error("Login failed:", e);
            setError(e.message || "Authentication failed. Please try again.");
            setIsLoading(false);
        }
    };

    return (
        <div className={`min-h-screen transition-colors duration-300 ${theme === 'dark' ? 'dark bg-black' : 'bg-[#f5f5f7]'} flex items-center justify-center p-0 overflow-hidden font-sans`}>
            
            {/* Theme Toggle */}
            <button 
                onClick={toggleTheme}
                className="absolute top-8 right-8 w-11 h-11 rounded-full flex items-center justify-center glass-effect z-50 transition-transform active:scale-95"
            >
                {theme === 'light' ? <Moon size={20} className="text-[#1d1d1f]" /> : <Sun size={20} className="text-[#f5f5f7]" />}
            </button>

            {/* Background Mountain SVG */}
            <div className="absolute inset-0 z-0 flex items-end pointer-events-none">
                <svg viewBox="0 0 1000 400" preserveAspectRatio="xMidYMax slice" className="w-full h-full opacity-100 transition-all duration-700">
                    <rect width="1000" height="400" fill={theme === 'dark' ? '#111' : '#f5f5f7'} />
                    
                    {/* Base Scura della Montagna */}
                    <path d="M 0 350 L 60 320 L 120 340 L 200 310 L 270 280 L 320 220 L 360 170 L 390 190 L 420 210 L 470 120 L 520 180 L 580 40 L 620 90 L 650 140 L 720 130 L 800 200 L 880 230 L 950 280 L 1050 290 L 1200 300 L 1200 400 L 0 400 Z" fill={theme === 'dark' ? '#0a0a0c' : '#242831'} />

                    {/* Dettagli Picco Sinistro */}
                    <polygon points="360,170 320,220 340,230 310,270 350,250 365,280 380,230" fill={theme === 'dark' ? '#1a1c22' : '#9096a1'} />
                    <polygon points="360,170 380,230 365,280 380,290 410,240 390,190" fill={theme === 'dark' ? '#2a2f3a' : '#d3d7df'} />

                    {/* PICCHI ILLUMINATI con Classe Sunrise */}
                    <g className="sunrise-sweep">
                        <polygon points="470,120 430,160 450,170 410,220 440,230 470,180" fill="#ff525c" />
                        <polygon points="470,120 470,180 440,230 480,250 520,180" fill="#d33e48" />
                        <polygon points="580,40 530,110 550,130 510,180 550,200 570,140 590,160" fill="#ff525c" />
                        <polygon points="580,40 590,160 570,140 550,200 600,280 630,200 610,110 620,90" fill="#d33e48" />
                        <polygon points="570,140 550,200 570,250 590,180" fill="#9f2b35" />
                        <polygon points="580,40 610,80 590,100" fill="#ff7a82" />
                    </g>
                </svg>
            </div>

            {/* Login Card */}
            <motion.div 
                initial={{ opacity: 0, y: 20, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                className={`w-full max-w-[380px] glass-effect rounded-[24px] p-10 z-10 relative flex flex-col items-center text-center shadow-[0_20px_40px_rgba(0,0,0,0.03)] ${error ? 'shake-animation border-red-500/30' : ''}`}
            >
                {/* Logo Area */}
                <svg className="w-12 h-auto mb-6" viewBox="0 0 100 85">
                    <path className="path-main" d="M50 5 L95 80 L78 80 L50 35 L22 80 L5 80 Z" />
                </svg>
                
                <h3 className="text-2xl font-bold mb-2 text-[var(--apple-text)] transition-colors">Welcome to HOBA</h3>
                <p className="text-[14px] mb-8 text-[var(--apple-text-muted)] font-medium transition-colors">Sign in to your enterprise workspace</p>
                
                <AnimatePresence>
                    {error && (
                        <motion.p 
                            initial={{ opacity: 0, y: -5 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="text-[#ff3b30] text-[13px] font-semibold mb-4"
                        >
                            {error}
                        </motion.p>
                    )}
                </AnimatePresence>

                <button 
                    onClick={handleLogin}
                    disabled={isLoading}
                    className="w-full h-[52px] bg-[var(--btn-bg)] text-[var(--btn-text)] rounded-full flex items-center justify-center gap-3 font-semibold text-[15px] shadow-[0_4px_12px_rgba(0,0,0,0.05),inset_0_0_0_1px_var(--border-light)] hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-70 group"
                >
                    {isLoading ? (
                        <div className="w-5 h-5 border-2 border-gray-100 border-t-[var(--brand-red)] rounded-full animate-spin"></div>
                    ) : (
                        <>
                            <svg className="w-5 h-5 transition-transform group-hover:scale-110" viewBox="0 0 21 21">
                                <rect x="1" y="1" width="9" height="9" fill="#f25022"/>
                                <rect x="11" y="1" width="9" height="9" fill="#7fba00"/>
                                <rect x="1" y="11" width="9" height="9" fill="#00a4ef"/>
                                <rect x="11" y="11" width="9" height="9" fill="#ffb900"/>
                            </svg>
                            {inTeams ? "Sign in with Teams" : "Sign in with Microsoft"}
                        </>
                    )}
                </button>

                {/* Footer Links */}
                <div className="mt-10 flex flex-wrap justify-center gap-x-6 gap-y-2">
                    <button className="text-[11px] font-bold uppercase tracking-widest text-[var(--apple-text)] hover:text-[var(--brand-red)] transition-colors">Privacy</button>
                    <button className="text-[11px] font-bold uppercase tracking-widest text-[var(--apple-text)] hover:text-[var(--brand-red)] transition-colors">Terms</button>
                    <button 
                        onClick={() => setShowHelp(true)}
                        className="text-[11px] font-bold uppercase tracking-widest text-[var(--apple-text)] hover:text-[var(--brand-red)] transition-colors inline-flex items-center gap-1"
                    >
                        Need Help?
                    </button>
                </div>
            </motion.div>

            {/* Version Badge */}
            <div className="absolute bottom-6 left-0 w-full flex justify-center pointer-events-none">
                <p className="text-[10px] tracking-[0.25em] font-extrabold text-[var(--apple-text-muted)] opacity-30 uppercase">© 2026 HOBA AI ENTERPRISE • v1.0.0</p>
            </div>

            {/* Help Modal Placeholder */}
            {showHelp && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
                    <div className="absolute inset-0 bg-black/40 backdrop-blur-md" onClick={() => setShowHelp(false)}></div>
                    <motion.div 
                        initial={{ scale: 0.9, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        className="relative w-full max-w-md bg-[var(--modal-bg)] backdrop-blur-3xl border border-[var(--apple-card-border)] rounded-[24px] p-8 shadow-2xl"
                    >
                        <button onClick={() => setShowHelp(false)} className="absolute top-6 right-6 p-2 rounded-full bg-black/5 hover:bg-black/10 transition-colors">
                            <X size={18} />
                        </button>
                        <h4 className="text-xl font-bold mb-2">Support Ticket</h4>
                        <p className="text-sm text-[var(--apple-text-muted)] mb-6">Our team will respond within 24 hours.</p>
                        <div className="space-y-4">
                            <input type="text" placeholder="Corporate Email" className="w-full h-12 bg-black/5 border border-[var(--border-light)] rounded-xl px-4 outline-none focus:border-[var(--brand-red)] transition-colors" />
                            <textarea placeholder="Describe your issue..." className="w-full h-32 bg-black/5 border border-[var(--border-light)] rounded-xl p-4 outline-none focus:border-[var(--brand-red)] transition-colors resize-none"></textarea>
                            <button className="w-full h-[52px] bg-[var(--brand-red)] text-white rounded-full font-bold transition-all hover:scale-[1.02] active:scale-[0.98]">Submit Request</button>
                        </div>
                    </motion.div>
                </div>
            )}
        </div>
    );
};

export default LoginPage;
