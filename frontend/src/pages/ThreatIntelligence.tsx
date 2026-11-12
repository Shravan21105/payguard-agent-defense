import React from 'react';
import { Flame, Globe, Database, AlertOctagon } from 'lucide-react';

export const ThreatIntelligence: React.FC = () => {
  const threats = [
    {
      category: 'Unauthorized Drain Exploit',
      indicator: 'malicious-drainer.near',
      risk: 'CRITICAL',
      detected: '2 hours ago',
      action: 'HARD BLOCK',
    },
    {
      category: 'Unverified DEX Swap Contract',
      indicator: 'unverified-agent-dex.near',
      risk: 'MEDIUM',
      detected: '45 mins ago',
      action: 'HUMAN APPROVAL REQUIRED',
    },
    {
      category: 'Replay / Duplicate Velocity Flooding',
      indicator: 'High-frequency burst (>10 tx/min)',
      risk: 'HIGH',
      detected: '10 mins ago',
      action: 'RATE LIMIT BLOCK',
    },
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <Flame className="w-6 h-6 text-rose-400" />
          <span>Threat Intelligence &amp; Counterparty Telemetry</span>
        </h1>
        <p className="text-sm text-charcoal-400 mt-1">
          Catalog of known malicious actors, exploit patterns, and automated mitigation signatures.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="payguard-panel p-5">
          <div className="flex items-center justify-between text-rose-400 text-xs font-mono">
            <span>ACTIVE BLOCKLISTED</span>
            <AlertOctagon className="w-4 h-4" />
          </div>
          <div className="text-2xl font-bold font-mono text-white mt-2">4 Entities</div>
          <p className="text-[11px] text-charcoal-400 mt-1">Directly neutralized</p>
        </div>

        <div className="payguard-panel p-5">
          <div className="flex items-center justify-between text-emerald-400 text-xs font-mono">
            <span>VERIFIED COUNTERPARTIES</span>
            <Database className="w-4 h-4" />
          </div>
          <div className="text-2xl font-bold font-mono text-white mt-2">5 Registries</div>
          <p className="text-[11px] text-charcoal-400 mt-1">Oracle and treasury targets</p>
        </div>

        <div className="payguard-panel p-5">
          <div className="flex items-center justify-between text-amber-400 text-xs font-mono">
            <span>HEURISTIC SIGNATURES</span>
            <Globe className="w-4 h-4" />
          </div>
          <div className="text-2xl font-bold font-mono text-white mt-2">6 Defenses</div>
          <p className="text-[11px] text-charcoal-400 mt-1">Rate limits &amp; deduplication</p>
        </div>
      </div>

      <div className="payguard-panel p-6">
        <h2 className="text-sm font-bold uppercase tracking-wider font-mono text-white border-b border-charcoal-800 pb-3 mb-4">
          Identified Threat Signatures
        </h2>
        <div className="space-y-3">
          {threats.map((t, idx) => (
            <div
              key={idx}
              className="p-4 rounded-lg bg-charcoal-850 border border-charcoal-750 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs font-mono"
            >
              <div>
                <span className="text-white font-bold block">{t.category}</span>
                <span className="text-charcoal-400 text-[11px]">{t.indicator}</span>
              </div>
              <div className="flex items-center gap-4">
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    t.risk === 'CRITICAL'
                      ? 'bg-rose-950 text-rose-400 border border-rose-800'
                      : t.risk === 'HIGH'
                      ? 'bg-rose-950/60 text-rose-400'
                      : 'bg-amber-950 text-amber-400 border border-amber-800'
                  }`}
                >
                  {t.risk}
                </span>
                <span className="text-charcoal-300 font-bold">{t.action}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
