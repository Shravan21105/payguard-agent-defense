import React from 'react';
import { Settings as SettingsIcon, Server, Database } from 'lucide-react';

export const Settings: React.FC = () => {
  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <SettingsIcon className="w-6 h-6 text-emerald-400" />
          <span>System &amp; Network Configuration</span>
        </h1>
        <p className="text-sm text-charcoal-400 mt-1">
          Target blockchain network, local daemon connection, and security alert channels.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Backend & Node Setup */}
        <div className="payguard-panel p-6 space-y-4">
          <div className="flex items-center gap-2 border-b border-charcoal-800 pb-3">
            <Server className="w-4 h-4 text-emerald-400" />
            <h2 className="text-sm font-bold uppercase tracking-wider font-mono text-white">
              Backend Server Endpoint
            </h2>
          </div>

          <div className="space-y-3 text-xs font-mono">
            <div>
              <label className="text-charcoal-400 block mb-1">API Base URL</label>
              <input
                type="text"
                disabled
                value="http://127.0.0.1:8000/api"
                className="w-full bg-charcoal-950 border border-charcoal-800 rounded-lg px-3 py-2 text-charcoal-300"
              />
            </div>

            <div>
              <label className="text-charcoal-400 block mb-1">WebSocket Telemetry URL</label>
              <input
                type="text"
                disabled
                value="ws://127.0.0.1:8000/ws/events"
                className="w-full bg-charcoal-950 border border-charcoal-800 rounded-lg px-3 py-2 text-charcoal-300"
              />
            </div>
          </div>
        </div>

        {/* Blockchain Network */}
        <div className="payguard-panel p-6 space-y-4">
          <div className="flex items-center gap-2 border-b border-charcoal-800 pb-3">
            <Database className="w-4 h-4 text-emerald-400" />
            <h2 className="text-sm font-bold uppercase tracking-wider font-mono text-white">
              Target Blockchain Architecture
            </h2>
          </div>

          <div className="space-y-3 text-xs font-mono">
            <div>
              <label className="text-charcoal-400 block mb-1">Network</label>
              <input
                type="text"
                disabled
                value="NEAR Protocol Testnet"
                className="w-full bg-charcoal-950 border border-charcoal-800 rounded-lg px-3 py-2 text-emerald-400 font-bold"
              />
            </div>

            <div>
              <label className="text-charcoal-400 block mb-1">Vault Smart Contract (Phase 2+)</label>
              <input
                type="text"
                disabled
                value="payguard-vault.testnet"
                className="w-full bg-charcoal-950 border border-charcoal-800 rounded-lg px-3 py-2 text-charcoal-300"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
