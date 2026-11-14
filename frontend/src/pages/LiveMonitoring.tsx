import React, { useEffect, useMemo, useState } from 'react';
import {
  Radio,
  Shield,
  Activity,
  Clock,
  ArrowRight,
  Search,
  Filter,
  CheckCircle2,
  XCircle,
  AlertOctagon,
  ExternalLink,
  Layers,
  Cpu,
  RefreshCw,
  Terminal,
  Play,
  Pause,
} from 'lucide-react';
import { useWebSocket } from '../hooks/useWebSocket';
import { apiService } from '../services/api';
import type {
  MonitoringHealthResponse,
  MonitoringMetricsResponse,
  PayguardEvent,
  TransactionRecord,
} from '../types';
import {
  SectionHeader,
  GlassCard,
  GradientButton,
  StatusBadge,
  RiskIndicator,
  LiveIndicator,
  EmptyState,
  PageTransition,
} from '../components/ui';
import { Modal } from '../components/common/Modal';

export const LiveMonitoring: React.FC = () => {
  const { isConnected, connectionState, lastMessage } = useWebSocket('all');
  const [events, setEvents] = useState<PayguardEvent[]>([]);
  const [streamItems, setStreamItems] = useState<TransactionRecord[]>([]);
  const [metrics, setMetrics] = useState<MonitoringMetricsResponse | null>(null);
  const [health, setHealth] = useState<MonitoringHealthResponse | null>(null);
  const [loading, setLoading] = useState(true);

  // Pause/Resume streaming display buffer control
  const [isPaused, setIsPaused] = useState(false);

  // Filters
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedSeverity, setSelectedSeverity] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Selected event for payload inspection modal
  const [selectedEvent, setSelectedEvent] = useState<PayguardEvent | null>(null);

  // Selected transaction for lifecycle visualizer
  const [selectedTxId, setSelectedTxId] = useState<string | null>(null);
  const [selectedTxEvents, setSelectedTxEvents] = useState<PayguardEvent[]>([]);

  // Initial load
  const fetchData = async () => {
    try {
      const [eventsRes, txRes, metricsRes, healthRes] = await Promise.allSettled([
        apiService.getEvents({ limit: 40 }),
        apiService.getTransactions(15),
        apiService.getMonitoringMetrics(),
        apiService.getMonitoringHealth(),
      ]);
      if (eventsRes.status === 'fulfilled') setEvents(eventsRes.value.events || []);
      if (txRes.status === 'fulfilled') {
        const txData = txRes.value || [];
        setStreamItems(txData);
        if (txData.length > 0 && !selectedTxId) {
          setSelectedTxId(txData[0].transaction_id);
        }
      }
      if (metricsRes.status === 'fulfilled') setMetrics(metricsRes.value);
      if (healthRes.status === 'fulfilled') setHealth(healthRes.value);
    } catch (err) {
      console.error('[LiveMonitoring] Failed to fetch initial monitoring data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(() => {
      apiService.getMonitoringMetrics().then(setMetrics).catch(() => {});
      apiService.getMonitoringHealth().then(setHealth).catch(() => {});
    }, 15000);
    return () => clearInterval(interval);
  }, []);

  // Handle incoming WebSocket events
  useEffect(() => {
    if (!lastMessage) return;

    if (!isPaused) {
      // Prepend new event to live stream with max 50 items
      setEvents((prev) => [lastMessage, ...prev.filter((e) => e.event_id !== lastMessage.event_id).slice(0, 49)]);
    }

    // Update transactions stream if transaction event
    if (
      lastMessage.event_type.startsWith('transaction.') ||
      lastMessage.event_type === 'NEW_TRANSACTION_EVALUATED'
    ) {
      const txPayload = lastMessage.payload;
      if (txPayload && txPayload.transaction_id) {
        setStreamItems((prev) => {
          const exists = prev.find((t) => t.transaction_id === txPayload.transaction_id);
          if (exists) {
            return prev.map((t) => (t.transaction_id === txPayload.transaction_id ? { ...t, ...txPayload } : t));
          }
          return [txPayload as TransactionRecord, ...prev.slice(0, 19)];
        });
      }
    }

    // If matching currently inspected transaction, update its lifecycle sequence
    if (selectedTxId && lastMessage.transaction_id === selectedTxId) {
      setSelectedTxEvents((prev) => [...prev, lastMessage]);
    }
  }, [lastMessage, selectedTxId, isPaused]);

  // When selected transaction changes, fetch its complete chronological events
  useEffect(() => {
    if (selectedTxId) {
      apiService
        .getTransactionEvents(selectedTxId)
        .then(setSelectedTxEvents)
        .catch(() => setSelectedTxEvents([]));
    }
  }, [selectedTxId]);

  // Filtered events
  const filteredEvents = useMemo(() => {
    return events.filter((evt) => {
      if (selectedCategory !== 'all' && evt.category !== selectedCategory) return false;
      if (selectedSeverity !== 'all' && evt.severity !== selectedSeverity) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesType = evt.event_type.toLowerCase().includes(q);
        const matchesTx = (evt.transaction_id || '').toLowerCase().includes(q);
        const matchesSource = evt.source.toLowerCase().includes(q);
        const matchesPayload = JSON.stringify(evt.payload).toLowerCase().includes(q);
        return matchesType || matchesTx || matchesSource || matchesPayload;
      }
      return true;
    });
  }, [events, selectedCategory, selectedSeverity, searchQuery]);

  // Lifecycle visualizer stages for selected transaction
  const lifecycleSteps = useMemo(() => {
    const types = selectedTxEvents.map((e) => e.event_type);
    const hasReceived = types.includes('transaction.received') || types.length > 0;
    const hasAnalyzing = types.includes('transaction.analyzing') || types.some((t) => t.startsWith('agent.'));
    const hasEvaluated =
      types.includes('transaction.evaluated') ||
      types.includes('transaction.decided') ||
      types.includes('transaction.allowed') ||
      types.includes('transaction.warned') ||
      types.includes('transaction.blocked');

    const isBlocked = types.includes('transaction.blocked');
    const isWarned = types.includes('transaction.warned') || types.includes('escrow.created');
    const isAllowed = types.includes('transaction.allowed');
    const isExecuting = types.includes('transaction.executing');
    const isConfirmed = types.includes('transaction.confirmed') || types.includes('blockchain.transaction_confirmed');
    const isEscrowReleased = types.includes('escrow.released') || types.includes('escrow.approved');
    const isEscrowRefunded = types.includes('escrow.refunded') || types.includes('escrow.rejected');
    const isFailed = types.includes('transaction.failed') || types.includes('blockchain.transaction_failed');

    return [
      { id: '1', name: 'RECEIVED', active: hasReceived, status: 'DONE' },
      { id: '2', name: 'ANALYZING', active: hasAnalyzing, status: hasAnalyzing ? 'DONE' : 'PENDING' },
      {
        id: '3',
        name: isBlocked ? 'BLOCKED' : isWarned ? 'WARN (ESCROW)' : 'ALLOWED',
        active: hasEvaluated,
        status: isBlocked ? 'BLOCKED' : isWarned ? 'WARN' : isAllowed ? 'DONE' : 'PENDING',
      },
      {
        id: '4',
        name: isBlocked ? 'SIGNATURE WITHHELD' : isWarned ? 'ESCROW PENDING' : 'EXECUTING',
        active: isBlocked || isWarned || isExecuting || isConfirmed,
        status: isBlocked ? 'HALTED' : isWarned ? (isEscrowReleased ? 'DONE' : isEscrowRefunded ? 'REFUNDED' : 'WAITING') : isConfirmed ? 'DONE' : 'PENDING',
      },
      {
        id: '5',
        name: isBlocked ? 'HALTED' : isEscrowRefunded ? 'REFUNDED' : isConfirmed ? 'CONFIRMED' : isFailed ? 'FAILED' : 'AWAITING',
        active: isBlocked || isConfirmed || isEscrowRefunded || isFailed,
        status: isBlocked ? 'HALTED' : isConfirmed ? 'CONFIRMED' : isEscrowRefunded ? 'REFUNDED' : isFailed ? 'FAILED' : 'PENDING',
      },
    ];
  }, [selectedTxEvents]);

  const rpcStatus = health?.subsystems?.near_rpc?.status || 'ONLINE';
  const blockHeight = health?.subsystems?.near_rpc?.latest_block_height || metrics?.infrastructure?.latest_block_height || 0;
  const lastSync = health?.subsystems?.blockchain_synchronization?.last_sync_time || metrics?.infrastructure?.last_blockchain_sync_time;

  return (
    <PageTransition className="space-y-6 max-w-7xl mx-auto pb-16">
      {/* Title & Live Status Header */}
      <SectionHeader
        icon={<Radio className="w-5 h-5 text-cyber-cyan animate-pulse" />}
        title="Real-Time Security SOC &amp; Event Streaming"
        description="Live telemetry stream bridging AI evaluation, deterministic policy synthesis, and verified NEAR Testnet execution."
        action={
          <div className="flex items-center gap-3">
            <LiveIndicator
              status={isConnected ? 'live' : (connectionState === 'CONNECTING' || connectionState === 'RECONNECTING') ? 'syncing' : 'offline'}
              label={isConnected ? 'STREAM ACTIVE' : `WS: ${connectionState}`}
            />
            <GradientButton
              variant="glass"
              size="sm"
              onClick={fetchData}
              isLoading={loading}
              leftIcon={<RefreshCw className={`w-3.5 h-3.5 text-cyber-cyan ${loading ? 'animate-spin' : ''}`} />}
            >
              SYNC
            </GradientButton>
          </div>
        }
      />

      {/* Real-Time Infrastructure Status Bar */}
      <GlassCard className="p-4 grid grid-cols-2 md:grid-cols-5 gap-4 text-xs font-mono" variant="elevated">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-slate-100 dark:bg-navy-900 border border-slate-200 dark:border-white/10 text-emerald-500 dark:text-emerald-400">
            <Shield className="w-4 h-4" />
          </div>
          <div>
            <span className="text-slate-500 dark:text-navy-400 block text-[10px] uppercase font-bold">NEAR RPC NODE</span>
            <span className={`font-bold ${rpcStatus.includes('ONLINE') ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-600 dark:text-amber-400'}`}>
              {rpcStatus}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-slate-100 dark:bg-navy-900 border border-slate-200 dark:border-white/10 text-cyan-600 dark:text-cyan-400">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <span className="text-slate-500 dark:text-navy-400 block text-[10px] uppercase font-bold">BLOCK HEIGHT</span>
            <span className="text-slate-900 dark:text-white font-bold">#{blockHeight.toLocaleString()}</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-slate-100 dark:bg-navy-900 border border-slate-200 dark:border-white/10 text-indigo-600 dark:text-indigo-400">
            <Activity className="w-4 h-4" />
          </div>
          <div>
            <span className="text-slate-500 dark:text-navy-400 block text-[10px] uppercase font-bold">ACTIVE WS CLIENTS</span>
            <span className="text-emerald-600 dark:text-emerald-400 font-bold">
              {metrics?.infrastructure?.active_websocket_connections ?? 1} Connected
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-slate-100 dark:bg-navy-900 border border-slate-200 dark:border-white/10 text-violet-600 dark:text-violet-400">
            <Clock className="w-4 h-4" />
          </div>
          <div>
            <span className="text-slate-500 dark:text-navy-400 block text-[10px] uppercase font-bold">LAST SYNC</span>
            <span className="text-slate-700 dark:text-navy-200 font-bold">
              {lastSync ? new Date(lastSync).toLocaleTimeString() : 'Active'}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3 col-span-2 md:col-span-1">
          <div className="p-2.5 rounded-xl bg-slate-100 dark:bg-navy-900 border border-slate-200 dark:border-white/10 text-amber-600 dark:text-amber-400">
            <Cpu className="w-4 h-4" />
          </div>
          <div>
            <span className="text-slate-500 dark:text-navy-400 block text-[10px] uppercase font-bold">AVG LATENCY</span>
            <span className="text-emerald-600 dark:text-emerald-400 font-bold">
              {metrics?.performance?.avg_evaluation_latency_ms ?? 3.5} ms
            </span>
          </div>
        </div>
      </GlassCard>

      {/* Transaction Lifecycle Visualizer */}
      <GlassCard className="p-5 space-y-3" variant="elevated">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200/80 dark:border-white/[0.08] pb-3">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-cyber-indigo dark:text-cyber-cyan" />
            <h2 className="text-xs font-bold uppercase tracking-wider font-mono text-slate-900 dark:text-white">
              Transaction Lifecycle Tracker
            </h2>
            {selectedTxId && (
              <span className="text-xs font-mono text-cyan-700 dark:text-cyan-300 px-2 py-0.5 rounded-lg bg-slate-100 dark:bg-navy-900 border border-slate-200 dark:border-white/10">
                {selectedTxId}
              </span>
            )}
          </div>
          <span className="text-[11px] font-mono text-slate-500 dark:text-navy-400">
            {selectedTxEvents.length} Verified Lifecycle Events
          </span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-2 pt-1 font-mono text-xs">
          {lifecycleSteps.map((step, idx) => (
            <div
              key={step.id}
              className={`p-3 rounded-xl border flex flex-col justify-between transition ${
                step.status === 'DONE' || step.status === 'CONFIRMED'
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-700 dark:text-emerald-400'
                  : step.status === 'BLOCKED' || step.status === 'HALTED'
                  ? 'bg-rose-500/10 border-rose-500/30 text-rose-700 dark:text-rose-400'
                  : step.status === 'WARN' || step.status === 'WAITING' || step.status === 'REFUNDED'
                  ? 'bg-amber-500/10 border-amber-500/30 text-amber-700 dark:text-amber-400'
                  : 'bg-slate-50 dark:bg-navy-850/60 border-slate-200 dark:border-white/[0.06] text-slate-700 dark:text-navy-400'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-slate-500 dark:text-navy-400 font-medium">STAGE 0{idx + 1}</span>
                {step.status === 'DONE' || step.status === 'CONFIRMED' ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                ) : step.status === 'BLOCKED' || step.status === 'HALTED' ? (
                  <XCircle className="w-3.5 h-3.5 text-rose-600 dark:text-rose-400" />
                ) : step.status === 'WARN' || step.status === 'WAITING' ? (
                  <AlertOctagon className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
                ) : (
                  <Clock className="w-3.5 h-3.5 text-slate-400 dark:text-navy-600" />
                )}
              </div>
              <div className="mt-2 font-bold text-xs truncate" title={step.name}>
                {step.name}
              </div>
            </div>
          ))}
        </div>
      </GlassCard>

      {/* Main Two-Column View: Real-Time Event Stream (Left) & Live Evaluated Transactions (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Live Event Stream with Filtering & Search (7 Cols) */}
        <GlassCard className="lg:col-span-7 p-6 space-y-4" variant="elevated">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200/80 dark:border-white/[0.08] pb-3">
            <div className="flex items-center gap-2">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500" />
              </span>
              <h2 className="text-sm font-bold uppercase tracking-wider font-mono text-slate-900 dark:text-white">
                Live Event Stream
              </h2>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs font-mono text-slate-500 dark:text-navy-400">{filteredEvents.length} events showing</span>
              <button
                onClick={() => setIsPaused(!isPaused)}
                className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-mono transition cursor-pointer ${
                  isPaused
                    ? 'bg-amber-500/20 text-amber-700 dark:text-amber-300 border border-amber-500/40'
                    : 'bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 dark:bg-navy-800 dark:text-navy-300 dark:hover:text-white dark:border-white/10'
                }`}
                title={isPaused ? 'Resume live stream update' : 'Pause display buffer'}
              >
                {isPaused ? <Play className="w-3 h-3 text-amber-600 dark:text-amber-400" /> : <Pause className="w-3 h-3 text-cyan-600 dark:text-cyan-400" />}
                <span>{isPaused ? 'RESUME' : 'PAUSE'}</span>
              </button>
            </div>
          </div>

          {/* Filter Pills & Search */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 bg-slate-50 dark:bg-navy-900 border border-slate-200 dark:border-white/10 rounded-xl px-3 py-2 text-xs font-mono">
              <Search className="w-3.5 h-3.5 text-slate-400 dark:text-navy-400" />
              <input
                type="text"
                placeholder="Search events by type, transaction ID, or keywords..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="bg-transparent border-none focus:outline-none w-full text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-navy-500 text-xs"
              />
            </div>

            {/* Category Pills */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-[11px] font-mono">
              <span className="text-slate-500 dark:text-navy-500 mr-1 flex items-center gap-1">
                <Filter className="w-3 h-3" /> CATEGORY:
              </span>
              {(['all', 'transactions', 'security', 'blockchain', 'escrow', 'system'] as const).map((cat) => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`px-2.5 py-0.5 rounded-lg capitalize transition cursor-pointer ${
                    selectedCategory === cat
                      ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-bold shadow-primary-glow'
                      : 'bg-slate-100 dark:bg-navy-850 text-slate-600 dark:text-navy-400 hover:text-slate-900 dark:hover:text-white border border-slate-200 dark:border-white/5'
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>

            {/* Severity Pills */}
            <div className="flex items-center gap-1.5 overflow-x-auto text-[11px] font-mono">
              <span className="text-slate-500 dark:text-navy-500 mr-1">SEVERITY:</span>
              {(['all', 'INFO', 'SUCCESS', 'WARNING', 'CRITICAL'] as const).map((sev) => (
                <button
                  key={sev}
                  onClick={() => setSelectedSeverity(sev)}
                  className={`px-2.5 py-0.5 rounded-lg font-bold transition cursor-pointer ${
                    selectedSeverity === sev
                      ? sev === 'CRITICAL'
                        ? 'bg-rose-600 text-white shadow-danger-glow'
                        : sev === 'WARNING'
                        ? 'bg-amber-600 text-white shadow-warning-glow'
                        : sev === 'SUCCESS'
                        ? 'bg-emerald-600 text-white shadow-success-glow'
                        : 'bg-indigo-600 text-white shadow-primary-glow'
                      : 'bg-slate-100 dark:bg-navy-850 text-slate-600 dark:text-navy-400 hover:text-slate-900 dark:hover:text-white border border-slate-200 dark:border-white/5'
                  }`}
                >
                  {sev}
                </button>
              ))}
            </div>
          </div>

          {/* Event Stream List */}
          <div className="space-y-2 max-h-[560px] overflow-y-auto pr-1">
            {filteredEvents.length === 0 ? (
              <EmptyState
                icon={<Radio className="w-6 h-6 text-slate-400 dark:text-navy-400" />}
                title="No Events Found"
                description="No matching telemetry events recorded under current filter criteria."
                className="py-12 border-0 bg-transparent"
              />
            ) : (
              filteredEvents.map((evt) => (
                <div
                  key={evt.event_id}
                  onClick={() => {
                    setSelectedEvent(evt);
                    if (evt.transaction_id) setSelectedTxId(evt.transaction_id);
                  }}
                  className="p-3.5 rounded-xl bg-white dark:bg-navy-850/80 border border-slate-200 dark:border-white/[0.06] hover:border-indigo-400/50 dark:hover:border-cyber-indigo/50 cursor-pointer transition space-y-1.5 text-xs font-mono shadow-sm dark:shadow-none"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <StatusBadge status={evt.severity} size="xs" />
                      <span className="text-slate-900 dark:text-white font-bold">{evt.event_type}</span>
                    </div>
                    <span className="text-slate-500 dark:text-navy-400 text-[10px]">
                      {new Date(evt.timestamp).toLocaleTimeString()}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-slate-500 dark:text-navy-400 pt-1">
                    <span className="truncate max-w-[280px]">
                      Source: <span className="text-slate-700 dark:text-navy-200 font-semibold">{evt.source}</span>
                      {evt.transaction_id && ` • Tx: ${evt.transaction_id.slice(0, 14)}...`}
                    </span>
                    <span className="text-indigo-600 dark:text-cyan-400 text-[10px] flex items-center gap-1 hover:underline font-bold">
                      <span>INSPECT</span>
                      <ArrowRight className="w-3 h-3" />
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </GlassCard>

        {/* Right Column: Live Evaluated Transactions Feed (5 Cols) */}
        <GlassCard className="lg:col-span-5 p-6 space-y-4" variant="elevated">
          <div className="flex items-center justify-between border-b border-slate-200/80 dark:border-white/[0.08] pb-3">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-cyber-indigo" />
              <h2 className="text-sm font-bold uppercase tracking-wider font-mono text-slate-900 dark:text-white">
                Live Transaction Stream
              </h2>
            </div>
            <span className="text-xs font-mono text-slate-500 dark:text-navy-400">{streamItems.length} records</span>
          </div>

          <div className="space-y-3 max-h-[640px] overflow-y-auto pr-1">
            {streamItems.length === 0 ? (
              <EmptyState
                icon={<Activity className="w-6 h-6 text-slate-400 dark:text-navy-400" />}
                title="Waiting for Transactions"
                description="Live agent transfers will stream here automatically upon evaluation."
                className="py-12 border-0 bg-transparent"
              />
            ) : (
              streamItems.map((tx) => (
                <div
                  key={tx.transaction_id}
                  onClick={() => setSelectedTxId(tx.transaction_id)}
                  className={`p-3.5 rounded-xl border cursor-pointer transition text-xs font-mono space-y-2 ${
                    selectedTxId === tx.transaction_id
                      ? 'bg-indigo-50/80 dark:bg-navy-800 border-indigo-500/50 dark:border-cyber-cyan shadow-sm dark:shadow-cyan-glow'
                      : 'bg-white dark:bg-navy-850/80 border-slate-200 dark:border-white/[0.06] hover:border-slate-300 dark:hover:border-white/20 shadow-sm dark:shadow-none'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <StatusBadge status={tx.decision} size="xs" />
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          tx.execution_mode === 'ONCHAIN'
                            ? 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/30'
                            : 'bg-slate-100 dark:bg-navy-900 text-slate-600 dark:text-navy-400 border border-slate-200 dark:border-white/5'
                        }`}
                      >
                        {tx.execution_mode || (tx.is_mock_simulation ? 'SIMULATION' : 'ONCHAIN')}
                      </span>
                    </div>
                    <span className="text-emerald-600 dark:text-emerald-400 font-bold">{tx.amount.toFixed(2)} NEAR</span>
                  </div>

                  <div className="flex items-center gap-1.5 text-xs text-slate-600 dark:text-navy-300">
                    <span className="truncate max-w-[120px]">{tx.sender}</span>
                    <ArrowRight className="w-3 h-3 text-slate-400 dark:text-navy-500 flex-shrink-0" />
                    <span className="text-slate-900 dark:text-white font-bold truncate max-w-[120px]">{tx.recipient}</span>
                  </div>

                  <div className="flex items-center justify-between text-[10px] text-slate-500 dark:text-navy-400 pt-1 border-t border-slate-200 dark:border-white/[0.06]">
                    <span className="truncate max-w-[140px]">{tx.transaction_id}</span>
                    <div className="flex items-center gap-2">
                      <RiskIndicator score={tx.risk_score} size="sm" />
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </GlassCard>
      </div>

      {/* Event Details Inspection Modal */}
      {selectedEvent && (
        <Modal
          isOpen={true}
          onClose={() => setSelectedEvent(null)}
          title={`Event Inspection: ${selectedEvent.event_type}`}
        >
          <div className="space-y-4 font-mono text-xs">
            <div className="grid grid-cols-2 gap-3 p-3.5 rounded-xl bg-slate-50 dark:bg-navy-900 border border-slate-200 dark:border-white/[0.08]">
              <div>
                <span className="text-slate-500 dark:text-navy-500 text-[10px] block uppercase">EVENT ID</span>
                <span className="text-slate-900 dark:text-white font-bold">{selectedEvent.event_id}</span>
              </div>
              <div>
                <span className="text-slate-500 dark:text-navy-500 text-[10px] block uppercase">TIMESTAMP (UTC)</span>
                <span className="text-slate-700 dark:text-navy-300">{selectedEvent.timestamp}</span>
              </div>
              <div>
                <span className="text-slate-500 dark:text-navy-500 text-[10px] block uppercase">CATEGORY &amp; SEVERITY</span>
                <span className="text-emerald-600 dark:text-emerald-400 font-bold">
                  {selectedEvent.category.toUpperCase()} • {selectedEvent.severity}
                </span>
              </div>
              <div>
                <span className="text-slate-500 dark:text-navy-500 text-[10px] block uppercase">SOURCE SUBSYSTEM</span>
                <span className="text-slate-800 dark:text-white">{selectedEvent.source}</span>
              </div>
            </div>

            {selectedEvent.transaction_id && (
              <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-navy-900 border border-slate-200 dark:border-white/[0.08] flex items-center justify-between">
                <div>
                  <span className="text-slate-500 dark:text-navy-500 text-[10px] block uppercase">ASSOCIATED TRANSACTION ID</span>
                  <span className="text-cyan-700 dark:text-cyan-400 font-bold">{selectedEvent.transaction_id}</span>
                </div>
                {selectedEvent.payload?.explorer_url && (
                  <a
                    href={selectedEvent.payload.explorer_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-100 dark:bg-navy-800 border border-slate-200 dark:border-white/10 text-cyan-700 dark:text-cyan-300 text-xs font-bold hover:bg-slate-200 dark:hover:bg-navy-750 transition"
                  >
                    <span>NEARBLOCKS</span>
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                )}
              </div>
            )}

            <div>
              <span className="text-slate-500 dark:text-navy-400 text-[11px] font-bold block mb-1">
                REDACTED EVENT PAYLOAD JSON:
              </span>
              <pre className="p-4 rounded-xl bg-slate-900 text-cyan-300 dark:bg-navy-950 border border-slate-800 dark:border-white/[0.08] text-[11px] overflow-x-auto max-h-[300px]">
                {JSON.stringify(selectedEvent.payload, null, 2)}
              </pre>
            </div>
          </div>
        </Modal>
      )}
    </PageTransition>
  );
};
