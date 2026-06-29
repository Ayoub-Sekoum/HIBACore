import React from 'react';
import { MessageSquare, Shield, Zap, FileSearch } from 'lucide-react';

/**
 * WelcomeScreen Component
 * Stile Apple-inspired: pulito, leggero, enfasi sulla tipografia e le icone.
 */
const WelcomeScreen: React.FC = () => {
  const cards = [
    {
      icon: <FileSearch className="w-6 h-6 text-blue-500" />,
      title: "RAG & Documenti",
      description: "Chatta con i tuoi PDF, Word e report aziendali. Cito sempre le fonti."
    },
    {
      icon: <Shield className="w-6 h-6 text-green-500" />,
      title: "Privacy Enterprise",
      description: "I tuoi dati sono isolati a livello tenant e non lasciano mai Azure."
    },
    {
      icon: <Zap className="w-6 h-6 text-orange-500" />,
      title: "Agenti Intelligenti",
      description: "Posso eseguire azioni, leggere file e pianificare task complessi."
    }
  ];

  return (
    <div className="flex flex-col items-center justify-center h-full max-w-2xl mx-auto px-6 text-center animate-reveal">
      <div className="mb-12">
        <div className="w-16 h-16 bg-white rounded-2xl shadow-sm flex items-center justify-center mx-auto mb-6 border border-gray-100 ai-pulse">
            <MessageSquare className="w-8 h-8 text-brand-red" />
        </div>
        <h1 className="text-4xl font-semibold tracking-tight text-gray-900 mb-4">
          Benvenuto in HOBA AI
        </h1>
        <p className="text-xl text-gray-500 max-w-md mx-auto leading-relaxed">
          L'assistente intelligente sicuro per la tua azienda. Chiedimi qualunque cosa sui tuoi documenti.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full">
        {cards.map((card, i) => (
          <div key={i} className="p-6 bg-white/40 backdrop-blur-md rounded-2xl border border-white/60 shadow-sm text-left hover:shadow-md transition-all duration-300">
            <div className="mb-4">{card.icon}</div>
            <h3 className="font-semibold text-gray-900 mb-1">{card.title}</h3>
            <p className="text-sm text-gray-500 leading-snug">{card.description}</p>
          </div>
        ))}
      </div>
      
      <div className="mt-12 text-xs text-gray-400 font-medium uppercase tracking-widest sunrise-sweep">
        Ready for production · Azure Zero Trust
      </div>
    </div>
  );
};

export default WelcomeScreen;
