import React from 'react';
import { Shield, Check } from 'lucide-react';

interface Plan {
    id: string;
    name: string;
    description: string;
    price: string;
    features: string[];
}

const PLANS: Plan[] = [
    { 
        id: 'base', 
        name: 'Base', 
        description: 'Per piccoli team.', 
        price: '€0', 
        features: ['Web Search', 'File Read (50MB)'] 
    },
    { 
        id: 'standard', 
        name: 'Standard', 
        description: 'Per aziende in crescita.', 
        price: '€49/m', 
        features: ['Web Search', 'File Read (100MB)', 'Code Execution', 'Webhooks'] 
    },
    { 
        id: 'enterprise', 
        name: 'Enterprise', 
        description: 'Sicurezza e controllo totale.', 
        price: 'Custom', 
        features: ['Tutto lo Standard', 'Shell Execution', 'Network Allowlist', 'Deep Thinking'] 
    },
];

interface Props {
    currentPlanId: string;
    onPlanSelect: (planId: string) => void;
}

const PlanSelector: React.FC<Props> = ({ currentPlanId, onPlanSelect }) => {
    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {PLANS.map((plan) => {
                const isSelected = plan.id === currentPlanId;
                return (
                    <div 
                        key={plan.id}
                        onClick={() => onPlanSelect(plan.id)}
                        className={`p-6 rounded-3xl border-2 cursor-pointer transition-all ${
                            isSelected ? 'border-[var(--brand-red)] bg-[var(--brand-red)]/5' : 'border-[var(--border-light)] hover:border-[var(--apple-text-muted)]'
                        }`}
                    >
                        <div className="flex justify-between items-start mb-4">
                            <h4 className="font-black text-lg">{plan.name}</h4>
                            {isSelected && <Check className="w-5 h-5 text-[var(--brand-red)]" />}
                        </div>
                        <p className="text-2xl font-black mb-2">{plan.price}</p>
                        <p className="text-xs text-[var(--apple-text-muted)] mb-4">{plan.description}</p>
                        <ul className="space-y-2">
                            {plan.features.map((f, i) => (
                                <li key={i} className="text-[10px] flex items-center gap-2 font-medium">
                                    <Shield className="w-3 h-3 text-[var(--brand-red)] opacity-40" /> {f}
                                </li>
                            ))}
                        </ul>
                    </div>
                );
            })}
        </div>
    );
};

export default PlanSelector;
