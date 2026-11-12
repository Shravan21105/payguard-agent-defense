import React, { useEffect, useState } from 'react';
import { FileCheck2, Check, X, Clock } from 'lucide-react';
import { apiService } from '../services/api';
import type { TransactionRecord } from '../types';
import { Badge } from '../components/common/Badge';
import { RiskMeter } from '../components/common/RiskMeter';

export const Approvals: React.FC = () => {
  const [pending, setPending] = useState<TransactionRecord[]>([]);

  useEffect(() => {
    loadApprovals();
  }, []);

  const loadApprovals = async () => {
    try {
      const data = await apiService.getTransactions(50, 'WARN');
      setPending(data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleAction = (id: string, action: 'APPROVE' | 'REJECT') => {
    // In Phase 1 demonstration, simulate human-in-the-loop sign-off
    alert(`Human Operator signed: ${action} for ${id}. (Simulation Mode)`);
    setPending((prev) => prev.filter((t) => t.transaction_id !== id));
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <FileCheck2 className="w-6 h-6 text-amber-400" />
          <span>Human-in-the-Loop Approval Queue</span>
        </h1>
        <p className="text-sm text-charcoal-400 mt-1">
          Transactions flagged with WARN status requiring explicit human verification before vault release.
        </p>
      </div>

      <div className="payguard-panel p-6">
        <div className="flex items-center justify-between border-b border-charcoal-800 pb-3 mb-4">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-amber-400" />
            <h2 className="text-sm font-bold uppercase tracking-wider font-mono text-white">
              Pending Authorization Requests ({pending.length})
            </h2>
          </div>
          <span className="text-xs font-mono text-charcoal-400">Escalated by Deterministic Policy</span>
        </div>

        {pending.length === 0 ? (
          <div className="py-16 text-center text-charcoal-400 text-xs font-mono">
            No transactions currently awaiting human operator approval.
          </div>
        ) : (
          <div className="space-y-4">
            {pending.map((tx) => (
              <div
                key={tx.transaction_id}
                className="p-4 rounded-xl bg-charcoal-850 border border-amber-900/40 hover:border-amber-700/60 transition space-y-3"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs font-mono">
                  <div className="flex items-center gap-3">
                    <Badge type="WARN" />
                    <div>
                      <span className="text-white font-bold">{tx.recipient}</span>
                      <span className="text-charcoal-400 block text-[11px]">Initiated by {tx.sender}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    <div>
                      <span className="text-charcoal-400 block text-[10px]">AMOUNT</span>
                      <span className="text-emerald-400 font-bold text-sm">{tx.amount.toFixed(2)} NEAR</span>
                    </div>
                    <div>
                      <span className="text-charcoal-400 block text-[10px]">RISK SCORE</span>
                      <RiskMeter score={tx.risk_score} />
                    </div>
                  </div>
                </div>

                <div className="p-2.5 rounded bg-charcoal-900 border border-charcoal-800 text-[11px] font-mono text-charcoal-300">
                  <span className="text-amber-400 font-bold block mb-1">Warning Reasons:</span>
                  {tx.reasons.map((r, i) => (
                    <div key={i} className="flex items-start gap-1.5">
                      <span className="text-amber-400">•</span>
                      <span>{r}</span>
                    </div>
                  ))}
                </div>

                <div className="flex items-center justify-end gap-3 pt-2">
                  <button
                    onClick={() => handleAction(tx.transaction_id, 'REJECT')}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-950 border border-rose-800/80 hover:bg-rose-900 text-rose-300 font-mono text-xs transition"
                  >
                    <X className="w-3.5 h-3.5" />
                    <span>REJECT TRANSACTION</span>
                  </button>

                  <button
                    onClick={() => handleAction(tx.transaction_id, 'APPROVE')}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-mono text-xs font-semibold transition shadow-shield-glow"
                  >
                    <Check className="w-3.5 h-3.5" />
                    <span>AUTHORIZE &amp; SIGN</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
