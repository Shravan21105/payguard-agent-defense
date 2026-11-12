import React, { useEffect, useState } from 'react';
import { Radio, Shield, Activity, Wifi, WifiOff, Clock, AlertTriangle, ArrowRight } from 'lucide-react';
import { useWebSocket } from '../hooks/useWebSocket';
import { apiService } from '../services/api';
import type { TransactionRecord } from '../types';
import { Badge } from '../components/common/Badge';
import { RiskMeter } from '../components/common/RiskMeter';

export const LiveMonitoring: React.FC = () => {
  const { isConnected, lastMessage } = useWebSocket();
  const [streamItems, setStreamItems] = useState<TransactionRecord[]>([]);

  useEffect(() => {
    // Initial fetch of recent records
    apiService.getTransactions(15).then((data) => {
      setStreamItems(data);
    });
  }, []);

  // When a new WebSocket message arrives
  useEffect(() => {
    if (lastMessage && lastMessage.type === 'NEW_TRANSACTION_EVALUATED') {
      const newRecord = lastMessage.payload;
      setStreamItems((prev) => [newRecord, ...prev.slice(0, 24)]);
    }
  }, [lastMessage]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Title */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Radio className="w-6 h-6 text-emerald-400 animate-pulse" />
            <span>Live Security Monitoring Stream</span>
          </h1>
          <p className="text-sm text-charcoal-400 mt-1">
            Real-time telemetry of autonomous agent payments evaluated against active policies.
          </p>
        </div>

        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-charcoal-900 border border-charcoal-750 text-xs font-mono">
          {isConnected ? (
            <>
              <Wifi className="w-4 h-4 text-emerald-400" />
              <span className="text-emerald-400">WS CONNECTED (127.0.0.1:8000)</span>
            </>
          ) : (
            <>
              <WifiOff className="w-4 h-4 text-amber-400" />
              <span className="text-amber-400">POLLING BACKUP ACTIVE</span>
            </>
          )}
        </div>
      </div>

      {/* Network & Engine Pipeline Bar */}
      <div className="p-4 rounded-xl bg-charcoal-900 border border-charcoal-800 grid grid-cols-1 md:grid-cols-4 gap-4 text-xs font-mono">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded bg-forest-950 border border-emerald-800/60 text-emerald-400">
            <Shield className="w-4 h-4" />
          </div>
          <div>
            <span className="text-charcoal-400 block text-[11px]">Enforcement Mode</span>
            <span className="text-white font-bold">Deterministic Inline</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="p-2 rounded bg-charcoal-800 border border-charcoal-700 text-charcoal-300">
            <Clock className="w-4 h-4" />
          </div>
          <div>
            <span className="text-charcoal-400 block text-[11px]">Evaluation Latency</span>
            <span className="text-emerald-400 font-bold">&lt; 1.8 ms</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="p-2 rounded bg-charcoal-800 border border-charcoal-700 text-charcoal-300">
            <Activity className="w-4 h-4" />
          </div>
          <div>
            <span className="text-charcoal-400 block text-[11px]">Target Chain</span>
            <span className="text-white font-bold">NEAR Protocol</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="p-2 rounded bg-charcoal-800 border border-charcoal-700 text-rose-400">
            <AlertTriangle className="w-4 h-4" />
          </div>
          <div>
            <span className="text-charcoal-400 block text-[11px]">Threat Interception</span>
            <span className="text-rose-400 font-bold">Automatic Killswitch</span>
          </div>
        </div>
      </div>

      {/* Live Stream Feed */}
      <div className="payguard-panel p-6">
        <div className="flex items-center justify-between border-b border-charcoal-800 pb-4">
          <div className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <h2 className="text-sm font-bold uppercase tracking-wider font-mono text-white">
              Real-Time Security Feed
            </h2>
          </div>
          <span className="text-xs font-mono text-charcoal-400">Showing last {streamItems.length} transactions</span>
        </div>

        <div className="mt-4 space-y-3">
          {streamItems.length === 0 ? (
            <div className="py-12 text-center text-charcoal-400 text-xs font-mono">
              Waiting for incoming agent transactions...
            </div>
          ) : (
            streamItems.map((tx) => (
              <div
                key={tx.transaction_id}
                className="p-4 rounded-lg bg-charcoal-850/70 border border-charcoal-750 hover:border-charcoal-700 transition flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                <div className="flex items-center gap-3">
                  <Badge type={tx.decision} />
                  <div>
                    <div className="flex items-center gap-2 text-xs font-mono">
                      <span className="text-charcoal-400">{tx.sender}</span>
                      <ArrowRight className="w-3 h-3 text-charcoal-400" />
                      <span className="text-white font-bold">{tx.recipient}</span>
                    </div>
                    {tx.purpose && (
                      <p className="text-[11px] text-charcoal-400 mt-0.5 truncate max-w-md">
                        {tx.purpose}
                      </p>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-6 justify-between md:justify-end text-xs font-mono">
                  <div>
                    <span className="text-charcoal-400 block text-[10px]">AMOUNT</span>
                    <span className="text-emerald-400 font-bold">{tx.amount.toFixed(2)} NEAR</span>
                  </div>

                  <div>
                    <span className="text-charcoal-400 block text-[10px]">RISK METER</span>
                    <RiskMeter score={tx.risk_score} />
                  </div>

                  <div className="text-right">
                    <span className="text-charcoal-400 block text-[10px]">SECURITY OUTCOME</span>
                    <span
                      className={`text-[11px] font-bold ${
                        tx.decision === 'ALLOW'
                          ? 'text-emerald-400'
                          : tx.decision === 'BLOCK'
                          ? 'text-rose-400'
                          : 'text-amber-400'
                      }`}
                    >
                      {tx.decision === 'ALLOW'
                        ? 'PERMITTED'
                        : tx.decision === 'BLOCK'
                        ? 'INTERCEPTED'
                        : 'PENDING SIGN-OFF'}
                    </span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
