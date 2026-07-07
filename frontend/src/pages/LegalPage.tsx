import React from 'react';
import { ShieldCheck, FileText, ChevronLeft } from 'lucide-react';

const LegalPage: React.FC = () => {
    return (
        <div className="flex-1 flex flex-col p-8 bg-[var(--apple-bg-light)] overflow-y-auto min-h-screen">
            <div className="max-w-4xl mx-auto w-full">
                <div className="mb-12">
                    <button 
                        onClick={() => window.history.back()}
                        className="flex items-center gap-2 px-4 py-2 rounded-full border border-[var(--border-light)] text-sm font-bold text-[var(--apple-text-muted)] hover:text-[var(--apple-text)] hover:bg-gray-50 transition-all mb-8"
                    >
                        <ChevronLeft size={16} /> Torna indietro
                    </button>
                    <h1 className="text-4xl font-black tracking-tight text-[var(--apple-text)] mb-4">Informazioni Legali</h1>
                    <p className="text-xl text-[var(--apple-text-muted)] leading-relaxed">Le policy e i termini di utilizzo di HOBA AI.</p>
                </div>

                {/* Content Cards*/}
                <div className="space-y-12">
                    <section className="bg-white dark:bg-[#1d1d1f] p-10 rounded-[40px] border border-[var(--border-light)] shadow-sm">
                        <div className="flex items-center gap-4 mb-8">
                            <div className="p-3 rounded-2xl bg-orange-50 text-orange-600"><ShieldCheck size={28} /></div>
                            <h2 className="text-2xl font-bold">Privacy Policy</h2>
                        </div>
                        <div className="prose dark:prose-invert max-w-none text-[var(--apple-text-muted)] leading-relaxed space-y-4">
                            <p>Proteggere i tuoi dati è la nostra missione. HOBA AI utilizza la crittografia end-to-end per ogni messaggio e documento caricato.</p>
                            <h3 className="text-lg font-bold text-[var(--apple-text)]">1. Raccolta Dati</h3>
                            <p>I dati raccolti sono finalizzati esclusivamente al miglioramento delle performance del tuo agente personalizzato. Non vendiamo i dati a terzi.</p>
                            <h3 className="text-lg font-bold text-[var(--apple-text)]">2. Sicurezza Azure</h3>
                            <p>Utilizziamo l'infrastruttura Microsoft Azure North Europe (Svezia e Irlanda) per garantire la massima conformità GDPR.</p>
                        </div>
                    </section>

                    <section className="bg-white dark:bg-[#1d1d1f] p-10 rounded-[40px] border border-[var(--border-light)] shadow-sm">
                        <div className="flex items-center gap-4 mb-8">
                            <div className="p-3 rounded-2xl bg-blue-50 text-blue-600"><FileText size={28} /></div>
                            <h2 className="text-2xl font-bold">Termini di Servizio</h2>
                        </div>
                        <div className="prose dark:prose-invert max-w-none text-[var(--apple-text-muted)] leading-relaxed space-y-4">
                            <p>Utilizzando HOBA AI, accetti i nostri termini. Il servizio è fornito "as is" per scopi di automazione aziendale.</p>
                            <h3 className="text-lg font-bold text-[var(--apple-text)]">Utilizzo Corretto</h3>
                            <p>È vietato l'utilizzo dell'agente per attività illegali o dannose verso l'infrastruttura Azure.</p>
                        </div>
                    </section>
                </div>
            </div>
        </div>
    );
};

export default LegalPage;
