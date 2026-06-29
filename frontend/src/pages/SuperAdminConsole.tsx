import React, { useEffect, useState } from 'react';
import { adminService } from '../services/admin';
import TenantPolicyCard from '../components/admin/TenantPolicyCard';
import AuditLogTable from '../components/admin/AuditLogTable';
import { LayoutDashboard, Users, ShieldCheck, Activity, Search, Plus } from 'lucide-react';

const SuperAdminConsole: React.FC = () => {
    const [tenants, setTenants] = useState<any[]>([]);
    const [globalAudit, setGlobalAudit] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function loadData() {
            try {
                const [auditRes, tenantsRes] = await Promise.all([
                    adminService.super_get_audit(20),
                    adminService.super_list_tenants()
                ]);

                if (auditRes.status === 'success') {
                    setGlobalAudit(auditRes.data);
                }
                
                if (tenantsRes.status === 'success') {
                    setTenants(tenantsRes.data);
                }
            } catch (error) {
                console.error("Failed to load super admin data", error);
            } finally {
                setLoading(false);
            }
        }
        loadData();
    }, []);

    if (loading) return <div className="flex h-screen items-center justify-center bg-[var(--apple-bg)] font-sans text-xl font-bold animate-pulse text-[var(--apple-text-muted)]">Caricamento Console Super Admin...</div>;

    return (
        <div className="min-h-screen p-8 space-y-10 animate-reveal">
            {/* Header */}
            <header className="flex justify-between items-center">
                <div>
                    <h1 className="text-4xl font-black tracking-tight">Super Admin Console</h1>
                    <p className="text-[var(--apple-text-muted)] mt-2">Gestione globale dei tenant e delle policy di sicurezza.</p>
                </div>
                <button className="flex items-center gap-2 px-6 py-3 bg-[var(--brand-red)] text-white rounded-2xl font-bold shadow-lg shadow-[var(--btn-hover-shadow)] hover:scale-105 active:scale-95 transition-all">
                    <Plus className="w-5 h-5" /> Nuovo Tenant
                </button>
            </header>

            {/* Stats Row */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                {[
                    { label: 'Tenant Attivi', value: '12', icon: Users, color: 'text-blue-500' },
                    { label: 'Policy Enforced', value: '100%', icon: ShieldCheck, color: 'text-green-500' },
                    { label: 'Audit Trail', value: '1.2k', icon: Activity, color: 'text-orange-500' },
                    { label: 'System Health', value: 'Optimal', icon: LayoutDashboard, color: 'text-purple-500' },
                ].map((stat, i) => (
                    <div key={i} className="glass-effect p-6 rounded-3xl flex items-center justify-between">
                        <div>
                            <p className="text-sm font-medium text-[var(--apple-text-muted)]">{stat.label}</p>
                            <p className="text-2xl font-black mt-1">{stat.value}</p>
                        </div>
                        <stat.icon className={`w-8 h-8 ${stat.color} opacity-20`} />
                    </div>
                ))}
            </div>

            {/* Main Content */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
                {/* Tenants Grid */}
                <div className="lg:col-span-2 space-y-6">
                    <div className="flex items-center justify-between">
                        <h2 className="text-2xl font-bold flex items-center gap-3">
                            <Users className="w-6 h-6 text-[var(--brand-red)]" /> Clienti Recenti
                        </h2>
                        <div className="relative">
                            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[var(--apple-text-muted)]" />
                            <input 
                                type="text" 
                                placeholder="Cerca tenant..." 
                                className="pl-10 pr-4 py-2 bg-[var(--input-bg)] rounded-xl text-sm focus:ring-2 ring-[var(--brand-red)] outline-none"
                            />
                        </div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {tenants.map((t) => (
                            <TenantPolicyCard key={t.tenant_id} policy={t} />
                        ))}
                    </div>
                </div>

                {/* Right Sidebar: Global Audit */}
                <div className="space-y-6">
                    <h2 className="text-2xl font-bold flex items-center gap-3">
                        <Activity className="w-6 h-6 text-orange-500" /> Audit Globale
                    </h2>
                    <div className="space-y-4">
                        <AuditLogTable logs={globalAudit} />
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SuperAdminConsole;
