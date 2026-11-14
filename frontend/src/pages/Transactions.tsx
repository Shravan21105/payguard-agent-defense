import React, { useEffect, useState } from 'react';
import {
  Search,
  RefreshCw,
  ArrowRightLeft,
  Copy,
  Check,
  ShieldCheck,
  Brain,
  FileCode,
  Sliders,
  ExternalLink,
  Layers,
  Clock,
  Radio,
  Filter,
} from 'lucide-react';
import { apiService } from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';
import type {
  AgentExecutionLog,
  AuthorizationEvidence,
  PayguardEvent,
  TransactionRecord,
} from '../types';
import {
  SectionHeader,
  GlassCard,
  GradientButton,
  StatusBadge,
  RiskIndicator,
  EmptyState,
  LoadingSkeleton,
  PageTransition,
} from '../components/ui';
import { PolicyPill } from '../components/common/PolicyPill';
import { Modal } from '../components/common/Modal';
import { formatAgentFindings } from '../utils/formatters';

export const Transactions: React.FC = () => {
  const { lastMessage } = useWebSocket('transactions');
  const [transactions, setTransactions] = useState<TransactionRecord[]>([]);
  const [filtered, setFiltered] = useState<TransactionRecord[]>([]);
  const [filterDecision, setFilterDecision] = useState<string>('ALL');
  const [filterMode, setFilterMode] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedTx, setSelectedTx] = useState<TransactionRecord | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Modal extra details state
  const [evidence, setEvidence] = useState<AuthorizationEvidence | null>(null);
  const [agentLogs, setAgentLogs] = useState<AgentExecutionLog[]>([]);
  const [txEvents, setTxEvents] = useState<PayguardEvent[]>([]);
  const [activeTab, setActiveTab] = useState<'policy' | 'agents' | 'evidence' | 'onchain' | 'timeline'>('policy');
  const [copiedHash, setCopiedHash] = useState(false);

  const fetchTransactions = async () => {
    setLoading(true);
    try {
      const data = await apiService.getTransactions(100);
      setTransactions(data);
      applyFilters(data, filterDecision, filterMode, searchQuery);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTransactions();
  }, []);

  // Live WebSocket updates
  useEffect(() => {
    if (!lastMessage) return;

    if (
      lastMessage.event_type.startsWith('transaction.') ||
      lastMessage.event_type === 'NEW_TRANSACTION_EVALUATED'
    ) {
      const tx = lastMessage.payload;
      if (tx && tx.transaction_id) {
        setTransactions((prev) => {
          const exists = prev.find((t) => t.transaction_id === tx.transaction_id);
          const next = exists
            ? prev.map((t) => (t.transaction_id === tx.transaction_id ? { ...t, ...tx } : t))
            : [tx as TransactionRecord, ...prev];
          applyFilters(next, filterDecision, filterMode, searchQuery);
          return next;
        });

        if (selectedTx && selectedTx.transaction_id === tx.transaction_id) {
          setTxEvents((prev) => [...prev, lastMessage]);
        }
      }
    }
  }, [lastMessage, selectedTx, filterDecision, filterMode, searchQuery]);

  const applyFilters = (data: TransactionRecord[], decision: string, mode: string, query: string) => {
    let result = [...data];
    if (decision !== 'ALL') {
      result = result.filter((t) => t.decision === decision);
    }
    if (mode !== 'ALL') {
      if (mode === 'ONCHAIN') {
        result = result.filter((t) => t.execution_mode === 'ONCHAIN' || (!t.is_mock_simulation && !t.execution_mode));
      } else if (mode === 'SIMULATION') {
        result = result.filter((t) => t.is_mock_simulation || t.execution_mode === 'SIMULATION' || t.execution_mode === 'dry_run');
      }
    }
    if (query.trim()) {
      const q = query.toLowerCase();
      result = result.filter(
        (t) =>
          t.sender.toLowerCase().includes(q) ||
          t.recipient.toLowerCase().includes(q) ||
          t.transaction_id.toLowerCase().includes(q) ||
          (t.purpose && t.purpose.toLowerCase().includes(q))
      );
    }
    setFiltered(result);
  };

  const handleDecisionChange = (dec: string) => {
    setFilterDecision(dec);
    applyFilters(transactions, dec, filterMode, searchQuery);
  };

  const handleModeChange = (mode: string) => {
    setFilterMode(mode);
    applyFilters(transactions, filterDecision, mode, searchQuery);
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const q = e.target.value;
    setSearchQuery(q);
    applyFilters(transactions, filterDecision, filterMode, q);
  };

  const handleSelectTx = async (tx: TransactionRecord) => {
    setSelectedTx(tx);
    setActiveTab('policy');
    setEvidence(null);
    setAgentLogs([]);
    setTxEvents([]);

    try {
      const [evData, agentsData, eventsData] = await Promise.allSettled([
        apiService.getEvidence(tx.transaction_id),
        apiService.getTransactionAgents(tx.transaction_id),
        apiService.getTransactionEvents(tx.transaction_id),
      ]);

      if (evData.status === 'fulfilled') {
        setEvidence(evData.value);
      }
      if (agentsData.status === 'fulfilled') {
        setAgentLogs(agentsData.value.executions || []);
      }
      if (eventsData.status === 'fulfilled') {
        setTxEvents(eventsData.value || []);
      }
    } catch (err) {
      console.error('Failed to load transaction audit details:', err);
    }
  };

  const handleCopyDigest = (digest: string) => {
    navigator.clipboard.writeText(digest);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  return (
    <PageTransition className="space-y-6 max-w-7xl mx-auto pb-16">
      {/* Header */}
      <SectionHeader
        icon={<ArrowRightLeft className="w-5 h-5" />}
        title="Transaction Security Explorer"
        description="Comprehensive audit ledger of evaluated autonomous agent transfers with cryptographic authorization evidence and NEAR blockchain verification."
        action={
          <GradientButton
            variant="glass"
            size="sm"
            onClick={fetchTransactions}
            isLoading={loading}
            leftIcon={<RefreshCw className={`w-3.5 h-3.5 text-cyber-cyan ${loading ? 'animate-spin' : ''}`} />}
          >
            REFRESH AUDIT LEDGER
          </GradientButton>
        }
      />

      {/* Filter and Search Bar */}
      <GlassCard className="p-4 flex flex-col md:flex-row md:items-center justify-between gap-4" variant="elevated">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 dark:text-navy-400 absolute left-3.5 top-3" />
          <input
            type="text"
            placeholder="Search by account, tx hash, or declared intent..."
            value={searchQuery}
            onChange={handleSearchChange}
            className="w-full bg-white dark:bg-navy-900/90 border border-slate-300 dark:border-white/10 rounded-xl pl-10 pr-4 py-2 text-xs font-mono text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-navy-500 focus:outline-none focus:border-cyber-indigo focus:ring-1 focus:ring-cyber-indigo"
          />
        </div>

        {/* Filter Controls: Execution Mode & Decision */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Execution Mode Filter */}
          <div className="flex items-center gap-1 p-1 rounded-xl bg-slate-100 dark:bg-navy-900 border border-slate-200 dark:border-white/10 text-xs font-mono">
            <span className="text-[10px] text-slate-500 dark:text-navy-400 px-2 uppercase font-bold flex items-center gap-1">
              <Radio className="w-3 h-3 text-cyan-600 dark:text-cyber-cyan" />
              <span>Mode:</span>
            </span>
            {[
              { id: 'ALL', label: 'ALL' },
              { id: 'ONCHAIN', label: '⚡ ON-CHAIN' },
              { id: 'SIMULATION', label: '🔬 SIM' },
            ].map((m) => (
              <button
                key={m.id}
                onClick={() => handleModeChange(m.id)}
                className={`px-3 py-1 rounded-lg transition text-[11px] font-medium cursor-pointer ${
                  filterMode === m.id
                    ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-bold shadow-primary-glow'
                    : 'text-slate-600 dark:text-navy-400 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                {m.label}
              </button>
            ))}
          </div>

          {/* Decision Filter Tabs */}
          <div className="flex items-center gap-1 p-1 rounded-xl bg-slate-100 dark:bg-navy-900 border border-slate-200 dark:border-white/10 text-xs font-mono">
            <span className="text-[10px] text-slate-500 dark:text-navy-400 px-2 uppercase font-bold flex items-center gap-1">
              <Filter className="w-3 h-3 text-slate-400 dark:text-navy-400" />
              <span>Verdict:</span>
            </span>
            {['ALL', 'ALLOW', 'WARN', 'BLOCK'].map((dec) => (
              <button
                key={dec}
                onClick={() => handleDecisionChange(dec)}
                className={`px-3 py-1 rounded-lg transition text-[11px] font-medium cursor-pointer ${
                  filterDecision === dec
                    ? 'bg-white dark:bg-navy-750 text-slate-900 dark:text-white font-bold border border-slate-200 dark:border-white/10 shadow-sm'
                    : 'text-slate-600 dark:text-navy-400 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                {dec}
              </button>
            ))}
          </div>
        </div>
      </GlassCard>

      {/* Transactions Table */}
      <GlassCard className="p-6" variant="elevated">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="text-slate-500 dark:text-navy-400 border-b border-slate-200 dark:border-white/[0.08] pb-3">
                <th className="py-3 font-semibold uppercase tracking-wider text-[11px]">TX ID</th>
                <th className="py-3 font-semibold uppercase tracking-wider text-[11px]">DECISION</th>
                <th className="py-3 font-semibold uppercase tracking-wider text-[11px]">STATUS</th>
                <th className="py-3 font-semibold uppercase tracking-wider text-[11px]">SENDER</th>
                <th className="py-3 font-semibold uppercase tracking-wider text-[11px]">RECIPIENT</th>
                <th className="py-3 font-semibold uppercase tracking-wider text-[11px]">AMOUNT</th>
                <th className="py-3 font-semibold uppercase tracking-wider text-[11px]">RISK</th>
                <th className="py-3 font-semibold uppercase tracking-wider text-[11px]">NEAR TX HASH</th>
                <th className="py-3 font-semibold uppercase tracking-wider text-[11px] text-right">ACTION</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-white/[0.04]">
              {loading && transactions.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-12">
                    <LoadingSkeleton variant="row" count={5} />
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center">
                    <EmptyState
                      icon={<ArrowRightLeft className="w-6 h-6 text-slate-400 dark:text-navy-400" />}
                      title="No matching transactions"
                      description="No records match your selected filter parameters or search query."
                      action={
                        <GradientButton
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setFilterDecision('ALL');
                            setFilterMode('ALL');
                            setSearchQuery('');
                            applyFilters(transactions, 'ALL', 'ALL', '');
                          }}
                        >
                          Clear Filters
                        </GradientButton>
                      }
                      className="border-0 bg-transparent py-4"
                    />
                  </td>
                </tr>
              ) : (
                filtered.map((tx) => {
                  const displayStatus = tx.status || (tx.decision === 'ALLOW' ? 'CONFIRMED' : (tx.decision === 'BLOCK' ? 'BLOCKED' : 'ESCROW_CREATED'));
                  return (
                    <tr
                      key={tx.transaction_id}
                      onClick={() => handleSelectTx(tx)}
                      className="hover:bg-slate-50 dark:hover:bg-white/[0.03] cursor-pointer transition"
                    >
                      <td className="py-3.5 text-slate-500 dark:text-navy-400 truncate max-w-[100px]" title={tx.transaction_id}>
                        {tx.transaction_id}
                      </td>
                      <td className="py-3.5">
                        <StatusBadge status={tx.decision} size="xs" />
                      </td>
                      <td className="py-3.5">
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          displayStatus === 'CONFIRMED' || displayStatus === 'ALLOWED'
                            ? 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/30'
                            : displayStatus === 'BLOCKED' || displayStatus === 'REJECTED'
                            ? 'bg-rose-500/10 text-rose-700 dark:text-rose-400 border border-rose-500/30'
                            : 'bg-amber-500/10 text-amber-700 dark:text-amber-400 border border-amber-500/30'
                        }`}>
                          {displayStatus}
                        </span>
                      </td>
                      <td className="py-3.5 text-slate-600 dark:text-navy-300 max-w-[130px] truncate" title={tx.sender}>
                        {tx.sender}
                      </td>
                      <td className="py-3.5 text-slate-900 dark:text-white max-w-[130px] truncate font-semibold" title={tx.recipient}>
                        {tx.recipient}
                      </td>
                      <td className="py-3.5 text-emerald-600 dark:text-emerald-400 font-bold">
                        {tx.amount.toFixed(2)} NEAR
                      </td>
                      <td className="py-3.5">
                        <RiskIndicator score={tx.risk_score} size="sm" />
                      </td>
                      <td className="py-3.5 text-slate-500 dark:text-navy-400 max-w-[120px]">
                        {tx.tx_hash ? (
                          <a
                            href={tx.explorer_url || `https://testnet.nearblocks.io/txns/${tx.tx_hash}`}
                            target="_blank"
                            rel="noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="text-indigo-600 hover:text-indigo-500 dark:text-cyan-400 dark:hover:text-cyan-300 hover:underline flex items-center gap-1 font-mono text-[11px]"
                            title={tx.tx_hash}
                          >
                            <span className="truncate">{tx.tx_hash.slice(0, 8)}...</span>
                            <ExternalLink className="w-3 h-3 flex-shrink-0" />
                          </a>
                        ) : (
                          <span className="text-slate-400 dark:text-navy-600 text-[10px]">—</span>
                        )}
                      </td>
                      <td className="py-3.5 text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleSelectTx(tx);
                          }}
                          className="px-3 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-800 border border-slate-200 dark:bg-navy-750 dark:hover:bg-navy-700 dark:text-cyan-300 dark:hover:text-white dark:border-white/5 text-[11px] transition cursor-pointer"
                        >
                          AUDIT
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </GlassCard>

      {/* Transaction Inspection Modal with 5 Tabs */}
      {selectedTx && (
        <Modal
          isOpen={!!selectedTx}
          onClose={() => setSelectedTx(null)}
          title={`Audit Trace — ${selectedTx.transaction_id}`}
          maxWidth="2xl"
        >
          <div className="space-y-4">
            {/* Verdict summary banner */}
            <div className="flex items-center justify-between p-3.5 rounded-xl bg-slate-50 dark:bg-navy-900 border border-slate-200 dark:border-white/[0.08]">
              <div>
                <span className="text-xs text-slate-500 dark:text-navy-400 block font-mono">DECISION</span>
                <StatusBadge status={selectedTx.decision} className="mt-1" />
              </div>
              <div className="text-right">
                <span className="text-xs text-slate-500 dark:text-navy-400 block font-mono">RISK SCORE</span>
                <div className="mt-1 flex items-center justify-end">
                  <RiskIndicator score={selectedTx.risk_score} showTier />
                </div>
              </div>
            </div>

            {/* Core Parameters */}
            <div className="grid grid-cols-2 gap-2 text-xs font-mono">
              <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-navy-850 border border-slate-200 dark:border-white/[0.06]">
                <span className="text-slate-500 dark:text-navy-400 block text-[10px]">SENDER</span>
                <span className="text-slate-900 dark:text-white font-bold truncate block mt-0.5">{selectedTx.sender}</span>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-navy-850 border border-slate-200 dark:border-white/[0.06]">
                <span className="text-slate-500 dark:text-navy-400 block text-[10px]">RECIPIENT</span>
                <span className="text-slate-900 dark:text-white font-bold truncate block mt-0.5">{selectedTx.recipient}</span>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-navy-850 border border-slate-200 dark:border-white/[0.06]">
                <span className="text-slate-500 dark:text-navy-400 block text-[10px]">AMOUNT</span>
                <span className="text-emerald-600 dark:text-emerald-400 font-bold block mt-0.5">
                  {selectedTx.amount} {selectedTx.currency}
                </span>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-navy-850 border border-slate-200 dark:border-white/[0.06]">
                <span className="text-slate-500 dark:text-navy-400 block text-[10px]">EXECUTION ALLOWED</span>
                <span className={`font-bold block mt-0.5 ${selectedTx.execution_allowed ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'}`}>
                  {selectedTx.execution_allowed ? 'TRUE (AUTHORIZED)' : 'FALSE (BLOCKED)'}
                </span>
              </div>
            </div>

            {selectedTx.purpose && (
              <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-navy-850 border border-slate-200 dark:border-white/[0.06] text-xs">
                <span className="text-slate-500 dark:text-navy-400 block font-mono text-[10px] mb-0.5">AGENT DECLARED INTENT</span>
                <span className="text-slate-700 dark:text-navy-200 font-sans">{selectedTx.purpose}</span>
              </div>
            )}

            {/* Modal Tabs */}
            <div className="flex border-b border-slate-200 dark:border-white/[0.08] font-mono text-xs overflow-x-auto">
              <button
                onClick={() => setActiveTab('policy')}
                className={`flex items-center gap-1.5 px-3 py-2 border-b-2 transition cursor-pointer ${
                  activeTab === 'policy'
                    ? 'border-indigo-600 dark:border-cyber-cyan text-slate-900 dark:text-white font-bold'
                    : 'border-transparent text-slate-500 dark:text-navy-400 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <Sliders className="w-3.5 h-3.5" />
                <span>Policy Checks</span>
              </button>
              <button
                onClick={() => setActiveTab('agents')}
                className={`flex items-center gap-1.5 px-3 py-2 border-b-2 transition cursor-pointer ${
                  activeTab === 'agents'
                    ? 'border-indigo-600 dark:border-cyber-cyan text-slate-900 dark:text-white font-bold'
                    : 'border-transparent text-slate-500 dark:text-navy-400 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <Brain className="w-3.5 h-3.5" />
                <span>Multi-Agent Traces</span>
              </button>
              <button
                onClick={() => setActiveTab('evidence')}
                className={`flex items-center gap-1.5 px-3 py-2 border-b-2 transition cursor-pointer ${
                  activeTab === 'evidence'
                    ? 'border-indigo-600 dark:border-cyber-cyan text-slate-900 dark:text-white font-bold'
                    : 'border-transparent text-slate-500 dark:text-navy-400 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <FileCode className="w-3.5 h-3.5" />
                <span>RFC-8785 Evidence</span>
              </button>
              <button
                onClick={() => setActiveTab('onchain')}
                className={`flex items-center gap-1.5 px-3 py-2 border-b-2 transition cursor-pointer ${
                  activeTab === 'onchain'
                    ? 'border-indigo-600 dark:border-cyber-cyan text-slate-900 dark:text-white font-bold'
                    : 'border-transparent text-slate-500 dark:text-navy-400 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <Layers className="w-3.5 h-3.5" />
                <span>NEAR On-Chain Audit</span>
              </button>
              <button
                onClick={() => setActiveTab('timeline')}
                className={`flex items-center gap-1.5 px-3 py-2 border-b-2 transition cursor-pointer ${
                  activeTab === 'timeline'
                    ? 'border-indigo-600 dark:border-cyber-cyan text-slate-900 dark:text-white font-bold'
                    : 'border-transparent text-slate-500 dark:text-navy-400 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <Clock className="w-3.5 h-3.5" />
                <span>Lifecycle Timeline ({txEvents.length})</span>
              </button>
            </div>

            {/* Tab 1: Policy Checks */}
            {activeTab === 'policy' && (
              <div className="space-y-3 animate-fade-in-up">
                <div>
                  <span className="text-[11px] font-mono uppercase text-slate-500 dark:text-navy-400 tracking-wider block mb-2 font-medium">
                    Deterministic Policy Outcomes
                  </span>
                  <div className="grid grid-cols-2 gap-2">
                    {Object.entries(selectedTx.policy_checks).map(([name, status]) => (
                      <PolicyPill key={name} name={name} status={status} />
                    ))}
                  </div>
                </div>

                <div>
                  <span className="text-[11px] font-mono uppercase text-slate-500 dark:text-navy-400 tracking-wider block mb-2 font-medium">
                    Enforcement Reasons
                  </span>
                  <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-navy-850 border border-slate-200 dark:border-white/[0.06] space-y-1.5 text-xs text-slate-700 dark:text-navy-300 font-sans">
                    {selectedTx.reasons.map((reason, idx) => (
                      <div key={idx} className="flex items-start gap-2">
                        <span className="text-indigo-600 dark:text-cyber-indigo font-bold">•</span>
                        <span>{reason}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Tab 2: Multi-Agent Traces */}
            {activeTab === 'agents' && (
              <div className="space-y-3 animate-fade-in-up text-xs font-mono">
                {agentLogs.length === 0 ? (
                  <EmptyState
                    icon={<Brain className="w-6 h-6 text-slate-400 dark:text-navy-400" />}
                    title="No Multi-Agent Traces"
                    description="Individual agent execution traces were not recorded for this transaction."
                    className="py-6 border-0 bg-transparent"
                  />
                ) : (
                  agentLogs.map((log) => (
                    <div
                      key={log.execution_id}
                      className="p-3.5 rounded-xl bg-slate-50 dark:bg-navy-850 border border-slate-200 dark:border-white/[0.06] space-y-1.5"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-slate-900 dark:text-white font-bold">{log.agent_name}</span>
                        <div className="flex items-center gap-2">
                          <span className="text-emerald-600 dark:text-emerald-400 text-[11px]">{log.execution_time_ms} ms</span>
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                              log.status === 'SUCCESS'
                                ? 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/30'
                                : 'bg-amber-500/10 text-amber-700 dark:text-amber-400 border border-amber-500/30'
                            }`}
                          >
                            {log.status}
                          </span>
                        </div>
                      </div>
                      <div className="text-slate-600 dark:text-navy-300 text-[11px] pt-1 font-sans space-y-1">
                        {formatAgentFindings(log.findings).map((f, i) => (
                          <div key={i} className="flex items-start gap-1">
                            <span className="text-indigo-600 dark:text-cyber-cyan">•</span>
                            <span>{f}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}

            {/* Tab 3: Cryptographic Evidence */}
            {activeTab === 'evidence' && (
              <div className="space-y-3 animate-fade-in-up text-xs font-mono">
                {!evidence ? (
                  <EmptyState
                    icon={<FileCode className="w-6 h-6 text-slate-400 dark:text-navy-400" />}
                    title="No Evidence Record"
                    description="Cryptographic RFC-8785 evidence record is not available for this record."
                    className="py-6 border-0 bg-transparent"
                  />
                ) : (
                  <>
                    <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-between">
                      <div className="flex items-center gap-2.5">
                        <ShieldCheck className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                        <div>
                          <span className="text-emerald-800 dark:text-emerald-300 font-bold block">
                            Cryptographic Integrity Verified
                          </span>
                          <span className="text-slate-500 dark:text-navy-400 text-[10px]">
                            RFC-8785 JSON Canonicalization + SHA-256 Digest
                          </span>
                        </div>
                      </div>
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-700 dark:text-emerald-400 font-bold">
                        IMMUTABLE
                      </span>
                    </div>

                    <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-navy-850 border border-slate-200 dark:border-white/[0.06] space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="text-slate-500 dark:text-navy-400 text-[10px]">SHA-256 DIGEST</span>
                        <button
                          onClick={() => handleCopyDigest(evidence.sha256_digest)}
                          className="flex items-center gap-1 text-[10px] text-indigo-600 dark:text-cyan-400 hover:text-indigo-500 dark:hover:text-cyan-300 cursor-pointer font-bold"
                        >
                          {copiedHash ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                          <span>{copiedHash ? 'COPIED' : 'COPY HASH'}</span>
                        </button>
                      </div>
                      <p className="text-emerald-600 dark:text-emerald-400 break-all text-[11px] bg-slate-100 dark:bg-navy-900 p-2.5 rounded-lg border border-slate-200 dark:border-white/5 select-all font-mono">
                        {evidence.sha256_digest}
                      </p>
                    </div>

                    <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-navy-850 border border-slate-200 dark:border-white/[0.06] space-y-1.5">
                      <span className="text-slate-500 dark:text-navy-400 text-[10px] block">CANONICAL RFC-8785 PAYLOAD</span>
                      <pre className="text-slate-800 dark:text-navy-300 text-[10px] bg-slate-100 dark:bg-navy-900 p-2.5 rounded-lg border border-slate-200 dark:border-white/5 overflow-x-auto whitespace-pre-wrap max-h-36 font-mono">
                        {evidence.rfc8785_canonical_payload}
                      </pre>
                    </div>
                  </>
                )}
              </div>
            )}

            {/* Tab 4: NEAR On-Chain Audit */}
            {activeTab === 'onchain' && (
              <div className="space-y-3 animate-fade-in-up text-xs font-mono">
                <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-navy-850 border border-slate-200 dark:border-white/[0.06] space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500 dark:text-navy-400 text-[11px]">Execution Status</span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      selectedTx.status === 'CONFIRMED' || selectedTx.decision === 'ALLOW'
                        ? 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/30'
                        : selectedTx.status === 'BLOCKED' || selectedTx.decision === 'BLOCK'
                        ? 'bg-rose-500/10 text-rose-700 dark:text-rose-400 border border-rose-500/30'
                        : 'bg-amber-500/10 text-amber-700 dark:text-amber-400 border border-amber-500/30'
                    }`}>
                      {selectedTx.status || 'CONFIRMED'}
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-slate-500 dark:text-navy-400 text-[11px]">Execution Pipeline</span>
                    <span className="text-slate-900 dark:text-white font-bold">
                      {selectedTx.execution_mode === 'ONCHAIN' ? '⚡ NEAR Testnet Vault (Live)' : '🔬 Dry Run / Sim'}
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-slate-500 dark:text-navy-400 text-[11px]">Vault Contract ID</span>
                    <code className="text-indigo-700 dark:text-cyan-300 bg-slate-100 dark:bg-navy-900 px-2 py-0.5 rounded-lg border border-slate-200 dark:border-white/10 font-bold">
                      payguard-vault.testnet
                    </code>
                  </div>
                </div>

                {selectedTx.tx_hash ? (
                  <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-navy-850 border border-emerald-500/30 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-emerald-700 dark:text-emerald-400 font-bold text-[11px] flex items-center gap-1.5">
                        <ShieldCheck className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                        <span>Confirmed on NEAR Testnet</span>
                      </span>
                      <a
                        href={selectedTx.explorer_url || `https://testnet.nearblocks.io/txns/${selectedTx.tx_hash}`}
                        target="_blank"
                        rel="noreferrer"
                        className="text-indigo-600 hover:text-indigo-500 dark:text-cyan-400 dark:hover:text-cyan-300 underline text-[10px] flex items-center gap-1 font-bold"
                      >
                        <span>NEARBLOCKS EXPLORER</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>

                    <div className="text-[10px] text-slate-600 dark:text-navy-300">
                      <span className="text-slate-400 dark:text-navy-500 block mb-1">RECEIPT HASH:</span>
                      <code className="text-emerald-700 dark:text-emerald-300 bg-slate-100 dark:bg-navy-900 p-2 rounded-lg border border-slate-200 dark:border-white/5 block truncate">
                        {selectedTx.tx_hash}
                      </code>
                    </div>

                    {selectedTx.block_height && (
                      <div className="text-[10px] text-slate-500 dark:text-navy-400 flex items-center justify-between pt-1">
                        <span>Block Height:</span>
                        <span className="text-slate-900 dark:text-white font-bold font-mono">#{selectedTx.block_height}</span>
                      </div>
                    )}
                  </div>
                ) : selectedTx.decision === 'BLOCK' ? (
                  <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 space-y-1.5">
                    <div className="text-rose-700 dark:text-rose-400 font-bold text-[11px]">Execution Signature Strictly Withheld</div>
                    <p className="text-[10px] text-slate-600 dark:text-navy-300 font-sans">
                      Deterministic policy blocked this transaction. In accordance with zero-trust design, no Ed25519 authorization token or blockchain receipt exists for blocked transactions.
                    </p>
                  </div>
                ) : (
                  <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 space-y-1.5">
                    <div className="text-amber-700 dark:text-amber-400 font-bold text-[11px]">Awaiting Human Authorization / Timelock Escrow</div>
                    <p className="text-[10px] text-slate-600 dark:text-navy-300 font-sans">
                      Funds are held in on-chain timelock escrow or awaiting operator decision before blockchain release.
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Tab 5: Real-Time Lifecycle Timeline */}
            {activeTab === 'timeline' && (
              <div className="space-y-3 animate-fade-in-up text-xs font-mono">
                {txEvents.length === 0 ? (
                  <EmptyState
                    icon={<Clock className="w-6 h-6 text-slate-400 dark:text-navy-400" />}
                    title="No Lifecycle Events Recorded"
                    description="Transactions evaluated live in Phase 5 stream events from intent evaluation to blockchain confirmation."
                    className="py-6 border-0 bg-transparent"
                  />
                ) : (
                  <div className="relative pl-6 space-y-4 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200 dark:before:bg-navy-800">
                    {txEvents.map((ev, index) => {
                      const sevColor =
                        ev.severity === 'CRITICAL'
                          ? 'border-rose-500/30 bg-rose-500/10 text-rose-700 dark:text-rose-300'
                          : ev.severity === 'WARNING'
                          ? 'border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-300'
                          : ev.severity === 'SUCCESS'
                          ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300'
                          : 'border-slate-200 bg-white text-slate-700 dark:border-white/10 dark:bg-navy-850 dark:text-navy-200';
                      
                      const dotColor =
                        ev.severity === 'CRITICAL'
                          ? 'bg-rose-500'
                          : ev.severity === 'WARNING'
                          ? 'bg-amber-500'
                          : ev.severity === 'SUCCESS'
                          ? 'bg-emerald-500'
                          : 'bg-indigo-600 dark:bg-cyber-cyan';

                      return (
                        <div key={ev.event_id || `ev-${index}`} className="relative group">
                          {/* Timeline dot */}
                          <div className={`absolute -left-[27px] top-1.5 w-2.5 h-2.5 rounded-full ${dotColor} ring-4 ring-slate-100 dark:ring-navy-950`} />
                          
                          <div className={`p-3.5 rounded-xl border ${sevColor} space-y-1.5 transition hover:border-slate-300 dark:hover:border-white/20`}>
                            <div className="flex flex-wrap items-center justify-between gap-2">
                              <div className="flex items-center gap-2">
                                <span className="font-bold text-slate-900 dark:text-white text-[11px]">
                                  {ev.event_type}
                                </span>
                                <span className="px-2 py-0.5 rounded-full text-[9px] bg-navy-900 border border-white/10 text-navy-400 uppercase font-mono font-bold">
                                  {ev.category}
                                </span>
                              </div>
                              <span className="text-navy-400 text-[10px]">
                                {new Date(ev.timestamp).toLocaleTimeString()}
                              </span>
                            </div>

                            <div className="flex items-center gap-2 text-[10px] text-navy-400">
                              <span>Source: <strong className="text-white">{ev.source}</strong></span>
                              <span>•</span>
                              <span>Severity: <strong className="text-white">{ev.severity}</strong></span>
                            </div>

                            {ev.payload && Object.keys(ev.payload).length > 0 && (
                              <details className="mt-2 text-[10px]">
                                <summary className="cursor-pointer text-cyan-400 hover:text-cyan-300 select-none font-medium">
                                  View event payload ({Object.keys(ev.payload).length} attributes)
                                </summary>
                                <pre className="mt-2 p-2.5 rounded-lg bg-navy-950 border border-white/10 text-navy-300 overflow-x-auto max-h-32 text-[10px] whitespace-pre-wrap font-mono">
                                  {JSON.stringify(ev.payload, null, 2)}
                                </pre>
                              </details>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}
          </div>
        </Modal>
      )}
    </PageTransition>
  );
};
