import React, { useEffect, useState } from 'react';
import { Sliders, Save, Plus, Trash2, CheckCircle2, AlertTriangle, Shield } from 'lucide-react';
import { apiService } from '../services/api';
import type { PolicyConfig } from '../types';

export const Policies: React.FC = () => {
  const [config, setConfig] = useState<PolicyConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // New list item inputs
  const [newTrusted, setNewTrusted] = useState('');
  const [newBlocked, setNewBlocked] = useState('');

  useEffect(() => {
    fetchPolicies();
  }, []);

  const fetchPolicies = async () => {
    try {
      const res = await apiService.getPolicies();
      setConfig(res.config);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!config) return;
    setSaving(true);
    setSaveSuccess(false);
    try {
      const res = await apiService.updatePolicies(config);
      setConfig(res.config);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (e: any) {
      alert(`Failed to save policies: ${e.response?.data?.message || e.message}`);
    } finally {
      setSaving(false);
    }
  };

  const addTrusted = () => {
    if (!config || !newTrusted.trim()) return;
    const clean = newTrusted.trim().toLowerCase();
    if (!config.trusted_recipients.includes(clean)) {
      setConfig({
        ...config,
        trusted_recipients: [...config.trusted_recipients, clean],
      });
      setNewTrusted('');
    }
  };

  const removeTrusted = (addr: string) => {
    if (!config) return;
    setConfig({
      ...config,
      trusted_recipients: config.trusted_recipients.filter((a) => a !== addr),
    });
  };

  const addBlocked = () => {
    if (!config || !newBlocked.trim()) return;
    const clean = newBlocked.trim().toLowerCase();
    if (!config.blocked_recipients.includes(clean)) {
      setConfig({
        ...config,
        blocked_recipients: [...config.blocked_recipients, clean],
      });
      setNewBlocked('');
    }
  };

  const removeBlocked = (addr: string) => {
    if (!config) return;
    setConfig({
      ...config,
      blocked_recipients: config.blocked_recipients.filter((a) => a !== addr),
    });
  };

  if (loading || !config) {
    return (
      <div className="py-24 text-center font-mono text-xs text-charcoal-400">
        Loading active security policy parameters...
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Title */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Sliders className="w-6 h-6 text-emerald-400" />
            <span>Deterministic Policy Configuration</span>
          </h1>
          <p className="text-sm text-charcoal-400 mt-1">
            Configure hard financial guardrails, spending ceilings, and counterparty classifications.
          </p>
        </div>

        <button
          onClick={handleSave}
          disabled={saving}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-mono text-xs font-semibold tracking-wider transition shadow-shield-glow w-fit"
        >
          {saving ? (
            <span>SAVING...</span>
          ) : saveSuccess ? (
            <>
              <CheckCircle2 className="w-4 h-4 text-white" />
              <span>POLICIES UPDATED!</span>
            </>
          ) : (
            <>
              <Save className="w-4 h-4 text-white" />
              <span>APPLY POLICY UPDATES</span>
            </>
          )}
        </button>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* Core Spending Limits */}
        <div className="payguard-panel p-6">
          <div className="flex items-center gap-2 border-b border-charcoal-800 pb-3 mb-6">
            <Shield className="w-4 h-4 text-emerald-400" />
            <h2 className="text-sm font-bold uppercase tracking-wider font-mono text-white">
              Spending Ceilings &amp; Velocity Limits
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Max Per-TX Limit */}
            <div className="space-y-2">
              <label className="text-xs font-mono text-charcoal-400 block">
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
                  className="w-full bg-charcoal-950 border border-charcoal-750 rounded-lg px-3 py-2 text-sm font-mono text-white focus:outline-none focus:border-emerald-500"
                />
              </div>
              <p className="text-[11px] text-charcoal-400">
                Single transfers exceeding this limit trigger an immediate hard BLOCK.
              </p>
            </div>

            {/* Daily Cumulative Limit */}
            <div className="space-y-2">
              <label className="text-xs font-mono text-charcoal-400 block">
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
                  className="w-full bg-charcoal-950 border border-charcoal-750 rounded-lg px-3 py-2 text-sm font-mono text-white focus:outline-none focus:border-emerald-500"
                />
              </div>
              <p className="text-[11px] text-charcoal-400">
                Cumulative 24-hour ceiling per agent sender.
              </p>
            </div>

            {/* Max Frequency / Min */}
            <div className="space-y-2">
              <label className="text-xs font-mono text-charcoal-400 block">
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
                  className="w-full bg-charcoal-950 border border-charcoal-750 rounded-lg px-3 py-2 text-sm font-mono text-white focus:outline-none focus:border-emerald-500"
                />
              </div>
              <p className="text-[11px] text-charcoal-400">
                Rate-limiting to thwart autonomous loop flooding attacks.
              </p>
            </div>
          </div>
        </div>

        {/* Risk Thresholds & Toggles */}
        <div className="payguard-panel p-6">
          <div className="flex items-center gap-2 border-b border-charcoal-800 pb-3 mb-6">
            <Sliders className="w-4 h-4 text-emerald-400" />
            <h2 className="text-sm font-bold uppercase tracking-wider font-mono text-white">
              Risk Score Decision Thresholds
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-amber-400 font-semibold">Medium Risk Threshold (WARN)</span>
                <span className="text-white font-bold">{config.medium_risk_threshold} / 100</span>
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
              <p className="text-[11px] text-charcoal-400">
                Scores at or above this threshold require human operator sign-off before execution.
              </p>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-rose-400 font-semibold">High Risk Threshold (HARD BLOCK)</span>
                <span className="text-white font-bold">{config.high_risk_threshold} / 100</span>
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
              <p className="text-[11px] text-charcoal-400">
                Scores at or above this threshold trigger an irrevocable automated BLOCK.
              </p>
            </div>
          </div>

          <div className="mt-6 pt-6 border-t border-charcoal-800 grid grid-cols-1 md:grid-cols-3 gap-4">
            <label className="flex items-center gap-3 p-3 rounded-lg bg-charcoal-900 border border-charcoal-800 cursor-pointer hover:border-charcoal-700 transition">
              <input
                type="checkbox"
                checked={config.require_approval_for_unknown}
                onChange={(e) =>
                  setConfig({ ...config, require_approval_for_unknown: e.target.checked })
                }
                className="rounded accent-emerald-500 h-4 w-4"
              />
              <span className="text-xs font-mono text-charcoal-300">
                Require approval for unknown recipients
              </span>
            </label>

            <label className="flex items-center gap-3 p-3 rounded-lg bg-charcoal-900 border border-charcoal-800 cursor-pointer hover:border-charcoal-700 transition">
              <input
                type="checkbox"
                checked={config.enable_duplicate_detection}
                onChange={(e) =>
                  setConfig({ ...config, enable_duplicate_detection: e.target.checked })
                }
                className="rounded accent-emerald-500 h-4 w-4"
              />
              <span className="text-xs font-mono text-charcoal-300">
                Enable duplicate transaction detection (120s)
              </span>
            </label>

            <label className="flex items-center gap-3 p-3 rounded-lg bg-charcoal-900 border border-charcoal-800 cursor-pointer hover:border-charcoal-700 transition">
              <input
                type="checkbox"
                checked={config.enable_frequency_check}
                onChange={(e) =>
                  setConfig({ ...config, enable_frequency_check: e.target.checked })
                }
                className="rounded accent-emerald-500 h-4 w-4"
              />
              <span className="text-xs font-mono text-charcoal-300">
                Enable agent frequency velocity limits
              </span>
            </label>
          </div>
        </div>

        {/* Counterparty Lists: Blocklist & Trusted List */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Critical Blocklist */}
          <div className="payguard-panel p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-charcoal-800 pb-3">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-400" />
                <h3 className="text-sm font-bold uppercase tracking-wider font-mono text-white">
                  Critical Blocklist
                </h3>
              </div>
              <span className="text-[11px] font-mono text-rose-400 bg-rose-950/60 px-2 py-0.5 rounded border border-rose-800/40">
                HARD BLOCK
              </span>
            </div>

            <p className="text-xs text-charcoal-400">
              Any transaction destined for these addresses is automatically aborted.
            </p>

            <div className="flex gap-2">
              <input
                type="text"
                placeholder="bad-actor.near"
                value={newBlocked}
                onChange={(e) => setNewBlocked(e.target.value)}
                className="flex-1 bg-charcoal-950 border border-charcoal-750 rounded-lg px-3 py-1.5 text-xs font-mono text-white focus:outline-none focus:border-rose-500"
              />
              <button
                type="button"
                onClick={addBlocked}
                className="px-3 py-1.5 rounded-lg bg-rose-700 hover:bg-rose-600 text-white text-xs font-mono flex items-center gap-1"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>ADD</span>
              </button>
            </div>

            <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
              {config.blocked_recipients.map((addr) => (
                <div
                  key={addr}
                  className="flex items-center justify-between p-2 rounded bg-charcoal-850 border border-charcoal-750 text-xs font-mono text-charcoal-300"
                >
                  <span className="truncate max-w-[260px]">{addr}</span>
                  <button
                    type="button"
                    onClick={() => removeBlocked(addr)}
                    className="text-charcoal-400 hover:text-rose-400 p-1 transition"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Verified Trusted List */}
          <div className="payguard-panel p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-charcoal-800 pb-3">
              <div className="flex items-center gap-2">
                <Shield className="w-4 h-4 text-emerald-400" />
                <h3 className="text-sm font-bold uppercase tracking-wider font-mono text-white">
                  Verified Trusted List
                </h3>
              </div>
              <span className="text-[11px] font-mono text-emerald-400 bg-forest-950 px-2 py-0.5 rounded border border-emerald-800/50">
                LOW RISK
              </span>
            </div>

            <p className="text-xs text-charcoal-400">
              Verified counterparties bypass unknown-counterparty warnings.
            </p>

            <div className="flex gap-2">
              <input
                type="text"
                placeholder="treasury.near"
                value={newTrusted}
                onChange={(e) => setNewTrusted(e.target.value)}
                className="flex-1 bg-charcoal-950 border border-charcoal-750 rounded-lg px-3 py-1.5 text-xs font-mono text-white focus:outline-none focus:border-emerald-500"
              />
              <button
                type="button"
                onClick={addTrusted}
                className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-mono flex items-center gap-1"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>ADD</span>
              </button>
            </div>

            <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
              {config.trusted_recipients.map((addr) => (
                <div
                  key={addr}
                  className="flex items-center justify-between p-2 rounded bg-charcoal-850 border border-charcoal-750 text-xs font-mono text-charcoal-300"
                >
                  <span className="truncate max-w-[260px]">{addr}</span>
                  <button
                    type="button"
                    onClick={() => removeTrusted(addr)}
                    className="text-charcoal-400 hover:text-rose-400 p-1 transition"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      </form>
    </div>
  );
};
