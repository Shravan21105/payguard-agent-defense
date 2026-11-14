import React, { useEffect, useState } from 'react';
import { FileCheck2, Check, X, Clock, RotateCw, CheckCircle2, ShieldAlert } from 'lucide-react';
import { apiService } from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';
import type { PendingApprovalItem } from '../types';
import {
  SectionHeader,
  GlassCard,
  GradientButton,
  StatusBadge,
  RiskIndicator,
  LiveIndicator,
  EmptyState,
  ConfirmationDialog,
  PageTransition,
} from '../components/ui';

export const Approvals: React.FC = () => {
  const { isConnected, lastMessage } = useWebSocket('escrow');
  const [pending, setPending] = useState<PendingApprovalItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionInProgress, setActionInProgress] = useState<string | null>(null);
  const [statusNotification, setStatusNotification] = useState<string | null>(null);

  // Confirmation dialog state
  const [confirmDialog, setConfirmDialog] = useState<{
    isOpen: boolean;
    txId: string;
    action: 'APPROVE' | 'REJECT';
    amount: number;
    currency: string;
    recipient: string;
  }>({
    isOpen: false,
    txId: '',
    action: 'APPROVE',
    amount: 0,
    currency: 'NEAR',
    recipient: '',
  });

  const loadApprovals = async () => {
    setLoading(true);
    try {
      const data = await apiService.getApprovals();
      setPending(data);
    } catch (e) {
      console.error('Failed to load approvals:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadApprovals();
    const interval = setInterval(loadApprovals, 15000);
    return () => clearInterval(interval);
  }, []);

  // Real-time escrow updates via WebSocket
  useEffect(() => {
    if (!lastMessage) return;
    const txId = lastMessage.payload?.transaction_id || lastMessage.transaction_id;

    if (lastMessage.event_type === 'escrow.created') {
      loadApprovals();
      setStatusNotification(`⚡ Live Event: New pending escrow ${txId || ''} escalated for operator review.`);
      setTimeout(() => setStatusNotification(null), 5000);
    } else if (
      lastMessage.event_type.startsWith('escrow.') &&
      (lastMessage.event_type.includes('released') || lastMessage.event_type.includes('refunded'))
    ) {
      loadApprovals();
    }
  }, [lastMessage]);

  const handleOpenConfirm = (tx: PendingApprovalItem, action: 'APPROVE' | 'REJECT') => {
    setConfirmDialog({
      isOpen: true,
      txId: tx.transaction_id,
      action,
      amount: tx.amount,
      currency: tx.currency,
      recipient: tx.recipient,
    });
  };

  const handleExecuteConfirmedAction = async () => {
    const { txId, action } = confirmDialog;
    setActionInProgress(txId);
    setConfirmDialog((prev) => ({ ...prev, isOpen: false }));

    try {
      await apiService.decideApproval(
        txId,
        action,
        `Manual operator ${action.toLowerCase()} via PAYGUARD dashboard`
      );
      setStatusNotification(
        `✓ Transaction ${txId} successfully ${action === 'APPROVE' ? 'authorized and released to NEAR vault' : 'rejected and refunded'}.`
      );
      setTimeout(() => setStatusNotification(null), 6000);
      await loadApprovals();
    } catch (err: any) {
      console.error('Failed to execute approval decision:', err);
      setStatusNotification(
        `✕ Error processing ${action} on ${txId}: ${err?.response?.data?.detail || err.message}`
      );
    } finally {
      setActionInProgress(null);
    }
  };

  return (
    <PageTransition className="space-y-6 max-w-7xl mx-auto pb-16">
      {/* Title */}
      <SectionHeader
        icon={<FileCheck2 className="w-5 h-5 text-amber-500" />}
        title="Human-in-the-Loop Approval Queue"
        description="Autonomous agent transactions escalated with WARN status requiring authorized human operator review and Ed25519 cryptographic release before vault execution."
        action={
          <div className="flex items-center gap-3">
            <LiveIndicator
              status={isConnected ? 'live' : 'offline'}
              label={isConnected ? 'ESCROW STREAM ACTIVE' : 'RECONNECTING'}
            />
            <GradientButton
              variant="glass"
              size="sm"
              onClick={loadApprovals}
              isLoading={loading}
              leftIcon={<RotateCw className={`w-3.5 h-3.5 text-cyber-cyan ${loading ? 'animate-spin' : ''}`} />}
            >
              REFRESH QUEUE
            </GradientButton>
          </div>
        }
      />

      {/* Escrow Invariant Notice */}
      <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-xs font-mono text-amber-700 dark:text-amber-300 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <ShieldAlert className="w-5 h-5 text-amber-500 flex-shrink-0" />
          <div>
            <span className="font-bold block tracking-wider uppercase">
              TIMELOCK VAULT ESCROW PROTECTION ACTIVE
            </span>
            <span className="text-slate-600 dark:text-navy-300">
              Funds remain safely locked in the NEAR Testnet smart contract vault (<code className="text-slate-900 dark:text-white bg-slate-200 dark:bg-navy-900 px-1.5 py-0.5 rounded border border-slate-300 dark:border-white/10">payguard-vault.testnet</code>) until an operator confirms or rejects the transfer.
            </span>
          </div>
        </div>
      </div>

      {statusNotification && (
        <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-700 dark:text-emerald-300 text-xs font-mono flex items-center gap-2 animate-fade-in-up">
          <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0" />
          <span>{statusNotification}</span>
        </div>
      )}

      <GlassCard className="p-6" variant="elevated">
        <div className="flex items-center justify-between border-b border-slate-200/80 dark:border-white/[0.08] pb-3 mb-6">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-amber-500" />
            <h2 className="text-sm font-bold uppercase tracking-wider font-mono text-slate-900 dark:text-white">
              Pending Authorization Requests ({pending.length})
            </h2>
          </div>
          <span className="text-xs font-mono text-slate-500 dark:text-navy-400">Escalated by Deterministic Policy</span>
        </div>

        {pending.length === 0 ? (
          <EmptyState
            icon={<CheckCircle2 className="w-8 h-8 text-emerald-500" />}
            title="Zero Pending Approvals"
            description="No transactions currently awaiting human operator authorization. Transactions with unverified counterparties or threshold anomalies appear here automatically."
            className="py-16 border-0 bg-transparent shadow-none"
          />
        ) : (
          <div className="space-y-4">
            {pending.map((tx) => (
              <div
                key={tx.transaction_id}
                className="p-5 rounded-2xl bg-white dark:bg-navy-850/90 border border-amber-500/30 hover:border-amber-500/60 transition space-y-4 shadow-sm dark:shadow-glass-panel"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs font-mono">
                  <div className="flex items-center gap-3">
                    <StatusBadge status="WARN" size="sm" />
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-slate-900 dark:text-white font-bold text-sm">{tx.recipient}</span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-700 dark:text-amber-400 border border-amber-500/30 font-semibold">
                          ON-CHAIN ESCROW ACTIVE
                        </span>
                      </div>
                      <span className="text-slate-500 dark:text-navy-400 block text-[11px] mt-0.5">
                        Initiated by agent <strong className="text-slate-800 dark:text-navy-200">{tx.sender}</strong>
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-6">
                    <div>
                      <span className="text-slate-500 dark:text-navy-400 block text-[10px] uppercase">LOCKED AMOUNT</span>
                      <span className="text-emerald-600 dark:text-emerald-400 font-bold text-base">
                        {tx.amount.toFixed(2)} {tx.currency}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-500 dark:text-navy-400 block text-[10px] uppercase">RISK SCORE</span>
                      <RiskIndicator score={tx.risk_score} showTier />
                    </div>
                  </div>
                </div>

                {tx.purpose && (
                  <div className="p-3 rounded-xl bg-slate-50 dark:bg-navy-900 border border-slate-200 dark:border-white/[0.06] text-xs font-mono">
                    <span className="text-slate-400 dark:text-navy-500 block text-[10px] uppercase mb-1 font-bold">DECLARED PURPOSE / INTENT</span>
                    <span className="text-slate-800 dark:text-navy-200 font-sans">{tx.purpose}</span>
                  </div>
                )}

                <div className="p-3 rounded-xl bg-slate-50 dark:bg-navy-900 border border-slate-200 dark:border-white/[0.06] text-xs font-mono space-y-1">
                  <span className="text-amber-600 dark:text-amber-400 font-bold text-[11px] block mb-1">Policy Violation Details:</span>
                  {tx.reasons.map((r, i) => (
                    <div key={i} className="flex items-start gap-1.5 text-slate-700 dark:text-navy-300">
                      <span className="text-amber-500 font-bold">•</span>
                      <span>{r}</span>
                    </div>
                  ))}
                </div>

                <div className="flex items-center justify-end gap-3 pt-2 border-t border-slate-200 dark:border-white/[0.06]">
                  <GradientButton
                    variant="danger"
                    size="sm"
                    disabled={actionInProgress === tx.transaction_id}
                    onClick={() => handleOpenConfirm(tx, 'REJECT')}
                    leftIcon={<X className="w-3.5 h-3.5" />}
                  >
                    REJECT &amp; REFUND ESCROW
                  </GradientButton>

                  <GradientButton
                    variant="success"
                    size="sm"
                    disabled={actionInProgress === tx.transaction_id}
                    onClick={() => handleOpenConfirm(tx, 'APPROVE')}
                    leftIcon={<Check className="w-3.5 h-3.5" />}
                  >
                    AUTHORIZE &amp; RELEASE VAULT
                  </GradientButton>
                </div>
              </div>
            ))}
          </div>
        )}
      </GlassCard>

      {/* Confirmation Dialog for Financial Authorization */}
      <ConfirmationDialog
        isOpen={confirmDialog.isOpen}
        onClose={() => setConfirmDialog((prev) => ({ ...prev, isOpen: false }))}
        onConfirm={handleExecuteConfirmedAction}
        isLoading={actionInProgress === confirmDialog.txId}
        type={confirmDialog.action === 'APPROVE' ? 'success' : 'danger'}
        title={
          confirmDialog.action === 'APPROVE'
            ? 'Confirm Cryptographic Vault Release'
            : 'Confirm Escrow Rejection & Refund'
        }
        description={
          confirmDialog.action === 'APPROVE'
            ? `You are authorizing the release of ${confirmDialog.amount.toFixed(2)} ${confirmDialog.currency} from the NEAR smart contract vault to ${confirmDialog.recipient}. This action will be cryptographically signed with the Ed25519 policy key and cannot be undone.`
            : `You are rejecting transaction ${confirmDialog.txId}. Locked funds will be refunded from vault escrow back to the agent sender treasury.`
        }
        confirmLabel={
          confirmDialog.action === 'APPROVE'
            ? 'Sign & Release Funds'
            : 'Reject & Refund Escrow'
        }
        cancelLabel="Cancel"
      />
    </PageTransition>
  );
};
