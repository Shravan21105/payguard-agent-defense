/**
 * PAYGUARD Agent Defense Layer
 * Formatting and data transformation utilities
 */

export function formatAgentFindings(findings: unknown): string[] {
  if (!findings) return ['Normal checks'];

  if (Array.isArray(findings)) {
    const list = findings.map((f) => (typeof f === 'string' ? f : JSON.stringify(f))).filter(Boolean);
    return list.length > 0 ? list : ['Normal checks'];
  }

  if (typeof findings === 'string') {
    if (!findings.trim()) return ['Normal checks'];
    try {
      const parsed = JSON.parse(findings);
      if (typeof parsed === 'object') return formatAgentFindings(parsed);
    } catch {
      // It's a plain string
    }
    return [findings];
  }

  if (typeof findings === 'object' && findings !== null) {
    const obj = findings as Record<string, any>;
    const collected: string[] = [];

    if (obj.summary && typeof obj.summary === 'string') {
      collected.push(obj.summary);
    }

    if (Array.isArray(obj.suspicious_indicators) && obj.suspicious_indicators.length > 0) {
      collected.push(...obj.suspicious_indicators.map((s) => String(s)));
    }

    if (Array.isArray(obj.flags) && obj.flags.length > 0) {
      collected.push(...obj.flags.map((f) => String(f)));
    }

    if (obj.explanation && typeof obj.explanation === 'string' && !collected.includes(obj.explanation)) {
      collected.push(obj.explanation);
    }

    if (collected.length > 0) {
      return collected;
    }

    // Agent-specific structured summaries
    if (obj.anomaly_score !== undefined) {
      const score = (Number(obj.anomaly_score) * 100).toFixed(1);
      return [`Anomaly score: ${score}% (Outlier: ${obj.is_anomaly ? 'YES' : 'NO'})`];
    }

    if (obj.threat_severity !== undefined) {
      return [`Threat level: ${obj.threat_severity} (Blocked: ${obj.is_blocked ? 'YES' : 'NO'})`];
    }

    if (obj.intent_matches !== undefined) {
      return [`Intent match: ${obj.intent_matches ? 'Consistent' : 'Mismatch'} (${obj.severity || 'LOW'})`];
    }

    const entries = Object.entries(obj)
      .slice(0, 3)
      .map(([k, v]) => `${k.replace(/_/g, ' ')}: ${typeof v === 'object' ? JSON.stringify(v) : v}`);
    return entries.length > 0 ? entries : ['Normal checks'];
  }

  return [String(findings)];
}

export function formatAgentFindingsString(findings: unknown): string {
  return formatAgentFindings(findings).join(' • ');
}

