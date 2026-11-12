import React from 'react';
import { Brain, ShieldAlert, Cpu, Sparkles, Lock } from 'lucide-react';

export const AiSecurity: React.FC = () => {
  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <Brain className="w-6 h-6 text-emerald-400" />
          <span>AI Security &amp; Behavioral Anomaly Architecture</span>
        </h1>
        <p className="text-sm text-charcoal-400 mt-1">
          Machine learning telemetry and explainable risk analytics for agent transactions.
        </p>
      </div>

      {/* Core Invariant Banner */}
      <div className="p-4 rounded-xl bg-forest-950/70 border border-emerald-800/40 text-xs font-mono text-emerald-300 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Lock className="w-5 h-5 text-emerald-400 flex-shrink-0" />
          <div>
            <span className="font-bold block">NON-NEGOTIABLE SAFETY INVARIANT</span>
            <span className="text-charcoal-300">
              AI analyzes • Policy engine enforces • Smart contract protects. An AI recommendation can NEVER override a deterministic policy BLOCK.
            </span>
          </div>
        </div>
        <span className="text-emerald-400 font-bold bg-forest-900 px-3 py-1 rounded border border-emerald-600/40">
          SEC-GUARD-01
        </span>
      </div>

      {/* Grid of AI components */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Isolation Forest Baseline */}
        <div className="payguard-panel p-6 space-y-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-charcoal-850 border border-charcoal-750 text-emerald-400">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">Isolation Forest Engine</h3>
              <span className="text-[11px] font-mono text-emerald-400">scikit-learn baseline</span>
            </div>
          </div>
          <p className="text-xs text-charcoal-400">
            Unsupervised outlier detection calibrated on agent payment frequency, transfer volume, and counterparty variance.
          </p>
          <div className="p-3 rounded bg-charcoal-900 border border-charcoal-800 text-[11px] font-mono space-y-1">
            <div className="flex justify-between text-charcoal-400">
              <span>Model State</span>
              <span className="text-emerald-400">CALIBRATED</span>
            </div>
            <div className="flex justify-between text-charcoal-400">
              <span>Contamination Factor</span>
              <span className="text-white">0.05 (5%)</span>
            </div>
            <div className="flex justify-between text-charcoal-400">
              <span>Latency Impact</span>
              <span className="text-emerald-400">&lt; 0.5 ms</span>
            </div>
          </div>
        </div>

        {/* Explainable Risk Assessor */}
        <div className="payguard-panel p-6 space-y-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-charcoal-850 border border-charcoal-750 text-amber-400">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">Explainable Risk Scorer</h3>
              <span className="text-[11px] font-mono text-amber-400">Deterministic Heuristics</span>
            </div>
          </div>
          <p className="text-xs text-charcoal-400">
            Weighted composite scoring decomposing counterparty risk, spending velocity, and cumulative budget headroom.
          </p>
          <div className="p-3 rounded bg-charcoal-900 border border-charcoal-800 text-[11px] font-mono space-y-1">
            <div className="flex justify-between text-charcoal-400">
              <span>Full Explainability</span>
              <span className="text-emerald-400">ENABLED</span>
            </div>
            <div className="flex justify-between text-charcoal-400">
              <span>Risk Range</span>
              <span className="text-white">0 to 100</span>
            </div>
            <div className="flex justify-between text-charcoal-400">
              <span>Decision Thresholds</span>
              <span className="text-white">Configurable</span>
            </div>
          </div>
        </div>

        {/* Provider-Independent LLM */}
        <div className="payguard-panel p-6 space-y-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-charcoal-850 border border-charcoal-750 text-emerald-400">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">Advisory LLM Gateway</h3>
              <span className="text-[11px] font-mono text-charcoal-400">Future Phase Prepared</span>
            </div>
          </div>
          <p className="text-xs text-charcoal-400">
            Provider-independent natural language prompt injection inspection and semantic intention alignment.
          </p>
          <div className="p-3 rounded bg-charcoal-900 border border-charcoal-800 text-[11px] font-mono space-y-1">
            <div className="flex justify-between text-charcoal-400">
              <span>Status</span>
              <span className="text-charcoal-400">PHASE 2 ROADMAP</span>
            </div>
            <div className="flex justify-between text-charcoal-400">
              <span>Zero On-chain Authority</span>
              <span className="text-emerald-400">VERIFIED</span>
            </div>
            <div className="flex justify-between text-charcoal-400">
              <span>Injection Defense</span>
              <span className="text-white">Sandboxed</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
