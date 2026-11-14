import React, { useEffect, useState } from 'react';
import { Flame, Database, AlertOctagon, RotateCw, ShieldCheck } from 'lucide-react';
import { apiService } from '../services/api';
import type { SecurityMetricsResponse, ThreatFinding } from '../types';
import {
  SectionHeader,
  GlassCard,
  MetricCard,
  StatusBadge,
  EmptyState,
  PageTransition,
  GradientButton,
} from '../components/ui';

export const ThreatIntelligence: React.FC = () => {
  const [threats, setThreats] = useState<ThreatFinding[]>([]);
  const [metrics, setMetrics] = useState<SecurityMetricsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const [threatsData, metricsData] = await Promise.all([
        apiService.getThreats(),
        apiService.getSecurityMetrics(),
      ]);
      const list = Array.isArray(threatsData) ? threatsData : ((threatsData as any)?.threats || []);
      setThreats(list);
      setMetrics(metricsData);
    } catch (err) {
      console.error('Failed to load threats:', err);
      setThreats([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, []);

  const threatsList = Array.isArray(threats) ? threats : [];
  const criticalCount = threatsList.filter((t) => t.severity === 'CRITICAL').length;
  const highCount = threatsList.filter((t) => t.severity === 'HIGH').length;

  const formatTimestamp = (ts?: string) => {
    if (!ts) return 'Recent';
    try {
      const d = new Date(ts);
      return isNaN(d.getTime()) ? 'Recent' : d.toLocaleTimeString();
    } catch {
      return 'Recent';
    }
  };

  return (
    <PageTransition className="space-y-6 max-w-7xl mx-auto pb-16">
      {/* Header */}
      <SectionHeader
        icon={<Flame className="w-5 h-5 text-rose-500" />}
        title="Threat Intelligence &amp; Counterparty Telemetry"
        description="Real-time catalog of intercepted malicious actors, prompt injection signatures, and automated mitigations."
        action={
          <GradientButton
            variant="glass"
            size="sm"
            onClick={loadData}
            isLoading={loading}
            leftIcon={<RotateCw className={`w-3.5 h-3.5 text-cyber-cyan ${loading ? 'animate-spin' : ''}`} />}
          >
            REFRESH THREATS
          </GradientButton>
        }
      />

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="ACTIVE THREATS"
          value={threatsList.length}
          subValue="Identified malicious triggers"
          icon={<Flame className="w-4 h-4 text-rose-500" />}
          accentColor="rose"
          isLoading={loading}
        />

        <MetricCard
          label="CRITICAL/HIGH ESCALATIONS"
          value={criticalCount + highCount}
          subValue={`${criticalCount} Critical • ${highCount} High`}
          icon={<AlertOctagon className="w-4 h-4 text-amber-500" />}
          accentColor="amber"
          isLoading={loading}
        />

        <MetricCard
          label="TOTAL INTERCEPTED"
          value={metrics?.blocked_count ?? 0}
          subValue="Policy enforcement kills"
          icon={<ShieldCheck className="w-4 h-4 text-emerald-500" />}
          accentColor="emerald"
          isLoading={loading && !metrics}
        />

        <MetricCard
          label="VERIFIED REGISTRIES"
          value="5 Counterparties"
          subValue="Whitelisted ecosystem nodes"
          icon={<Database className="w-4 h-4 text-cyan-500" />}
          accentColor="cyan"
          isLoading={loading && !metrics}
        />
      </div>

      {/* Threats Table */}
      <GlassCard className="p-6 space-y-4" variant="elevated">
        <div className="flex items-center justify-between border-b border-slate-200/80 dark:border-white/[0.08] pb-3">
          <h2 className="text-sm font-bold uppercase tracking-wider font-mono text-slate-900 dark:text-white">
            Recorded Multi-Agent Threat Findings ({threatsList.length})
          </h2>
          <span className="text-xs font-mono text-slate-500 dark:text-navy-400">Persisted in Security Audit DB</span>
        </div>

        {threatsList.length === 0 ? (
          <EmptyState
            icon={<ShieldCheck className="w-6 h-6 text-emerald-500" />}
            title="No Active Threat Indicators"
            description="No active threat indicators currently recorded in database. Malicious agent attempts are isolated here."
            className="py-12 border-0 bg-transparent shadow-none"
          />
        ) : (
          <div className="space-y-3">
            {threatsList.map((t: any, index: number) => {
              const threatId = t.id || t.finding_id || `threat-${index}`;
              const txId = typeof t.transaction_id === 'string' ? t.transaction_id : (t.transaction_id ? String(t.transaction_id) : '');
              return (
                <div
                  key={threatId}
                  className="p-4 rounded-xl bg-white dark:bg-navy-850 border border-slate-200 dark:border-white/[0.06] hover:border-slate-300 dark:hover:border-white/20 transition flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs font-mono shadow-sm dark:shadow-none"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <StatusBadge status={t.severity} size="xs" />
                      <span className="font-bold text-slate-900 dark:text-white text-xs">{t.finding_type || t.attack_type || 'Threat Intercept'}</span>
                    </div>
                    <p className="text-slate-600 dark:text-navy-300 text-xs font-sans max-w-xl">{t.description || t.attack_explanation || 'Identified policy anomaly'}</p>
                    <div className="flex items-center gap-3 text-[10px] text-slate-500 dark:text-navy-400 pt-1">
                      <span>Agent: <strong className="text-slate-800 dark:text-white">{t.agent_name || 'Agent C'}</strong></span>
                      {txId && (
                        <span>Tx: <strong className="text-blue-600 dark:text-cyan-300">{txId}</strong></span>
                      )}
                    </div>
                  </div>

                  <div className="text-right text-[11px] font-mono text-slate-500 dark:text-navy-400 flex-shrink-0">
                    <span>{formatTimestamp(t.created_at || t.timestamp)}</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </GlassCard>
    </PageTransition>
  );
};
