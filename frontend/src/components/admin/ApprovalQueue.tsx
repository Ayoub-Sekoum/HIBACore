import React, { useState } from 'react';
import { Clock, CheckCircle2, AlertTriangle, ExternalLink } from 'lucide-react';

interface ApprovalRequest {
    id: string;
    tenant_id: string;
    tool_name: string;
    args: any;
    reason: string;
    created_at: string;
    status: 'pending' | 'approved' | 'rejected';
}

interface Props {
    requests: ApprovalRequest[];
    onActionCompleted?: () => void;
}

const ApprovalQueue: React.FC<Props> = ({ requests, onActionCompleted }) => {
    const [processingId, setProcessingId] = useState<string | null>(null);

    const handleAction = async (id: string, _action: 'approve' | 'reject') => {
        setProcessingId(id);
        try {
            // Nota: endpoint mockati nel backend ma pronti per l'integrazione
            // await adminService.super_process_approval(id, action);
            if (onActionCompleted) onActionCompleted();
        } catch (error) {
            console.error("Failed to process approval", error);
        } finally {
            setProcessingId(null);
        }
    };

    return (
        <div className="space-y-4">
            {requests.length === 0 && (
                <div className="p-10 text-center glass-effect rounded-3xl border border-dashed border-[var(--border-light)]">
                    <CheckCircle2 className="w-10 h-10 text-green-500 mx-auto opacity-20 mb-3" />
                    <p className="text-sm text-[var(--apple-text-muted)]">Coda vuota. Tutte le richieste sono state gestite.</p>
                </div>
            )}
            {requests.map((req) => (
                <div key={req.id} className="glass-effect p-6 rounded-3xl border border-[var(--border-light)] space-y-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="p-3 bg-orange-500/10 text-orange-500 rounded-2xl">
                                <AlertTriangle className="w-5 h-5" />
                            </div>
                            <div>
                                <h3 className="font-bold text-lg">Richiesta Ad Alto Rischio</h3>
                                <p className="text-xs text-[var(--apple-text-muted)] uppercase tracking-wider font-bold">{req.tenant_id}</p>
                            </div>
                        </div>
                        <div className="text-right text-xs text-[var(--apple-text-muted)]">
                            <p className="flex items-center gap-1 justify-end"><Clock className="w-3 h-3" /> {new Date(req.created_at).toLocaleTimeString()}</p>
                        </div>
                    </div>

                    <div className="bg-[var(--input-bg)] p-4 rounded-2xl space-y-2">
                        <p className="text-sm font-bold flex items-center gap-2">
                            <ExternalLink className="w-4 h-4 text-[var(--brand-red)]" /> 
                            Tool: <span className="text-[var(--brand-red)]">{req.tool_name.toUpperCase()}</span>
                        </p>
                        <p className="text-xs italic text-[var(--apple-text-muted)]">"{req.reason}"</p>
                        <div className="mt-2 text-[10px] font-mono opacity-60 overflow-x-auto whitespace-nowrap">
                            ARGS: {JSON.stringify(req.args)}
                        </div>
                    </div>

                    <div className="flex gap-3">
                        <button 
                            onClick={() => handleAction(req.id, 'approve')}
                            disabled={processingId !== null}
                            className="flex-1 py-3 bg-green-500 text-white rounded-2xl font-bold text-sm shadow-lg shadow-green-500/20 hover:scale-105 active:scale-95 transition-all disabled:opacity-50"
                        >
                            Approva
                        </button>
                        <button 
                            onClick={() => handleAction(req.id, 'reject')}
                            disabled={processingId !== null}
                            className="flex-1 py-3 bg-[var(--input-bg)] text-[var(--apple-text)] border border-[var(--border-light)] rounded-2xl font-bold text-sm hover:bg-red-500/10 hover:text-red-500 hover:border-red-500/20 transition-all disabled:opacity-50"
                        >
                            Rifiuta
                        </button>
                    </div>
                </div>
            ))}
        </div>
    );
};

export default ApprovalQueue;
