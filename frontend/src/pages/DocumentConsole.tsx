import React from 'react';
import { FileText, Search, Plus, Filter, LayoutGrid, List } from 'lucide-react';

const DocumentConsole: React.FC = () => {
    return (
        <div className="flex-1 flex flex-col p-8 bg-[var(--apple-bg-light)] overflow-y-auto min-h-screen">
            <div className="max-w-6xl mx-auto w-full">
                <div className="flex items-center justify-between mb-8">
                    <div className="flex flex-col">
                        <h1 className="text-3xl font-bold tracking-tight text-[var(--apple-text)]">Knowledge Base</h1>
                        <p className="text-[var(--apple-text-muted)] mt-1">Gestisci i documenti e le memorie dell'agente</p>
                    </div>
                    <div className="flex gap-3">
                        <button className="h-10 px-4 rounded-xl bg-[var(--brand-red)] text-white font-bold text-sm shadow-lg shadow-red-500/20 flex items-center gap-2 active:scale-95 transition-all">
                            <Plus size={18} /> Carica File
                        </button>
                    </div>
                </div>

                {/* Search & Filters*/}
                <div className="flex items-center gap-4 mb-6">
                    <div className="relative flex-1">
                        <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
                        <input 
                            type="text" 
                            placeholder="Cerca tra i documenti..."
                            className="w-full bg-white border border-[var(--border-light)] rounded-[16px] py-3 pl-12 pr-4 text-sm focus:ring-2 focus:ring-red-100 outline-none transition-all"
                        />
                    </div>
                    <button className="h-12 w-12 flex items-center justify-center rounded-[16px] bg-white border border-[var(--border-light)] hover:shadow-md transition-all text-gray-500">
                        <Filter size={20} />
                    </button>
                    <div className="flex items-center bg-gray-100 p-1 rounded-xl">
                        <button className="p-2 rounded-lg bg-white shadow-sm text-red-500"><LayoutGrid size={18} /></button>
                        <button className="p-2 rounded-lg text-gray-400"><List size={18} /></button>
                    </div>
                </div>

                {/* Documents Grid*/}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {[
                        { name: 'Policy Aziendale v2.pdf', type: 'PDF', size: '1.2MB', date: '2 h fa' },
                        { name: 'Schema Database.sql', type: 'CODE', size: '45KB', date: 'Ieri' },
                        { name: 'Contratto Meteora.docx', type: 'DOCX', size: '250KB', date: '3 gg fa' },
                        { name: 'Logo HOBA (Vector).svg', type: 'SVG', size: '15KB', date: '1 settimana fa' },
                    ].map((doc, idx) => (
                        <div key={idx} className="bg-white p-5 rounded-[22px] border border-[var(--border-light)] shadow-sm hover:shadow-xl transition-all group cursor-pointer">
                            <div className="w-12 h-12 rounded-[14px] bg-gray-50 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                                <FileText className="text-red-500" />
                            </div>
                            <h3 className="font-bold text-[var(--apple-text)] truncate">{doc.name}</h3>
                            <div className="flex items-center gap-3 mt-3">
                                <span className="text-[10px] font-bold uppercase tracking-wider text-red-500 bg-red-50 px-2 py-0.5 rounded-md">{doc.type}</span>
                                <span className="text-[11px] text-[var(--apple-text-muted)]">{doc.size}</span>
                                <span className="text-[11px] text-[var(--apple-text-muted)]">| {doc.date}</span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default DocumentConsole;
