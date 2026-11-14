import React, { useEffect, useState } from 'react';
import {
  Sliders,
  Shield,
  AlertTriangle,
  Users,
  CheckCircle2,
  Trash2,
  Plus,
  Save,
} from 'lucide-react';
import { apiService } from '../services/api';
import type { PolicyConfig } from '../types';
import {
  SectionHeader,
  GlassCard,
  GradientButton,
  StatusBadge,
  PageTransition,
} from '../components/ui';

export const Policies: React.FC = () => {
  const [config, setConfig] = useState<PolicyConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [newBlocked, setNewBlocked] = useState('');
  const [newTrusted, setNewTrusted] = useState('');

  const fetchPolicies = async () => {
    setLoading(true);
    try {
      const data = await apiService.getPolicies();
      setConfig(data.config || (data as any).active_policy);
    } catch (err) {
      console.error('Failed to load policies:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPolicies();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!config) return;
    setSaving(true);
    setSaveSuccess(false);
    try {
      const res = await apiService.updatePolicies(config);
      setConfig(res.config || (res as any).active_policy);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      console.error('Failed to update policies:', err);
    } finally {
      setSaving(false);
    }
  };

  const addBlocked = () => {
    if (!newBlocked.trim() || !config) return;
    if (!config.blocked_recipients.includes(newBlocked.trim())) {
      setConfig({
        ...config,
        blocked_recipients: [...config.blocked_recipients, newBlocked.trim()],
      });
    }
    setNewBlocked('');
  };

  const removeBlocked = (addr: string) => {
    if (!config) return;
    setConfig({
      ...config,
      blocked_recipients: config.blocked_recipients.filter((a) => a !== addr),
    });
  };

  const addTrusted = () => {
    if (!newTrusted.trim() || !config) return;
    if (!config.trusted_recipients.includes(newTrusted.trim())) {
      setConfig({
        ...config,
        trusted_recipients: [...config.trusted_recipients, newTrusted.trim()],
      });
    }
    setNewTrusted('');
  };

  const removeTrusted = (addr: string) => {
    if (!config) return;
    setConfig({
      ...config,
      trusted_recipients: config.trusted_recipients.filter((a) => a !== addr),
    });
  };

  if (loading || !config) {
    return (
      <div className="py-24 text-center font-mono text-xs text-slate-500 dark:text-navy-400">
        Loading active security policy parameters...
      </div>
    );
  }

  return (
    <PageTransition className="space-y-6 max-w-7xl mx-auto pb-16">
      {/* Title */}
      <SectionHeader
        icon={<Sliders className="w-5 h-5 text-cyber-indigo" />}
        title="Deterministic Policy Configuration"
        description="Configure hard financial guardrails, cumulative spending limits, frequency thresholds, and trusted/blocked counterparty registries."
        action={
          <GradientButton
            variant="primary"
            size="sm"
            onClick={handleSave}
            isLoading={saving}
            leftIcon={saveSuccess ? <CheckCircle2 className="w-4 h-4 text-white" /> : <Save className="w-4 h-4 text-white" />}
          >
            {saveSuccess ? 'POLICIES UPDATED!' : 'APPLY POLICY UPDATES'}
          </GradientButton>
        }
      />

      <form onSubmit={handleSave} className="space-y-6">
        {/* Core Spending Limits */}
        <GlassCard className="p-6" variant="elevated">
          <div className="flex items-center gap-2 border-b border-slate-200/80 dark:border-white/[0.08] pb-3 mb-6">
            <Shield className="w-4 h-4 text-cyber-cyan" />
            <h2 className="text-sm font-bold uppercase tracking-wider font-mono text-slate-900 dark:text-white">
              Spending Ceilings &amp; Velocity Limits
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Max Per-TX Limit */}
            <div className="space-y-2">
              <label className="text-xs font-mono text-slate-500 dark:text-navy-400 block font-medium">
                MAX PER-TRANSACTION (NEAR)
              </label>
              <div className="flex items-center gap-3">
                <input
                  type="number"
                  step="1"
                  min="1"
                  max="10000"
                  value={config.max_tx_amount}
                  onChange={(e) =>
                    setConfig({ ...config, max_tx_amount: parseFloat(e.target.value) || 0 })
                  }
                  className="w-full bg-white dark:bg-navy-900 border border-slate-300 dark:border-white/10 rounded-xl px-3 py-2 text-sm font-mono text-slate-900 dark:text-white focus:outline-none focus:border-cyber-indigo focus:ring-1 focus:ring-cyber-indigo"
                />
              </div>
              <p className="text-[11px] text-slate-500 dark:text-navy-400 font-sans">
                Single transfers exceeding this limit trigger an immediate hard BLOCK.
              </p>
            </div>

            {/* Daily Cumulative Limit */}
            <div className="space-y-2">
              <label className="text-xs font-mono text-slate-500 dark:text-navy-400 block font-medium">
                DAILY ROLLING LIMIT (NEAR)
              </label>
              <div className="flex items-center gap-3">
                <input
                  type="number"
                  step="5"
                  min="5"
                  max="50000"
                  value={config.daily_spending_limit}
                  onChange={(e) =>
                    setConfig({ ...config, daily_spending_limit: parseFloat(e.target.value) || 0 })
                  }
                  className="w-full bg-white dark:bg-navy-900 border border-slate-300 dark:border-white/10 rounded-xl px-3 py-2 text-sm font-mono text-slate-900 dark:text-white focus:outline-none focus:border-cyber-indigo focus:ring-1 focus:ring-cyber-indigo"
                />
              </div>
              <p className="text-[11px] text-slate-500 dark:text-navy-400 font-sans">
                Cumulative 24-hour ceiling per agent sender with atomic TOCTOU protection.
              </p>
            </div>

            {/* Max Frequency / Min */}
            <div className="space-y-2">
              <label className="text-xs font-mono text-slate-500 dark:text-navy-400 block font-medium">
                MAX FREQUENCY (TX / MIN)
              </label>
              <div className="flex items-center gap-3">
                <input
                  type="number"
                  step="1"
                  min="1"
                  max="100"
                  value={config.max_tx_frequency_per_minute}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      max_tx_frequency_per_minute: parseInt(e.target.value) || 1,
                    })
                  }
                  className="w-full bg-white dark:bg-navy-900 border border-slate-300 dark:border-white/10 rounded-xl px-3 py-2 text-sm font-mono text-slate-900 dark:text-white focus:outline-none focus:border-cyber-indigo focus:ring-1 focus:ring-cyber-indigo"
                />
              </div>
              <p className="text-[11px] text-slate-500 dark:text-navy-400 font-sans">
                Prevents rapid loop exploits and autonomous high-frequency transaction drain.
              </p>
            </div>
          </div>
        </GlassCard>

        {/* Risk Thresholds & Heuristics */}
        <GlassCard className="p-6" variant="elevated">
          <div className="flex items-center gap-2 border-b border-slate-200/80 dark:border-white/[0.08] pb-3 mb-6">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            <h2 className="text-sm font-bold uppercase tracking-wider font-mono text-slate-900 dark:text-white">
              Dynamic Risk Scoring Thresholds
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-amber-500 dark:text-amber-400 font-semibold">Medium Risk Threshold (WARN)</span>
                <span className="text-slate-900 dark:text-white font-bold">{config.medium_risk_threshold} / 100</span>
              </div>
              <input
                type="range"
                min="10"
                max="60"
                value={config.medium_risk_threshold}
                onChange={(e) =>
                  setConfig({ ...config, medium_risk_threshold: parseInt(e.target.value) })
                }
                className="w-full accent-amber-500 cursor-pointer"
              />
              <p className="text-[11px] text-slate-500 dark:text-navy-400 font-sans">
                Scores at or above this threshold require human operator sign-off and vault escrow before execution.
              </p>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-rose-500 dark:text-rose-400 font-semibold">High Risk Threshold (HARD BLOCK)</span>
                <span className="text-slate-900 dark:text-white font-bold">{config.high_risk_threshold} / 100</span>
              </div>
              <input
                type="range"
                min="60"
                max="95"
                value={config.high_risk_threshold}
                onChange={(e) =>
                  setConfig({ ...config, high_risk_threshold: parseInt(e.target.value) })
                }
                className="w-full accent-rose-500 cursor-pointer"
              />
              <p className="text-[11px] text-slate-500 dark:text-navy-400 font-sans">
                Scores at or above this threshold trigger an irrevocable automated BLOCK.
              </p>
            </div>
          </div>

          {/* Toggle Switches */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-6 mt-6 border-t border-slate-200/80 dark:border-white/[0.08]">
            <label className="flex items-center gap-3 p-3.5 rounded-xl bg-slate-50 dark:bg-navy-850 border border-slate-200 dark:border-white/[0.06] cursor-pointer hover:border-slate-300 dark:hover:border-white/20 transition">
              <input
                type="checkbox"
                checked={config.require_approval_for_unknown}
                onChange={(e) =>
                  setConfig({ ...config, require_approval_for_unknown: e.target.checked })
                }
                className="rounded accent-cyber-cyan h-4 w-4"
              />
              <span className="text-xs font-mono text-slate-700 dark:text-navy-200">
                Require approval for unknown recipients
              </span>
            </label>

            <label className="flex items-center gap-3 p-3.5 rounded-xl bg-slate-50 dark:bg-navy-850 border border-slate-200 dark:border-white/[0.06] cursor-pointer hover:border-slate-300 dark:hover:border-white/20 transition">
              <input
                type="checkbox"
                checked={config.enable_duplicate_detection}
                onChange={(e) =>
                  setConfig({ ...config, enable_duplicate_detection: e.target.checked })
                }
                className="rounded accent-cyber-cyan h-4 w-4"
              />
              <span className="text-xs font-mono text-slate-700 dark:text-navy-200">
                Enable duplicate transaction detection (120s)
              </span>
            </label>

            <label className="flex items-center gap-3 p-3.5 rounded-xl bg-slate-50 dark:bg-navy-850 border border-slate-200 dark:border-white/[0.06] cursor-pointer hover:border-slate-300 dark:hover:border-white/20 transition">
              <input
                type="checkbox"
                checked={config.enable_frequency_check}
                onChange={(e) =>
                  setConfig({ ...config, enable_frequency_check: e.target.checked })
                }
                className="rounded accent-cyber-cyan h-4 w-4"
              />
              <span className="text-xs font-mono text-slate-700 dark:text-navy-200">
                Enforce transaction rate limits
              </span>
            </label>
          </div>
        </GlassCard>

        {/* Counterparty Lists */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Blocklist */}
          <GlassCard className="p-6 space-y-4" variant="elevated">
            <div className="flex items-center justify-between border-b border-slate-200/80 dark:border-white/[0.08] pb-3">
              <div className="flex items-center gap-2">
                <Users className="w-4 h-4 text-rose-400" />
                <h2 className="text-sm font-bold uppercase tracking-wider font-mono text-slate-900 dark:text-white">
                  Critical Blocklist
                </h2>
              </div>
              <StatusBadge status="BLOCK" size="xs" />
            </div>

            <p className="text-xs text-slate-500 dark:text-navy-400 font-sans">
              Any transaction destined for these addresses is automatically aborted with signature withholding.
            </p>

            <div className="flex gap-2">
              <input
                type="text"
                placeholder="bad-actor.near"
                value={newBlocked}
                onChange={(e) => setNewBlocked(e.target.value)}
                className="flex-1 bg-white dark:bg-navy-900 border border-slate-300 dark:border-white/10 rounded-xl px-3 py-2 text-xs font-mono text-slate-900 dark:text-white focus:outline-none focus:border-rose-500"
              />
              <GradientButton
                type="button"
                variant="danger"
                size="sm"
                onClick={addBlocked}
                leftIcon={<Plus className="w-3.5 h-3.5" />}
              >
                ADD
              </GradientButton>
            </div>

            <div className="max-h-48 overflow-y-auto divide-y divide-slate-200/80 dark:divide-white/[0.05] rounded-xl border border-slate-200/80 dark:border-white/[0.08] bg-slate-50/60 dark:bg-navy-900/60 p-2">
              {config.blocked_recipients.length === 0 ? (
                <div className="text-center py-4 text-xs font-mono text-slate-400 dark:text-navy-500">
                  No addresses currently blocked.
                </div>
              ) : (
                config.blocked_recipients.map((addr) => (
                  <div key={addr} className="flex items-center justify-between py-2 px-3 text-xs font-mono text-slate-800 dark:text-navy-200 hover:bg-slate-100 dark:hover:bg-white/[0.02]">
                    <span>{addr}</span>
                    <button
                      type="button"
                      onClick={() => removeBlocked(addr)}
                      className="text-slate-400 hover:text-rose-500 dark:text-navy-500 dark:hover:text-rose-400 transition"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))
              )}
            </div>
          </GlassCard>

          {/* Trusted Counterparties */}
          <GlassCard className="p-6 space-y-4" variant="elevated">
            <div className="flex items-center justify-between border-b border-slate-200/80 dark:border-white/[0.08] pb-3">
              <div className="flex items-center gap-2">
                <Users className="w-4 h-4 text-emerald-400" />
                <h2 className="text-sm font-bold uppercase tracking-wider font-mono text-slate-900 dark:text-white">
                  Verified Trusted List
                </h2>
              </div>
              <StatusBadge status="ALLOW" size="xs" />
            </div>

            <p className="text-xs text-slate-500 dark:text-navy-400 font-sans">
              Known, whitelisted recipient counterparties (treasury, verified oracles, official contracts).
            </p>

            <div className="flex gap-2">
              <input
                type="text"
                placeholder="treasury.payguard.near"
                value={newTrusted}
                onChange={(e) => setNewTrusted(e.target.value)}
                className="flex-1 bg-white dark:bg-navy-900 border border-slate-300 dark:border-white/10 rounded-xl px-3 py-2 text-xs font-mono text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500"
              />
              <GradientButton
                type="button"
                variant="success"
                size="sm"
                onClick={addTrusted}
                leftIcon={<Plus className="w-3.5 h-3.5" />}
              >
                ADD
              </GradientButton>
            </div>

            <div className="max-h-48 overflow-y-auto divide-y divide-slate-200/80 dark:divide-white/[0.05] rounded-xl border border-slate-200/80 dark:border-white/[0.08] bg-slate-50/60 dark:bg-navy-900/60 p-2">
              {config.trusted_recipients.length === 0 ? (
                <div className="text-center py-4 text-xs font-mono text-slate-400 dark:text-navy-500">
                  No addresses currently trusted.
                </div>
              ) : (
                config.trusted_recipients.map((addr) => (
                  <div key={addr} className="flex items-center justify-between py-2 px-3 text-xs font-mono text-slate-800 dark:text-navy-200 hover:bg-slate-100 dark:hover:bg-white/[0.02]">
                    <span>{addr}</span>
                    <button
                      type="button"
                      onClick={() => removeTrusted(addr)}
                      className="text-slate-400 hover:text-rose-500 dark:text-navy-500 dark:hover:text-rose-400 transition"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))
              )}
            </div>
          </GlassCard>
        </div>
      </form>
    </PageTransition>
  );
};
