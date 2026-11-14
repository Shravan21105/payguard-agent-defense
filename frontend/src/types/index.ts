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
  intent_audit?: string;
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
  status?: string;
  tx_hash?: string | null;
  block_height?: number | null;
  block_hash?: string | null;
  explorer_url?: string | null;
  escrow_id?: string | null;
  error_details?: string | null;
  execution_mode?: 'ONCHAIN' | 'SIMULATION' | string;
}

export interface InitiateTransactionRequest {
  transaction_id?: string;
  sender: string;
  recipient: string;
  amount: number;
  currency?: string;
  agent_id?: string;
  purpose?: string;
  metadata?: Record<string, any>;
  dry_run?: boolean;
  network_id?: string;
  contract_id?: string;
  timelock_seconds?: number;
}

export interface TransactionRecord extends TransactionAnalysisResponse {
  agent_id?: string;
  purpose?: string;
  approval_status?: 'NONE' | 'PENDING' | 'APPROVED' | 'REJECTED';
  evidence_hash?: string;
  intent_matches?: boolean;
}

// ---------------------------------------------------------------------------
// Phase 2 Multi-Agent & Evidence Types
// ---------------------------------------------------------------------------

export interface AuthorizationEvidence {
  evidence_id: string;
  transaction_id: string;
  sha256_digest: string;
  rfc8785_canonical_payload: string;
  policy_version: string;
  decision: DecisionType;
  risk_score: number;
  created_at: string;
  is_tamper_verified: boolean;
  on_chain_submission_ready: boolean;
}

export interface AgentStatusInfo {
  agent_name: string;
  role: string;
  status: 'ONLINE' | 'ACTIVE' | 'IDLE' | 'DEGRADED';
  model: string;
  provider: string;
  uptime_pct: number;
  total_executions: number;
  average_latency_ms: number;
  capabilities: string[];
}

export interface AgentStatusResponse {
  orchestrator_status: string;
  llm_provider: string;
  llm_model: string;
  database_status: string;
  agents: AgentStatusInfo[];
}

export interface AgentExecutionLog {
  execution_id: string;
  transaction_id?: string;
  agent_name: string;
  status: 'SUCCESS' | 'ERROR' | 'FALLBACK' | string;
  execution_time_ms: number;
  findings: string[] | Record<string, any> | string;
  metadata?: Record<string, any>;
  timestamp: string;
}

export interface IntentAuditResult {
  declared_purpose: string;
  expected_recipient?: string | null;
  expected_amount?: number | null;
  expected_asset: string;
  intent_matches_transaction: boolean;
  recipient_matches: boolean;
  amount_matches: boolean;
  amount_deviation_percent: number;
  prompt_injection_detected: boolean;
  suspicious_indicators: string[];
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  reasoning: string;
  confidence: number;
  llm_provider_used: string;
  llm_fallback_used: boolean;
  intent_summary?: string;
  observed_behavior?: string;
  intent_consistency_score?: number;
  explanation?: string;
  evidence_references?: string[];
  task_scope_valid?: boolean;
  detected_attack_type?: string | null;
}

export interface IntentTestRequest {
  purpose_text: string;
  recipient: string;
  amount: number;
  currency?: string;
  sender?: string;
}

export interface IntentTestResponse {
  status: string;
  audit_result: IntentAuditResult;
  simulated_decision: DecisionType;
  simulated_risk_score: number;
  reasons: string[];
}

export interface PendingApprovalItem {
  approval_id: string;
  transaction_id: string;
  sender: string;
  recipient: string;
  amount: number;
  currency: string;
  purpose?: string;
  risk_score: number;
  risk_level: RiskLevel;
  reasons: string[];
  decision: DecisionType;
  approval_status: 'PENDING' | 'APPROVED' | 'REJECTED';
  created_at: string;
}

export interface ApprovalDecisionRequest {
  decision: 'APPROVE' | 'REJECT';
  reason?: string;
}

