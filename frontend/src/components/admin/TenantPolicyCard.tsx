import React from 'react';
import { Shield, ShieldAlert, Zap, Lock, MoreHorizontal } from 'lucide-react';

interface TenantPolicy {
    tenant_id: string;
    status: 'active' | 'suspended';
    plan: 'base' | 'standard' | 'enterprise';
    tool_allowlist: string[];
    max_thinking_level: string;
}

interface Props {
    policy: TenantPolicy;
    onConfigure?: (id: string) => void;
}

const TenantPolicyCard: React.FC<Props> = ({ policy, onConfigure }) => {
    const isSuspended = policy.status === 'suspended';

    return (
        <div className={`glass-effect p-6 rounded-[2.5rem] border ${isSuspended ? 'border-red-500/30' : 'border-[var(--border-light)]'} space-y-6 hover:shadow-2xl transition-all group relative overflow-hidden`}>
            {isSuspended && (
                <div className="absolute top-0 left-0 w-full h-1 bg-red-500" />
            )}
            
            <div className="flex justify-between items-start">
                <div className="space-y-1">
                    <h3 className="text-xl font-black tracking-tight flex items-center gap-2">
                        {policy.tenant_id}
                        {isSuspended && <ShieldAlert className="w-4 h-4 text-red-500" />}
                    </h3>
                    <div className="flex gap-2">
                         <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-widest ${
                            policy.plan === 'enterprise' ? 'bg-purple-500/10 text-purple-500' :
                            policy.plan === 'standard' ? 'bg-blue-500/10 text-blue-500' :
                            'bg-gray-500/10 text-gray-400'
                        }`}>
                            {policy.plan}
                        </span>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-widest ${
                            isSuspended ? 'bg-red-500/10 text-red-500' : 'bg-green-500/10 text-green-500'
                        }`}>
                            {policy.status}
                        </span>
                    </div>
                </div>
                <button 
                    onClick={() => onConfigure?.(policy.tenant_id)}
                    className="p-2 hover:bg-[var(--input-bg)] rounded-xl transition-colors"
                >
                    <MoreHorizontal className="w-5 h-5 text-[var(--apple-text-muted)]" />
                </button>
            </div>

            <div className="space-y-3">
                <p className="text-[10px] font-bold text-[var(--apple-text-muted)] uppercase tracking-wider">Tool Autorizzati</p>
                <div className="flex flex-wrap gap-2">
                    {policy.tool_allowlist.slice(0, 3).map((tool) => (
                        <div key={tool} className="flex items-center gap-1.5 px-2.5 py-1 bg-[var(--input-bg)] rounded-lg border border-[var(--border-light)]">
                            <Zap className="w-3 h-3 text-[var(--brand-red)]" />
                            <span className="text-[10px] font-medium">{tool}</span>
                        </div>
                    ))}
                    {policy.tool_allowlist.length > 3 && (
                        <span className="text-[10px] text-[var(--apple-text-muted)] font-bold pl-1">+{policy.tool_allowlist.length - 3}</span>
                    )}
                </div>
            </div>

            <div className="pt-4 flex items-center justify-between border-t border-[var(--border-light)]">
                <div className="flex items-center gap-2">
                    <Shield className="w-4 h-4 text-blue-500 opacity-50" />
                    <span className="text-xs font-medium text-[var(--apple-text-muted)]">Enforced</span>
                </div>
                <button 
                    onClick={() => onConfigure?.(policy.tenant_id)}
                    className="text-xs font-bold text-[var(--brand-red)] hover:underline"
                >
                    Configura Policy
                </button>
            </div>
        </div>
    );
};

export default TenantPolicyCard;
