export type DecisionType = 'ALLOW' | 'WARN' | 'BLOCK';
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH';
export type CheckStatus = 'PASSED' | 'WARNING' | 'FAILED' | 'BLOCKED' | 'SKIPPED';

export interface TransactionRequest {
  transaction_id?: string;
  sender: string;
  recipient: string;
  amount: number;
  currency?: string;
  agent_id?: string;
  purpose?: string;
  metadata?: Record<string, any>;
  timestamp?: string;
}

export interface PolicyChecksBreakdown {
  data_integrity: string;
  recipient_status: string;
  amount_limit: string;
  daily_limit: string;
  duplicate_check: string;
  frequency_check: string;
}

export interface TransactionAnalysisResponse {
  transaction_id: string;
  sender: string;
  recipient: string;
  amount: number;
  currency: string;
  decision: DecisionType;
  risk_score: number;
  risk_level: RiskLevel;
  requires_approval: boolean;
  reasons: string[];
  policy_checks: PolicyChecksBreakdown;
  timestamp: string;
  execution_allowed: boolean;
  confidence_score: number;
  is_mock_simulation: boolean;
}

export interface TransactionRecord extends TransactionAnalysisResponse {
  agent_id?: string;
  purpose?: string;
  approval_status?: 'NONE' | 'PENDING' | 'APPROVED' | 'REJECTED';
}

export interface PolicyConfig {
  max_tx_amount: number;
  daily_spending_limit: number;
  max_tx_frequency_per_minute: number;
  duplicate_window_seconds: number;
  trusted_recipients: string[];
  blocked_recipients: string[];
  require_approval_for_unknown: boolean;
  high_risk_threshold: number;
  medium_risk_threshold: number;
  enable_frequency_check: boolean;
  enable_duplicate_detection: boolean;
}

export interface PolicyResponse {
  version: string;
  updated_at: string;
  config: PolicyConfig;
}

export interface PolicyUpdateRequest {
  max_tx_amount?: number;
  daily_spending_limit?: number;
  max_tx_frequency_per_minute?: number;
  duplicate_window_seconds?: number;
  trusted_recipients?: string[];
  blocked_recipients?: string[];
  require_approval_for_unknown?: boolean;
  high_risk_threshold?: number;
  medium_risk_threshold?: number;
  enable_frequency_check?: boolean;
  enable_duplicate_detection?: boolean;
}

export interface SecurityAlert {
  id: string;
  timestamp: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  title: string;
  description: string;
  transaction_id?: string;
  recipient?: string;
  amount?: number;
}

export interface SecurityMetricsResponse {
  total_monitored: number;
  approved_count: number;
  warn_count: number;
  blocked_count: number;
  pending_approvals: number;
  total_near_volume: number;
  protected_near_volume: number;
  average_risk_score: number;
  active_agents_monitored: number;
  recent_alerts: SecurityAlert[];
  is_demo_metrics: boolean;
}
