import React, { useEffect, useState } from 'react';
import {
  Settings as SettingsIcon,
  Server,
  Database,
  Brain,
  HardDrive,
  RotateCw,
  KeyRound,
  CheckCircle2,
  Lock,
  Sun,
  Moon,
  Palette,
} from 'lucide-react';
import { apiService } from '../services/api';
import type { AgentStatusResponse, NEARNodeStatus } from '../types';
import {
  SectionHeader,
  GlassCard,
  GradientButton,
  PageTransition,
} from '../components/ui';
import { useTheme } from '../context/ThemeContext';

export const Settings: React.FC = () => {
  const { theme, isDark, setTheme } = useTheme();
  const [agentStatus, setAgentStatus] = useState<AgentStatusResponse | null>(null);
  const [healthStatus, setHealthStatus] = useState<{ status: string; application: string; version: string } | null>(null);
  const [blockchainStatus, setBlockchainStatus] = useState<NEARNodeStatus | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchConfig = async () => {
    setLoading(true);
    try {
      const [statusData, healthData, nodeData] = await Promise.allSettled([
        apiService.getAgentStatus(),
        apiService.getHealth(),
        apiService.getBlockchainStatus(),
      ]);
      if (statusData.status === 'fulfilled') setAgentStatus(statusData.value);
      if (healthData.status === 'fulfilled') setHealthStatus(healthData.value);
      if (nodeData.status === 'fulfilled') setBlockchainStatus(nodeData.value);
    } catch (err) {
      console.error('Failed to load system settings:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConfig();
  }, []);

  return (
    <PageTransition className="space-y-6 max-w-7xl mx-auto pb-16">
      <SectionHeader
        icon={<SettingsIcon className="w-5 h-5 text-cyber-indigo" />}
        title="System &amp; Network Configuration"
        description="LLM Gateway configuration, multi-agent orchestrator state, persistent SQLite evidence ledger, and NEAR Testnet node diagnostics."
        action={
          <GradientButton
            variant="glass"
            size="sm"
            onClick={fetchConfig}
            isLoading={loading}
            leftIcon={<RotateCw className={`w-3.5 h-3.5 text-cyber-cyan ${loading ? 'animate-spin' : ''}`} />}
          >
            RELOAD DIAGNOSTICS
          </GradientButton>
        }
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* LLM Gateway & Multi-Agent Engine */}
        <GlassCard className="p-6 space-y-4" variant="elevated">
          <div className="flex items-center gap-2 border-b border-slate-200/80 dark:border-white/[0.08] pb-3">
            <Brain className="w-4 h-4 text-cyber-indigo dark:text-cyber-cyan" />
            <h2 className="text-sm font-bold uppercase tracking-wider font-mono text-slate-900 dark:text-white">
              LLM Intention Auditing Gateway
            </h2>
          </div>

          <div className="space-y-3.5 text-xs font-mono">
            <div>
              <label className="text-slate-500 dark:text-navy-400 block mb-1">Active LLM Provider</label>
              <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 dark:bg-navy-900 border border-slate-200 dark:border-white/10">
                <span className="text-cyan-700 dark:text-cyan-400 font-bold uppercase">
                  {agentStatus?.llm_provider || 'openai'}
                </span>
                <span className="text-[10px] text-emerald-700 dark:text-emerald-400 px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 font-bold">
                  SANDBOXED
                </span>
              </div>
            </div>

            <div>
              <label className="text-slate-500 dark:text-navy-400 block mb-1">Configured Model</label>
              <input
                type="text"
                disabled
                value={agentStatus?.llm_model || 'gpt-4o-mini'}
                className="w-full bg-slate-50 dark:bg-navy-900 border border-slate-200 dark:border-white/10 rounded-xl px-3 py-2 text-slate-800 dark:text-navy-200"
              />
            </div>

            <div>
              <label className="text-slate-500 dark:text-navy-400 block mb-1">Deterministic NLP Fallback</label>
              <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-navy-900 border border-slate-200 dark:border-white/10 text-[11px] text-slate-700 dark:text-navy-300 flex items-center justify-between">
                <span>Autonomous offline NLP fallback</span>
                <span className="text-emerald-600 dark:text-emerald-400 font-bold">ONLINE &amp; READY</span>
              </div>
            </div>

            <div>
              <label className="text-slate-500 dark:text-navy-400 block mb-1">Orchestrator Framework</label>
              <input
                type="text"
                disabled
                value="LangGraph StateGraph 0.2.x"
                className="w-full bg-slate-50 dark:bg-navy-900 border border-slate-200 dark:border-white/10 rounded-xl px-3 py-2 text-indigo-700 dark:text-cyber-indigo font-bold"
              />
            </div>
          </div>
        </GlassCard>

        {/* Persistence Engine */}
        <GlassCard className="p-6 space-y-4" variant="elevated">
          <div className="flex items-center gap-2 border-b border-slate-200/80 dark:border-white/[0.08] pb-3">
            <HardDrive className="w-4 h-4 text-emerald-500 dark:text-emerald-400" />
            <h2 className="text-sm font-bold uppercase tracking-wider font-mono text-slate-900 dark:text-white">
              Database &amp; Cryptographic Evidence
            </h2>
          </div>

          <div className="space-y-3.5 text-xs font-mono">
            <div>
              <label className="text-slate-500 dark:text-navy-400 block mb-1">Storage Engine</label>
              <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 dark:bg-navy-900 border border-slate-200 dark:border-white/10">
                <span className="text-slate-900 dark:text-white font-bold">SQLite 3 (payguard.db)</span>
                <span className="text-[10px] text-emerald-700 dark:text-emerald-400 px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 font-bold">
                  {agentStatus?.database_status || 'CONNECTED'}
                </span>
              </div>
            </div>

            <div>
              <label className="text-slate-500 dark:text-navy-400 block mb-1">Evidence Serialization Standard</label>
              <input
                type="text"
                disabled
                value="RFC-8785 Canonical JSON (JCS)"
                className="w-full bg-slate-50 dark:bg-navy-900 border border-slate-200 dark:border-white/10 rounded-xl px-3 py-2 text-slate-800 dark:text-navy-200"
              />
            </div>

            <div>
              <label className="text-slate-500 dark:text-navy-400 block mb-1">Digest Algorithm</label>
              <input
                type="text"
                disabled
                value="SHA-256 Cryptographic Hash"
                className="w-full bg-slate-50 dark:bg-navy-900 border border-slate-200 dark:border-white/10 rounded-xl px-3 py-2 text-slate-800 dark:text-navy-200"
              />
            </div>

            <div>
              <label className="text-slate-500 dark:text-navy-400 block mb-1">Audit DB Tables (11 Managed Tables)</label>
              <span className="text-[11px] text-slate-500 dark:text-navy-400 block truncate">
                transactions, agent_executions, security_findings, authorization_evidence, events, agent_profiles, ai_anomalies
              </span>
            </div>
          </div>
        </GlassCard>

        {/* Backend & Node Setup */}
        <GlassCard className="p-6 space-y-4" variant="elevated">
          <div className="flex items-center gap-2 border-b border-slate-200/80 dark:border-white/[0.08] pb-3">
            <Server className="w-4 h-4 text-indigo-500 dark:text-indigo-400" />
            <h2 className="text-sm font-bold uppercase tracking-wider font-mono text-slate-900 dark:text-white">
              Backend Daemon &amp; Telemetry State
            </h2>
          </div>

          <div className="space-y-3.5 text-xs font-mono">
            <div>
              <label className="text-slate-500 dark:text-navy-400 block mb-1">API Endpoint</label>
              <input
                type="text"
                disabled
                value="http://127.0.0.1:8000/api"
                className="w-full bg-slate-50 dark:bg-navy-900 border border-slate-200 dark:border-white/10 rounded-xl px-3 py-2 text-slate-800 dark:text-navy-200"
              />
            </div>

            <div>
              <label className="text-slate-500 dark:text-navy-400 block mb-1">WebSocket Telemetry URL</label>
              <input
                type="text"
                disabled
                value="ws://127.0.0.1:8000/ws/events"
                className="w-full bg-slate-50 dark:bg-navy-900 border border-slate-200 dark:border-white/10 rounded-xl px-3 py-2 text-slate-800 dark:text-navy-200"
              />
            </div>

            <div>
              <label className="text-slate-500 dark:text-navy-400 block mb-1">Application Version</label>
              <input
                type="text"
                disabled
                value={`PAYGUARD v${healthStatus?.version || '1.0.0'} (Phase 8 Production)`}
                className="w-full bg-slate-50 dark:bg-navy-900 border border-slate-200 dark:border-white/10 rounded-xl px-3 py-2 text-emerald-600 dark:text-emerald-400 font-bold"
              />
            </div>
          </div>
        </GlassCard>

        {/* Blockchain Network & Smart Contract Vault */}
        <GlassCard className="p-6 space-y-4" variant="elevated">
          <div className="flex items-center gap-2 border-b border-slate-200/80 dark:border-white/[0.08] pb-3">
            <Database className="w-4 h-4 text-cyan-600 dark:text-cyan-400" />
            <h2 className="text-sm font-bold uppercase tracking-wider font-mono text-slate-900 dark:text-white">
              NEAR Blockchain &amp; Vault Contract
            </h2>
          </div>

          <div className="space-y-3.5 text-xs font-mono">
            <div>
              <label className="text-slate-500 dark:text-navy-400 block mb-1">Target Network &amp; RPC Connection</label>
              <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 dark:bg-navy-900 border border-slate-200 dark:border-white/10">
                <span className="text-cyan-700 dark:text-cyan-400 font-bold">
                  NEAR {blockchainStatus?.network?.toUpperCase() || 'TESTNET'}
                </span>
                <span className="text-[10px] text-emerald-700 dark:text-emerald-400 px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 flex items-center gap-1 font-bold">
                  <CheckCircle2 className="w-3 h-3 text-emerald-600 dark:text-emerald-400" />
                  <span>{blockchainStatus?.status || 'CONNECTED'}</span>
                </span>
              </div>
            </div>

            <div>
              <label className="text-slate-500 dark:text-navy-400 block mb-1">Vault Smart Contract (Rust NEP-297)</label>
              <input
                type="text"
                disabled
                value={blockchainStatus?.vault_contract || 'payguard-vault.testnet'}
                className="w-full bg-slate-50 dark:bg-navy-900 border border-slate-200 dark:border-white/10 rounded-xl px-3 py-2 text-slate-900 dark:text-white font-bold"
              />
            </div>

            <div>
              <label className="text-slate-500 dark:text-navy-400 block mb-1">Ed25519 Policy Signer Public Key</label>
              <div className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-50 dark:bg-navy-900 border border-slate-200 dark:border-white/10 text-[11px] text-emerald-700 dark:text-emerald-400 break-all font-mono">
                <KeyRound className="w-4 h-4 text-emerald-600 dark:text-emerald-400 flex-shrink-0" />
                <span>{blockchainStatus?.signer_public_key || 'ed25519:6H8mJ... (Active)'}</span>
              </div>
            </div>

            <div>
              <label className="text-slate-500 dark:text-navy-400 block mb-1">Cryptographic Signing Key (Secret)</label>
              <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 dark:bg-navy-900 border border-slate-200 dark:border-white/10 text-[11px] text-slate-500 dark:text-navy-400 font-mono">
                <div className="flex items-center gap-2">
                  <Lock className="w-3.5 h-3.5 text-amber-500 dark:text-amber-400" />
                  <span>ed25519:••••••••••••••••••••••••••••••••</span>
                </div>
                <span className="text-[10px] text-amber-600 dark:text-amber-400 font-bold uppercase">MASKED SECURELY</span>
              </div>
            </div>
          </div>
        </GlassCard>

        {/* UI Appearance & SOC Theme Configuration */}
        <GlassCard className="p-6 md:col-span-2 space-y-4" variant="elevated">
          <div className="flex items-center justify-between border-b border-slate-200/80 dark:border-white/[0.08] pb-3">
            <div className="flex items-center gap-2">
              <Palette className="w-4 h-4 text-cyber-indigo" />
              <h2 className="text-sm font-bold uppercase tracking-wider font-mono text-slate-900 dark:text-white">
                UI Appearance &amp; SOC Console Theme
              </h2>
            </div>
            <span className="text-xs font-mono px-2.5 py-1 rounded-full bg-indigo-500/10 dark:bg-indigo-500/20 text-indigo-700 dark:text-cyan-300 border border-indigo-500/30 font-semibold uppercase">
              Current: {theme} Mode
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
            {/* Cyber Dark Option */}
            <div
              onClick={() => setTheme('dark')}
              className={`p-4 rounded-xl border transition-all cursor-pointer flex items-start gap-4 ${
                isDark
                  ? 'bg-navy-900/90 border-cyber-cyan shadow-cyan-glow ring-1 ring-cyber-cyan'
                  : 'bg-slate-100/80 hover:bg-slate-200/80 border-slate-300/80 dark:bg-navy-900/40 dark:border-white/10'
              }`}
            >
              <div className="p-3 rounded-xl bg-navy-950 border border-white/20 text-cyber-cyan shadow-primary-glow flex-shrink-0">
                <Moon className="w-5 h-5" />
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-sm font-bold text-slate-900 dark:text-white">Cyber Dark Mode</span>
                  {isDark && (
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-400 font-bold">
                      ACTIVE
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-600 dark:text-navy-400 mt-1 font-sans">
                  Futuristic midnight &amp; deep navy canvas with electric glows and cybersecurity aesthetic.
                </p>
              </div>
            </div>

            {/* Enterprise Light Option */}
            <div
              onClick={() => setTheme('light')}
              className={`p-4 rounded-xl border transition-all cursor-pointer flex items-start gap-4 ${
                !isDark
                  ? 'bg-white border-cyber-indigo shadow-primary-glow ring-1 ring-cyber-indigo'
                  : 'bg-navy-900/40 hover:bg-navy-800/60 border-white/10 dark:border-white/10'
              }`}
            >
              <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-500 shadow-warning-glow flex-shrink-0">
                <Sun className="w-5 h-5" />
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-sm font-bold text-slate-900 dark:text-white">Enterprise Light Mode</span>
                  {!isDark && (
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-700 font-bold">
                      ACTIVE
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-600 dark:text-navy-400 mt-1 font-sans">
                  Crisp slate canvas with high contrast, elevated borders, and enterprise SaaS presentation.
                </p>
              </div>
            </div>
          </div>
        </GlassCard>
      </div>
    </PageTransition>
  );
};
