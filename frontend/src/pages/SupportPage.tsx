import React from 'react';
import { LifeBuoy, Mail, MessageSquare, BookOpen, ExternalLink, ShieldCheck } from 'lucide-react';

const SupportPage: React.FC = () => {
    return (
        <div className="flex-1 flex flex-col p-8 bg-[var(--apple-bg-light)] overflow-y-auto min-h-screen font-sans">
            <div className="max-w-6xl mx-auto w-full">
                <div className="flex items-center justify-between mb-8">
                    <div className="flex flex-col">
                        <h1 className="text-4xl font-extrabold tracking-tight text-[var(--apple-text)]">Support Center</h1>
                        <p className="text-[var(--apple-text-muted)] text-lg mt-1">Siamo qui per aiutarti :)</p>
                    </div>
                </div>

                {/* Grid of Support Options */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
                    {[
                        { title: 'Chat Live', desc: 'Parla ora con un assistente HOBA', icon: <MessageSquare className="text-blue-500" />, action: 'Avvia Chat' },
                        { title: 'Email Support', desc: 'Risposta garantita entro 24 ore', icon: <Mail className="text-purple-500" />, action: 'Invia Email' },
                        { title: 'Documentazione', desc: 'Esplora le guide e le API', icon: <BookOpen className="text-orange-500" />, action: 'Vai ai Docs' },
                    ].map((item, idx) => (
                        <div key={idx} className="bg-white p-8 rounded-[32px] border border-[var(--border-light)] shadow-sm hover:shadow-xl transition-all group flex flex-col items-center text-center">
                            <div className="w-16 h-16 rounded-[22px] bg-gray-50 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                                {item.icon && React.cloneElement(item.icon as React.ReactElement, { size: 32 })}
                            </div>
                            <h3 className="text-xl font-bold text-[var(--apple-text)] mb-3">{item.title}</h3>
                            <p className="text-[var(--apple-text-muted)] mb-6">{item.desc}</p>
                            <button className="px-6 py-2.5 rounded-full bg-gray-100 font-bold text-sm text-[var(--apple-text)] hover:bg-[var(--apple-text)] hover:text-white transition-all">
                                {item.action}
                            </button>
                        </div>
                    ))}
                </div>

                {/* FAQ Section Style */}
                <div className="bg-white p-10 rounded-[40px] border border-[var(--border-light)]">
                    <h2 className="text-2xl font-bold mb-8 flex items-center gap-3">
                        <ShieldCheck size={28} className="text-red-500" /> FAQ e Sicurezza
                    </h2>
                    <div className="space-y-6">
                        {[
                            'Come vengono gestiti i miei dati?',
                            'Posso collegare il mio CRM?',
                            'Cosa succede se l\'agente risponde male?',
                        ].map((q, idx) => (
                            <div key={idx} className="flex items-center justify-between py-4 border-b border-[var(--border-light)] group cursor-pointer">
                                <span className="font-semibold text-[var(--apple-text)] group-hover:text-red-500 transition-colors">{q}</span>
                                <ExternalLink size={18} className="text-gray-300 opacity-0 group-hover:opacity-100 transition-opacity" />
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SupportPage;
