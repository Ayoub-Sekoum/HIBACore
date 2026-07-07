import React, { useEffect, useState } from 'react';
import { adminService } from '../services/admin';
import AuditLogTable from '../components/admin/AuditLogTable';
import { Settings, Shield, Zap, Clock, Lock, Save } from 'lucide-react';

const TenantAdminConsole: React.FC = () => {
    const [policy, setPolicy] = useState<any>(null);
    const [audit, setAudit] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        async function loadData() {
            try {
                const pRes = await adminService.tenant_get_policy();
                if (pRes.status === 'success') {
                    setPolicy(pRes.data);
                }
                const aRes = await adminService.tenant_get_audit(20);
                if (aRes.status === 'success') {
                    setAudit(aRes.data);
                }
            } catch (error) {
                console.error("Failed to load tenant admin data", error);
            } finally {
                setLoading(false);
            }
        }
        loadData();
    }, []);

    const handleToggleTool = async (tool: string) => {
        if (!policy) return;
        const newTools = policy.tool_allowlist.includes(tool)
            ? policy.tool_allowlist.filter((t: string) => t !== tool)
            : [...policy.tool_allowlist, tool];
        
        setPolicy({ ...policy, tool_allowlist: newTools });
    };

    const handleSave = async () => {
        setSaving(true);
        try {
            await adminService.tenant_update_policy({ 
                tool_allowlist: policy.tool_allowlist,
                require_approval_for_high_risk: policy.require_approval_for_high_risk
            });
            // Update audit log
            const aRes = await adminService.tenant_get_audit(20);
            if (aRes.status === 'success') setAudit(aRes.data);
        } catch (error) {
            console.error("Failed to save policy", error);
        } finally {
            setSaving(false);
        }
    };

    if (loading) return <div className="p-20 text-center animate-pulse">Caricamento console admin...</div>;

    const allPossibleTools = ["web_search", "file_read", "code_execution", "shell_exec", "webhook_send"];

    return (
        <div className="min-h-screen p-8 max-w-6xl mx-auto space-y-10 animate-reveal">
            <header className="flex justify-between items-center">
                <div>
                    <h1 className="text-4xl font-black tracking-tight">Admin Console Console</h1>
                    <p className="text-[var(--apple-text-muted)] mt-2">Configura le policy di sicurezza per il tuo tenant.</p>
                </div>
                <span className="bg-[var(--brand-red)] text-white px-4 py-1.5 rounded-full text-sm font-bold shadow-lg">
                    Piano: {policy.plan.toUpperCase()}
                </span>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
                {/* Left Column: Tools Configuration*/}
                <div className="md:col-span-2 space-y-8">
                    <section className="glass-effect rounded-[2.5rem] p-8 space-y-6">
                        <div className="flex items-center justify-between">
                            <h2 className="text-2xl font-bold flex items-center gap-3">
                                <Settings className="w-6 h-6 text-[var(--brand-red)]" /> Tool Autorizzati
                            </h2>
                            <button 
                                onClick={handleSave}
                                disabled={saving}
                                className="flex items-center gap-2 px-5 py-2.5 bg-[var(--apple-text)] text-[var(--apple-bg)] rounded-xl font-bold hover:opacity-90 disabled:opacity-50 transition-all"
                            >
                                <Save className="w-4 h-4" /> {saving ? 'Salvataggio...' : 'Salva Modifiche'}
                            </button>
                        </div>

                        <div className="grid grid-cols-1 gap-4">
                            {allPossibleTools.map((tool) => {
                                const isEnabled = policy.tool_allowlist.includes(tool);
                                const isRestricted = !policy.admin_can_modify.includes('tool_allowlist');
                                
                                return (
                                    <div 
                                        key={tool}
                                        className={`flex items-center justify-between p-5 rounded-2xl border ${
                                            isEnabled ? 'border-[var(--brand-red)] bg-red-50/5' : 'border-[var(--border-light)] opacity-60'
                                        } transition-all`}
                                    >
                                        <div className="flex items-center gap-4">
                                            <div className={`p-3 rounded-xl ${isEnabled ? 'bg-[var(--brand-red)] text-white' : 'bg-[var(--input-bg)]'}`}>
                                                <Zap className="w-5 h-5" />
                                            </div>
                                            <div>
                                                <p className="font-bold text-lg">{tool.replace('_', ' ').toUpperCase()}</p>
                                                <p className="text-sm text-[var(--apple-text-muted)]">Permette all'agente di usare {tool}.</p>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-4">
                                            {isRestricted && <Lock className="w-4 h-4 text-orange-400" />}
                                            <button 
                                                disabled={isRestricted}
                                                onClick={() => handleToggleTool(tool)}
                                                className={`w-14 h-8 rounded-full relative transition-colors ${
                                                    isEnabled ? 'bg-[var(--brand-red)]' : 'bg-[var(--border-light)]'
                                                } ${isRestricted ? 'cursor-not-allowed grayscale' : ''}`}
                                            >
                                                <div className={`w-6 h-6 bg-white rounded-full absolute top-1 transition-transform ${isEnabled ? 'left-7' : 'left-1'}`} />
                                            </button>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </section>
                </div>

                {/* Right Column: General Settings & Audit*/}
                <div className="space-y-8">
                     <section className="glass-effect rounded-[2rem] p-6 space-y-6">
                        <h2 className="text-xl font-bold flex items-center gap-3">
                            <Shield className="w-5 h-5 text-blue-500" /> Sicurezza Avanzata
                        </h2>
                        
                        <div className="flex items-center justify-between p-4 bg-[var(--input-bg)] rounded-2xl">
                            <div>
                                <p className="font-bold text-sm">Approvazione Umana</p>
                                <p className="text-xs text-[var(--apple-text-muted)]">Per azioni ad alto rischio.</p>
                            </div>
                            <button 
                                onClick={() => setPolicy({...policy, require_approval_for_high_risk: !policy.require_approval_for_high_risk})}
                                className={`w-11 h-6 rounded-full relative transition-colors ${
                                    policy.require_approval_for_high_risk ? 'bg-green-500' : 'bg-[var(--border-light)]'
                                }`}
                            >
                                <div className={`w-4 h-4 bg-white rounded-full absolute top-1 transition-transform ${policy.require_approval_for_high_risk ? 'left-6' : 'left-1'}`} />
                            </button>
                        </div>
                     </section>

                     <section className="space-y-4">
                        <h2 className="text-xl font-bold flex items-center gap-3 px-2 text-orange-500">
                            <Clock className="w-5 h-5" /> Attività Recenti
                        </h2>
                        <AuditLogTable logs={audit} />
                     </section>
                </div>
            </div>
        </div>
    );
};

export default TenantAdminConsole;
