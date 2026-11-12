import React, { useEffect, useState } from 'react';
import {
  ShieldCheck,
  ShieldX,
  Clock,
  Coins,
  Send,
  RefreshCw,
  AlertTriangle,
  ExternalLink,
  Info,
  Activity,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { apiService } from '../services/api';
import type {
  SecurityMetricsResponse,
  TransactionAnalysisResponse,
  TransactionRecord,
} from '../types';
import { Badge } from '../components/common/Badge';
import { RiskMeter } from '../components/common/RiskMeter';
import { PolicyPill } from '../components/common/PolicyPill';
import { Modal } from '../components/common/Modal';

export const Overview: React.FC = () => {
  const [metrics, setMetrics] = useState<SecurityMetricsResponse | null>(null);
  const [transactions, setTransactions] = useState<TransactionRecord[]>([]);
  const [selectedTx, setSelectedTx] = useState<TransactionRecord | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Simulation form state
  const [sender, setSender] = useState('agent-executor.near');
  const [recipient, setRecipient] = useState('oracle.near');
  const [amount, setAmount] = useState('5.0');
  const [purpose, setPurpose] = useState('Oracle computation payment');
  const [simulating, setSimulating] = useState(false);
  const [simulationResult, setSimulationResult] = useState<TransactionAnalysisResponse | null>(null);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [metricsData, txData] = await Promise.all([
        apiService.getSecurityMetrics(),
        apiService.getTransactions(10),
      ]);
      setMetrics(metricsData);
      setTransactions(txData);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleSimulate = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setSimulating(true);
    setSimulationResult(null);
    try {
      const numAmount = parseFloat(amount);
      if (isNaN(numAmount) || numAmount <= 0) {
        alert('Please specify a positive numerical amount.');
        setSimulating(false);
        return;
      }
      const res = await apiService.analyzeTransaction({
        sender,
        recipient,
        amount: numAmount,
        currency: 'NEAR',
        purpose,
        agent_id: sender,
      });
      setSimulationResult(res);
      await fetchData();
    } catch (err: any) {
      alert(`Simulation failed: ${err.response?.data?.message || err.message}`);
    } finally {
      setSimulating(false);
    }
  };

  const applyPreset = (preset: {
    sender: string;
    recipient: string;
    amount: string;
    purpose: string;
  }) => {
    setSender(preset.sender);
    setRecipient(preset.recipient);
    setAmount(preset.amount);
    setPurpose(preset.purpose);
    setSimulationResult(null);
  };

  // Mock chart activity data derived from metrics
  const chartData = [
    { time: '10:00', volume: 12.5, risk: 10 },
    { time: '10:30', volume: 28.0, risk: 18 },
    { time: '11:00', volume: 15.0, risk: 85 },
    { time: '11:30', volume: 45.0, risk: 45 },
    { time: '12:00', volume: 30.0, risk: 20 },
    { time: '12:30', volume: 65.0, risk: 95 },
    { time: '13:00', volume: 22.0, risk: 15 },
  ];

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Page Title & Status Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <span>Security Operations Dashboard</span>
          </h1>
          <p className="text-sm text-charcoal-400 mt-1">
            Real-time deterministic policy enforcement and AI risk telemetry for autonomous agents.
          </p>
        </div>

        <button
          onClick={fetchData}
          className="flex items-center gap-2 px-3 py-2 rounded-lg bg-charcoal-900 border border-charcoal-750 hover:border-charcoal-600 text-xs font-mono text-charcoal-300 transition w-fit"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-emerald-400 ${isLoading ? 'animate-spin' : ''}`} />
          <span>REFRESH METRICS</span>
        </button>
      </div>

      {/* Demo Mode Notice */}
      <div className="p-3.5 rounded-lg bg-forest-950/80 border border-emerald-800/40 text-xs text-emerald-300 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Info className="w-4 h-4 text-emerald-400 flex-shrink-0" />
          <span>
            <strong>NEAR Hackathon 2026 Phase 1:</strong> Running in deterministic simulation mode.
            Policies are enforced locally; transactions are safely validated before future smart contract execution.
          </span>
        </div>
        <span className="font-mono text-[11px] text-emerald-400/80 hidden sm:inline">DEMO DATASET ACTIVE</span>
      </div>

      {/* Metric KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Total Monitored */}
        <div className="payguard-panel p-5">
          <div className="flex items-center justify-between text-charcoal-400">
            <span className="text-xs uppercase font-mono tracking-wider">Monitored</span>
            <Activity className="w-4 h-4 text-charcoal-400" />
          </div>
          <div className="mt-3">
            <div className="text-3xl font-bold font-mono text-white">
              {metrics ? metrics.total_monitored : '—'}
            </div>
            <p className="text-[11px] text-charcoal-400 mt-1 font-mono">Agent transactions</p>
          </div>
        </div>

        {/* Approved */}
        <div className="payguard-panel p-5">
          <div className="flex items-center justify-between text-emerald-400">
            <span className="text-xs uppercase font-mono tracking-wider">Approved</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-3">
            <div className="text-3xl font-bold font-mono text-emerald-400">
              {metrics ? metrics.approved_count : '—'}
            </div>
            <p className="text-[11px] text-charcoal-400 mt-1 font-mono">Passed all policies</p>
          </div>
        </div>

        {/* Blocked */}
        <div className="payguard-panel p-5">
          <div className="flex items-center justify-between text-rose-400">
            <span className="text-xs uppercase font-mono tracking-wider">Blocked</span>
            <ShieldX className="w-4 h-4 text-rose-400" />
          </div>
          <div className="mt-3">
            <div className="text-3xl font-bold font-mono text-rose-400">
              {metrics ? metrics.blocked_count : '—'}
            </div>
            <p className="text-[11px] text-charcoal-400 mt-1 font-mono">Threats prevented</p>
          </div>
        </div>

        {/* Pending Approvals */}
        <div className="payguard-panel p-5">
          <div className="flex items-center justify-between text-amber-400">
            <span className="text-xs uppercase font-mono tracking-wider">Warn / Pending</span>
            <Clock className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-3">
            <div className="text-3xl font-bold font-mono text-amber-400">
              {metrics ? metrics.pending_approvals : '—'}
            </div>
            <p className="text-[11px] text-charcoal-400 mt-1 font-mono">Awaiting human sign-off</p>
          </div>
        </div>

        {/* Protected NEAR Volume */}
        <div className="payguard-panel p-5">
          <div className="flex items-center justify-between text-emerald-300">
            <span className="text-xs uppercase font-mono tracking-wider">Protected Volume</span>
            <Coins className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-3">
            <div className="text-3xl font-bold font-mono text-white">
              {metrics ? `${metrics.protected_near_volume} Ⓝ` : '—'}
            </div>
            <p className="text-[11px] text-emerald-400/80 mt-1 font-mono">Malicious drain saved</p>
          </div>
        </div>
      </div>

      {/* Main Grid: Interactive Simulation + Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Interactive Transaction Simulator (5 cols) */}
        <div className="lg:col-span-5 payguard-panel p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-charcoal-800 pb-3">
              <div className="flex items-center gap-2">
                <Send className="w-4 h-4 text-emerald-400" />
                <h2 className="text-sm font-bold uppercase tracking-wider font-mono text-white">
                  Agent Transaction Simulator
                </h2>
              </div>
              <span className="text-[11px] font-mono text-emerald-400 bg-forest-950 px-2 py-0.5 rounded border border-emerald-800/50">
                LIVE ENGINE
              </span>
            </div>

            <p className="text-xs text-charcoal-400 mt-2">
              Dispatch an agent transaction to test deterministic policy decisions and risk calculation.
            </p>

            {/* Quick Presets */}
            <div className="mt-4 space-y-1.5">
              <span className="text-[11px] font-mono text-charcoal-400">Quick Test Scenarios:</span>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() =>
                    applyPreset({
                      sender: 'agent-alpha.near',
                      recipient: 'oracle.near',
                      amount: '3.5',
                      purpose: 'Automated price query fee',
                    })
                  }
                  className="text-left px-2.5 py-1.5 rounded bg-charcoal-850 border border-charcoal-750 hover:border-emerald-600/50 text-[11px] text-charcoal-300 transition"
                >
                  <span className="text-emerald-400 font-semibold block">1. Safe Transfer</span>
                  <span className="text-charcoal-400 truncate block">3.5 NEAR to oracle.near</span>
                </button>

                <button
                  type="button"
                  onClick={() =>
                    applyPreset({
                      sender: 'agent-alpha.near',
                      recipient: 'malicious-drainer.near',
                      amount: '25.0',
                      purpose: 'Emergency liquidity transfer',
                    })
                  }
                  className="text-left px-2.5 py-1.5 rounded bg-charcoal-850 border border-charcoal-750 hover:border-rose-600/50 text-[11px] text-charcoal-300 transition"
                >
                  <span className="text-rose-400 font-semibold block">2. Blocked Malicious</span>
                  <span className="text-charcoal-400 truncate block">To malicious-drainer.near</span>
                </button>

                <button
                  type="button"
                  onClick={() =>
                    applyPreset({
                      sender: 'agent-beta.near',
                      recipient: 'unregistered-arbitrage-bot.near',
                      amount: '35.0',
                      purpose: 'DEX flash arbitrage swap',
                    })
                  }
                  className="text-left px-2.5 py-1.5 rounded bg-charcoal-850 border border-charcoal-750 hover:border-amber-600/50 text-[11px] text-charcoal-300 transition"
                >
                  <span className="text-amber-400 font-semibold block">3. Unknown Recipient</span>
                  <span className="text-charcoal-400 truncate block">Requires Human WARN</span>
                </button>

                <button
                  type="button"
                  onClick={() =>
                    applyPreset({
                      sender: 'agent-alpha.near',
                      recipient: 'treasury.payguard.near',
                      amount: '120.0',
                      purpose: 'Treasury rebalance above ceiling',
                    })
                  }
                  className="text-left px-2.5 py-1.5 rounded bg-charcoal-850 border border-charcoal-750 hover:border-rose-600/50 text-[11px] text-charcoal-300 transition"
                >
                  <span className="text-rose-400 font-semibold block">4. Exceeds Limit</span>
                  <span className="text-charcoal-400 truncate block">120 NEAR &gt; 50 max</span>
                </button>
              </div>
            </div>

            {/* Input Form */}
            <form onSubmit={handleSimulate} className="mt-4 space-y-3">
              <div>
                <label className="text-[11px] font-mono text-charcoal-400 block mb-1">
                  Sender Account
                </label>
                <input
                  type="text"
                  value={sender}
                  onChange={(e) => setSender(e.target.value)}
                  className="w-full bg-charcoal-950 border border-charcoal-750 rounded-lg px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-emerald-500"
                  required
                />
              </div>

              <div>
                <label className="text-[11px] font-mono text-charcoal-400 block mb-1">
                  Recipient Account
                </label>
                <input
                  type="text"
                  value={recipient}
                  onChange={(e) => setRecipient(e.target.value)}
                  className="w-full bg-charcoal-950 border border-charcoal-750 rounded-lg px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-emerald-500"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] font-mono text-charcoal-400 block mb-1">
                    Amount (NEAR)
                  </label>
                  <input
                    type="number"
                    step="0.001"
                    min="0.001"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    className="w-full bg-charcoal-950 border border-charcoal-750 rounded-lg px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-emerald-500"
                    required
                  />
                </div>
                <div>
                  <label className="text-[11px] font-mono text-charcoal-400 block mb-1">
                    Currency
                  </label>
                  <input
                    type="text"
                    value="NEAR"
                    disabled
                    className="w-full bg-charcoal-900 border border-charcoal-800 rounded-lg px-3 py-2 text-xs font-mono text-charcoal-400 cursor-not-allowed"
                  />
                </div>
              </div>

              <div>
                <label className="text-[11px] font-mono text-charcoal-400 block mb-1">
                  Task Intent / Purpose
                </label>
                <input
                  type="text"
                  value={purpose}
                  onChange={(e) => setPurpose(e.target.value)}
                  placeholder="Task explanation..."
                  className="w-full bg-charcoal-950 border border-charcoal-750 rounded-lg px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-emerald-500"
                />
              </div>

              <button
                type="submit"
                disabled={simulating}
                className="w-full mt-2 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-mono font-semibold text-xs tracking-wider transition shadow-shield-glow flex items-center justify-center gap-2"
              >
                {simulating ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>EVALUATING POLICIES...</span>
                  </>
                ) : (
                  <>
                    <ShieldCheck className="w-3.5 h-3.5" />
                    <span>EVALUATE TRANSACTION</span>
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Real-time simulation feedback card */}
          {simulationResult && (
            <div className="mt-4 p-3.5 rounded-lg bg-charcoal-850 border border-charcoal-700 space-y-2 animate-fade-in">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono text-charcoal-400">Verdict</span>
                <Badge type={simulationResult.decision} />
              </div>

              <div className="flex items-center justify-between text-xs">
                <span className="text-charcoal-400">Risk Assessment</span>
                <RiskMeter score={simulationResult.risk_score} />
              </div>

              <div className="pt-2 border-t border-charcoal-750 text-[11px] text-charcoal-300 space-y-1">
                {simulationResult.reasons.map((r, i) => (
                  <div key={i} className="flex items-start gap-1.5">
                    <span className="text-emerald-400 font-bold">•</span>
                    <span>{r}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Transaction Volume & Risk Velocity Chart (7 cols) */}
        <div className="lg:col-span-7 payguard-panel p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-charcoal-800 pb-3">
              <div>
                <h2 className="text-sm font-bold uppercase tracking-wider font-mono text-white">
                  Monitored Volume &amp; Threat Telemetry
                </h2>
                <p className="text-xs text-charcoal-400 mt-0.5">
                  Chronological transaction throughput and rolling risk index
                </p>
              </div>
              <div className="flex items-center gap-4 text-xs font-mono">
                <div className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-emerald-500" />
                  <span className="text-charcoal-400">Volume (NEAR)</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-rose-500" />
                  <span className="text-charcoal-400">Risk Score</span>
                </div>
              </div>
            </div>

            <div className="h-64 mt-6">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="volumeGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10B981" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#10B981" stopOpacity={0.0} />
                    </linearGradient>
                    <linearGradient id="riskGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#EF4444" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#EF4444" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#161F27" />
                  <XAxis dataKey="time" stroke="#7F93A7" fontSize={11} tickLine={false} />
                  <YAxis stroke="#7F93A7" fontSize={11} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0C1115',
                      border: '1px solid #263442',
                      borderRadius: '8px',
                      fontSize: '12px',
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="volume"
                    stroke="#10B981"
                    fillOpacity={1}
                    fill="url(#volumeGrad)"
                    strokeWidth={2}
                    name="Volume (NEAR)"
                  />
                  <Area
                    type="monotone"
                    dataKey="risk"
                    stroke="#EF4444"
                    fillOpacity={1}
                    fill="url(#riskGrad)"
                    strokeWidth={2}
                    name="Risk Score"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Invariant callout */}
          <div className="mt-4 p-3 rounded-lg bg-charcoal-900 border border-charcoal-800 text-xs font-mono text-charcoal-400 flex items-center justify-between">
            <span className="text-emerald-400 font-semibold">Core Security Invariant:</span>
            <span>AI analyzes • Policy engine enforces • Smart contract protects</span>
          </div>
        </div>
      </div>

      {/* Lower Section: Recent Transactions & Security Alerts Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Recent Monitored Transactions (8 cols) */}
        <div className="lg:col-span-8 payguard-panel p-6">
          <div className="flex items-center justify-between border-b border-charcoal-800 pb-4">
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold uppercase tracking-wider font-mono text-white">
                Recent Monitored Transactions
              </h2>
              <span className="text-xs font-mono text-charcoal-400">({transactions.length})</span>
            </div>
            <a
              href="/transactions"
              className="text-xs font-mono text-emerald-400 hover:text-emerald-300 flex items-center gap-1"
            >
              <span>VIEW ALL</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>

          <div className="overflow-x-auto mt-4">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="text-charcoal-400 border-b border-charcoal-800 pb-2">
                  <th className="py-2.5 font-normal">DECISION</th>
                  <th className="py-2.5 font-normal">SENDER</th>
                  <th className="py-2.5 font-normal">RECIPIENT</th>
                  <th className="py-2.5 font-normal">AMOUNT</th>
                  <th className="py-2.5 font-normal">RISK SCORE</th>
                  <th className="py-2.5 font-normal text-right">DETAILS</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-charcoal-800/60">
                {transactions.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-6 text-center text-charcoal-400">
                      No transactions recorded yet. Use the simulator above to submit one.
                    </td>
                  </tr>
                ) : (
                  transactions.slice(0, 6).map((tx) => (
                    <tr
                      key={tx.transaction_id}
                      onClick={() => setSelectedTx(tx)}
                      className="hover:bg-charcoal-850/50 cursor-pointer transition"
                    >
                      <td className="py-3">
                        <Badge type={tx.decision} size="sm" />
                      </td>
                      <td className="py-3 text-charcoal-300 max-w-[120px] truncate" title={tx.sender}>
                        {tx.sender}
                      </td>
                      <td className="py-3 text-white max-w-[140px] truncate" title={tx.recipient}>
                        {tx.recipient}
                      </td>
                      <td className="py-3 text-emerald-400 font-bold">
                        {tx.amount.toFixed(2)} NEAR
                      </td>
                      <td className="py-3">
                        <RiskMeter score={tx.risk_score} />
                      </td>
                      <td className="py-3 text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedTx(tx);
                          }}
                          className="px-2 py-1 rounded bg-charcoal-800 hover:bg-charcoal-700 text-charcoal-300 text-[11px]"
                        >
                          INSPECT
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Security Alerts Stream (4 cols) */}
        <div className="lg:col-span-4 payguard-panel p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-charcoal-800 pb-4">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-400" />
                <h2 className="text-sm font-bold uppercase tracking-wider font-mono text-white">
                  Security Alerts
                </h2>
              </div>
              <span className="text-[11px] font-mono text-rose-400 bg-rose-950/60 px-2 py-0.5 rounded border border-rose-800/40">
                DEFENSE FEED
              </span>
            </div>

            <div className="mt-4 space-y-3 overflow-y-auto max-h-[380px] pr-1">
              {!metrics || metrics.recent_alerts.length === 0 ? (
                <div className="py-8 text-center text-charcoal-400 text-xs">
                  No active security alerts.
                </div>
              ) : (
                metrics.recent_alerts.map((alert) => (
                  <div
                    key={alert.id}
                    className="p-3 rounded-lg bg-charcoal-850 border border-charcoal-750 text-xs space-y-1 hover:border-charcoal-700 transition"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-white truncate max-w-[180px]">
                        {alert.title}
                      </span>
                      <span
                        className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${
                          alert.severity === 'CRITICAL'
                            ? 'bg-rose-950 text-rose-400 border border-rose-800'
                            : 'bg-amber-950 text-amber-400 border border-amber-800'
                        }`}
                      >
                        {alert.severity}
                      </span>
                    </div>
                    <p className="text-charcoal-400 text-[11px] line-clamp-2">
                      {alert.description}
                    </p>
                    {alert.amount && (
                      <div className="text-[10px] font-mono text-emerald-400/90 pt-1 flex items-center justify-between">
                        <span>Intercepted: {alert.amount} NEAR</span>
                        <span className="text-charcoal-400">{alert.recipient}</span>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-charcoal-800 text-[11px] font-mono text-charcoal-400 text-center">
            Automated Blocklist updates active
          </div>
        </div>
      </div>

      {/* Transaction Details Modal */}
      {selectedTx && (
        <Modal
          isOpen={!!selectedTx}
          onClose={() => setSelectedTx(null)}
          title={`Transaction Security Audit — ${selectedTx.transaction_id}`}
        >
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 rounded-lg bg-charcoal-850 border border-charcoal-750">
              <div>
                <span className="text-xs text-charcoal-400 block font-mono">ENFORCEMENT DECISION</span>
                <Badge type={selectedTx.decision} className="mt-1" />
              </div>
              <div className="text-right">
                <span className="text-xs text-charcoal-400 block font-mono">RISK SCORE</span>
                <div className="mt-1 flex items-center justify-end">
                  <RiskMeter score={selectedTx.risk_score} />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs font-mono">
              <div className="p-2.5 rounded bg-charcoal-850 border border-charcoal-800">
                <span className="text-charcoal-400 block">Sender Account</span>
                <span className="text-white font-bold truncate block">{selectedTx.sender}</span>
              </div>
              <div className="p-2.5 rounded bg-charcoal-850 border border-charcoal-800">
                <span className="text-charcoal-400 block">Recipient Account</span>
                <span className="text-white font-bold truncate block">{selectedTx.recipient}</span>
              </div>
              <div className="p-2.5 rounded bg-charcoal-850 border border-charcoal-800">
                <span className="text-charcoal-400 block">Amount</span>
                <span className="text-emerald-400 font-bold block">
                  {selectedTx.amount} {selectedTx.currency}
                </span>
              </div>
              <div className="p-2.5 rounded bg-charcoal-850 border border-charcoal-800">
                <span className="text-charcoal-400 block">Requires Approval</span>
                <span className="text-white font-bold block">
                  {selectedTx.requires_approval ? 'YES (Human In Loop)' : 'NO'}
                </span>
              </div>
            </div>

            {selectedTx.purpose && (
              <div className="p-2.5 rounded bg-charcoal-850 border border-charcoal-800 text-xs">
                <span className="text-charcoal-400 block font-mono mb-1">Declared Intent</span>
                <span className="text-charcoal-200">{selectedTx.purpose}</span>
              </div>
            )}

            <div>
              <span className="text-xs font-mono uppercase text-charcoal-400 tracking-wider block mb-2">
                Deterministic Policy Checks
              </span>
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(selectedTx.policy_checks).map(([name, status]) => (
                  <PolicyPill key={name} name={name} status={status} />
                ))}
              </div>
            </div>

            <div>
              <span className="text-xs font-mono uppercase text-charcoal-400 tracking-wider block mb-2">
                Audit Reasons &amp; Violations
              </span>
              <div className="p-3 rounded bg-charcoal-850 border border-charcoal-800 space-y-1.5 text-xs text-charcoal-300">
                {selectedTx.reasons.map((reason, idx) => (
                  <div key={idx} className="flex items-start gap-2">
                    <span className="text-emerald-400 font-bold">•</span>
                    <span>{reason}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
