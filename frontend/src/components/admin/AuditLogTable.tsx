import React from 'react';
import { Clock, ShieldAlert, CheckCircle2 } from 'lucide-react';

interface AuditLogEntry {
    id: string;
    timestamp: string;
    action: string;
    actor_id: string;
    result: string;
    field_changed?: string;
    old_value?: any;
    new_value?: any;
    reason?: string;
    tool_name?: string;
}

interface Props {
    logs: AuditLogEntry[];
}

const AuditLogTable: React.FC<Props> = ({ logs }) => {
    return (
        <div className="space-y-3">
            {logs.length === 0 && (
                <p className="text-center text-sm text-[var(--apple-text-muted)] py-10">Nessuna attività registrata.</p>
            )}
            {logs.map((log) => (
                <div key={log.id} className="p-4 rounded-2xl bg-[var(--input-bg)] border border-[var(--border-light)] hover:border-[var(--brand-red)] transition-all group">
                    <div className="flex items-start justify-between gap-3">
                        <div className="flex items-start gap-3">
                            <div className={`p-2 rounded-lg mt-0.5 ${
                                log.result === 'denied' ? 'bg-red-500/10 text-red-500' : 
                                log.result === 'pending' ? 'bg-orange-500/10 text-orange-500' :
                                'bg-green-500/10 text-green-500'
                            }`}>
                                {log.result === 'denied' ? <ShieldAlert className="w-4 h-4" /> : 
                                 log.result === 'pending' ? <Clock className="w-4 h-4" /> :
                                 <CheckCircle2 className="w-4 h-4" />}
                            </div>
                            <div>
                                <p className="text-sm font-bold">
                                    {log.action === 'update_policy' ? `Modifica: ${log.field_changed}` : 
                                     log.action === 'attempted_enable_tool' ? `Accesso negato: ${log.tool_name}` :
                                     log.action}
                                </p>
                                <p className="text-xs text-[var(--apple-text-muted)] flex items-center gap-1 mt-1">
                                    <Clock className="w-3 h-3" /> {new Date(log.timestamp).toLocaleString()}
                                </p>
                                {log.reason && (
                                    <p className="text-[10px] mt-2 text-red-400 bg-red-400/5 p-1 rounded border border-red-400/10 italic">
                                        "{log.reason}"
                                    </p>
                                )}
                            </div>
                        </div>
                        <div className="text-right">
                             <span className="text-[10px] font-mono bg-[var(--apple-bg)] px-2 py-0.5 rounded border border-[var(--border-light)]">
                                {log.actor_id.slice(-6)}
                             </span>
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
};

export default AuditLogTable;