export interface ThreatFinding {
  finding_id: string;
  transaction_id: string;
  agent_name: string;
  finding_type: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  description: string;
  created_at: string;
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

// ---------------------------------------------------------------------------
// Phase 3 NEAR Blockchain & Vault Contract Types
// ---------------------------------------------------------------------------

export interface SignedPolicyAuthorization {
  auth_id: string;
  sender_id: string;
  recipient_id: string;
  amount_yocto: string;
  amount_near: number;
  decision: DecisionType;
  risk_score: number;
  policy_version: string;
  nonce: number;
  issued_at: number;
  expires_at: number;
  network_id: string;
  contract_id: string;
  canonical_payload: string;
  signature: string;
  signer_public_key: string;
  execution_ready: boolean;
  reasons: string[];
}

export interface OnChainAuthorizationRequest {
  sender: string;
  recipient: string;
  amount: number;
  currency?: string;
  purpose: string;
  network_id?: string;
  contract_id?: string;
  timelock_seconds?: number;
}

export interface OnChainExecutionRequest {
  authorization: SignedPolicyAuthorization;
  tx_hash?: string;
  caller_account_id?: string;
}

export interface OnChainEscrowRecord {
  escrow_id: string;
  auth_id: string;
  sender_id: string;
  recipient_id: string;
  amount_near: number;
  amount_yocto: string;
  risk_score: number;
  status: 'PENDING_APPROVAL' | 'APPROVED' | 'RELEASED' | 'REJECTED' | 'REFUNDED' | 'EXPIRED';
  created_at: string;
  timelock_until: string;
  approved_by?: string | null;
  approved_at?: string | null;
  rejection_reason?: string | null;
  tx_hash?: string | null;
}

export interface OnChainTransactionRecord {
  auth_id: string;
  tx_hash: string;
  sender_id: string;
  recipient_id: string;
  amount_near: number;
  amount_yocto: string;
  decision: DecisionType;
  risk_score: number;
  status: string;
  block_height?: number | null;
  block_hash?: string | null;
  explorer_url: string;
  executed_at: string;
}

export interface NEARNodeStatus {
  network: string;
  rpc_url: string;
  status: string;
  latest_block_height: number;
  latest_block_hash: string;
  vault_contract: string;
  signer_public_key: string;
  is_contract_deployed: boolean;
}

export interface VaultConfigView {
  admin_id: string;
  policy_signer_pk: string;
  min_escrow_duration_sec: number;
  max_escrow_duration_sec: number;
  policy_version: string;
  is_paused: boolean;
  total_volume_yocto: string;
  total_transfers_count: number;
  active_escrow_count: number;
}

// -----------------------------------------------------------------------------
// Phase 5: Real-Time Monitoring & Event Streaming Types
// -----------------------------------------------------------------------------
export type EventCategoryType = 'transactions' | 'escrow' | 'security' | 'blockchain' | 'system';
export type EventSeverityType = 'INFO' | 'SUCCESS' | 'WARNING' | 'CRITICAL';

export interface PayguardEvent {
  event_id: string;
  event_type: string;
  category: EventCategoryType;
  transaction_id?: string | null;
  timestamp: string;
  source: string;
  severity: EventSeverityType;
  payload: Record<string, any>;
}

export interface EventListResponse {
  total: number;
  limit: number;
  offset: number;
  events: PayguardEvent[];
}

export interface EventMetricsResponse {
  total_events: number;
  by_category: Record<string, number>;
  by_severity: Record<string, number>;
  active_subscriptions: number;
  recent_event_rate_per_min: number;
}

export interface MonitoringMetricsResponse {
  summary: {
    total_transactions: number;
    today_transactions: number;
    allow_count: number;
    warn_count: number;
    block_count: number;
  };
  execution_breakdown: {
    confirmed_onchain_count: number;
    failed_onchain_count: number;
    simulation_count: number;
  };
  escrow_breakdown: {
    pending_escrows: number;
    released_escrows: number;
    refunded_escrows: number;
  };
  volume_separation: {
    confirmed_onchain_volume_near: number;
    simulation_volume_near: number;
    pending_escrow_volume_near: number;
    protected_blocked_volume_near: number;
    note: string;
  };
  performance: {
    avg_evaluation_latency_ms: number;
    total_events_logged: number;
  };
  infrastructure: {
    active_websocket_connections: number;
    total_websocket_messages: number;
    near_rpc_status: string;
    last_blockchain_sync_time: string | null;
    latest_block_height: number;
  };
  generated_at: string;
}

export interface SubsystemHealth {
  status: string;
  [key: string]: any;
}

export interface MonitoringHealthResponse {
  overall_status: 'HEALTHY' | 'DEGRADED' | 'UNHEALTHY';
  timestamp: string;
  subsystems: {
    backend: SubsystemHealth;
    database: SubsystemHealth;
    websocket_manager: SubsystemHealth;
    near_rpc: SubsystemHealth;
    smart_contract: SubsystemHealth;
    blockchain_synchronization: SubsystemHealth;
  };
}

// ---------------------------------------------------------------------------
// Phase 6: Advanced AI Intelligence, Behavioral Profiling & Consensus Types
// ---------------------------------------------------------------------------

export interface AgentBehavioralProfile {
  agent_id: string;
  profile_version: number;
  transaction_count: number;
  average_amount: number;
  maximum_amount: number;
  std_dev_amount: number;
  transaction_frequency_per_day: number;
  spending_velocity_24h: number;
  known_recipients: string[];
  recipient_distribution: Record<string, number>;
  allow_count: number;
  warn_count: number;
  block_count: number;
  status: 'ACTIVE' | 'INSUFFICIENT_HISTORY';
  behavioral_baseline: Record<string, any>;
  last_updated: string;
}

export interface AnomalyFinding {
  anomaly_type: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  anomaly_score: number;
  affected_agent: string;
  transaction_id: string;
  observed_value: any;
  expected_range: string;
  explanation: string;
  supporting_evidence: string[];
  detection_method: string;
  timestamp: string;
}

export interface SecurityAttackFinding {
  detected_attack_type: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  confidence: number;
  suspicious_text_reference: string;
  attack_explanation: string;
  affected_component: string;
  recommended_mitigation: string;
  timestamp: string;
}

export interface AgentConsensusReport {
  consensus_score: number;
  disagreement_score: number;
  agent_recommendations: Record<string, string>;
  agent_risk_scores: Record<string, number>;
  agent_confidences: Record<string, number>;
  conflicting_findings: string[];
  missing_evidence: string[];
  consolidated_risk_summary: string;
  recommended_review_level: string;
  has_high_severity_conflict: boolean;
}

export interface ExplainableRiskAssessment {
  risk_category: 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';
  observed_facts: string[];
  model_interpretations: string[];
  statistical_anomalies: string[];
  security_warnings: string[];
  uncertainty_factors: string[];
  recommended_review: string;
  ai_vs_policy_distinction: string;
  plain_language_summary: string;
}

export interface ConfidenceAssessment {
  confidence_category: 'HIGH_CONFIDENCE' | 'MEDIUM_CONFIDENCE' | 'LOW_CONFIDENCE' | 'INSUFFICIENT_EVIDENCE';
  confidence_score: number;
  completeness_score: number;
  fallback_used: boolean;
  uncertainty_reasons: string[];
}

export interface AiPerformanceMetrics {
  total_evaluations: number;
  average_latency_ms: number;
  executions_by_agent: Record<string, number>;
  active_profiles: number;
  total_anomalies_flagged: number;
  llm_provider: string;
  llm_model: string;
  fallback_rate_pct: number;
  timestamp: string;
}

export interface AiEvaluationResponse {
  evaluation_id: string;
  transaction_id: string;
  agent_id: string;
  consensus_score: number;
  composite_risk_score: number;
  decision: DecisionType;
  requires_approval: boolean;
  consensus?: AgentConsensusReport;
  explainable_assessment?: ExplainableRiskAssessment;
  confidence_assessment?: ConfidenceAssessment;
  agent_profile?: AgentBehavioralProfile;
  agent_executions?: AgentExecutionLog[];
  created_at: string;
}

export interface AiConsensusResponse {
  transaction_id: string;
  consensus: AgentConsensusReport;
  explainable_assessment?: ExplainableRiskAssessment;
  confidence_assessment?: ConfidenceAssessment;
}

