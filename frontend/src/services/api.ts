import axios from 'axios';
import type {
  AgentBehavioralProfile,
  AgentExecutionLog,
  AgentStatusResponse,
  AiConsensusResponse,
  AiEvaluationResponse,
  AiPerformanceMetrics,
  AnomalyFinding,
  ApprovalDecisionRequest,
  AuthorizationEvidence,
  InitiateTransactionRequest,
  IntentTestRequest,
  IntentTestResponse,
  NEARNodeStatus,
  OnChainAuthorizationRequest,
  OnChainEscrowRecord,
  OnChainExecutionRequest,
  OnChainTransactionRecord,
  PendingApprovalItem,
  PolicyResponse,
  PolicyUpdateRequest,
  SecurityAttackFinding,
  SecurityMetricsResponse,
  SignedPolicyAuthorization,
  ThreatFinding,
  TransactionAnalysisResponse,
  TransactionRecord,
  TransactionRequest,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiService = {
  // Health
  async getHealth(): Promise<{ status: string; application: string; version: string }> {
    const { data } = await apiClient.get('/health');
    return data;
  },

  // Transactions
  async initiateTransaction(payload: InitiateTransactionRequest): Promise<TransactionRecord> {
    const { data } = await apiClient.post<TransactionRecord>('/transactions/initiate', payload);
    return data;
  },

  async analyzeTransaction(payload: TransactionRequest): Promise<TransactionAnalysisResponse> {
    const { data } = await apiClient.post<TransactionAnalysisResponse>('/transactions/analyze', payload);
    return data;
  },

  async getTransactions(limit = 50, decision?: string): Promise<TransactionRecord[]> {
    const params: Record<string, any> = { limit };
    if (decision && decision !== 'ALL') {
      params.decision = decision;
    }
    const { data } = await apiClient.get<TransactionRecord[]>('/transactions', { params });
    return data;
  },

  async getTransaction(id: string): Promise<TransactionRecord> {
    const { data } = await apiClient.get<TransactionRecord>(`/transactions/${id}`);
    return data;
  },

  async getEvidence(transactionId: string): Promise<AuthorizationEvidence> {
    const { data } = await apiClient.get<AuthorizationEvidence>(`/transactions/${transactionId}/evidence`);
    return data;
  },

  async getTransactionAgents(transactionId: string): Promise<{ transaction_id: string; executions: AgentExecutionLog[] }> {
    const { data } = await apiClient.get<{ transaction_id: string; executions: AgentExecutionLog[] }>(
      `/transactions/${transactionId}/agents`
    );
    return data;
  },

  // Policies
  async getPolicies(): Promise<PolicyResponse> {
    const { data } = await apiClient.get<PolicyResponse>('/policies');
    return data;
  },

  async updatePolicies(payload: PolicyUpdateRequest): Promise<PolicyResponse> {
    const { data } = await apiClient.post<PolicyResponse>('/policies', payload);
    return data;
  },

  // Security Metrics
  async getSecurityMetrics(): Promise<SecurityMetricsResponse> {
    const { data } = await apiClient.get<SecurityMetricsResponse>('/security/metrics');
    return data;
  },

  // Agents Telemetry
  async getAgentStatus(): Promise<AgentStatusResponse> {
    const { data } = await apiClient.get<AgentStatusResponse>('/agents/status');
    return data;
  },

  async getAgentRuns(limit = 20): Promise<AgentExecutionLog[]> {
    const { data } = await apiClient.get<AgentExecutionLog[]>('/agents/runs', { params: { limit } });
    return data;
  },

  async testIntent(payload: IntentTestRequest): Promise<IntentTestResponse> {
    const { data } = await apiClient.post<IntentTestResponse>('/agents/test-intent', payload);
    return data;
  },

  // Approvals
  async getApprovals(): Promise<PendingApprovalItem[]> {
    const { data } = await apiClient.get<PendingApprovalItem[]>('/approvals');
    return data;
  },

  async decideApproval(
    transactionId: string,
    decision: 'APPROVE' | 'REJECT',
    reason = 'Manual operator decision'
  ): Promise<{ status: string; transaction_id: string; decision: string }> {
    const payload: ApprovalDecisionRequest = { decision, reason };
    const { data } = await apiClient.post(`/approvals/${transactionId}/decide`, payload);
    return data;
  },

  // Threat Intelligence
  async getThreats(): Promise<ThreatFinding[]> {
    const { data } = await apiClient.get<any>('/threats');
    if (Array.isArray(data)) return data;
    if (data && Array.isArray(data.threats)) return data.threats;
    return [];
  },

  // -------------------------------------------------------------------------
  // Phase 3: NEAR Blockchain & Smart Contract Vault Endpoints
  // -------------------------------------------------------------------------
  async authorizeOnchain(payload: OnChainAuthorizationRequest): Promise<SignedPolicyAuthorization> {
    const { data } = await apiClient.post<SignedPolicyAuthorization>('/blockchain/authorize', payload);
    return data;
  },

  async executeOnchain(payload: OnChainExecutionRequest): Promise<OnChainTransactionRecord> {
    const { data } = await apiClient.post<OnChainTransactionRecord>('/blockchain/execute', payload);
    return data;
  },

  async createEscrow(
    authorization: SignedPolicyAuthorization,
    timelockSeconds = 3600
  ): Promise<OnChainEscrowRecord> {
    const { data } = await apiClient.post<OnChainEscrowRecord>(
      `/blockchain/escrow?timelock_seconds=${timelockSeconds}`,
      authorization
    );
    return data;
  },

  async getEscrow(escrowId: string): Promise<OnChainEscrowRecord> {
    const { data } = await apiClient.get<OnChainEscrowRecord>(`/blockchain/escrow/${escrowId}`);
    return data;
  },

  async approveEscrow(
    escrowId: string,
    operatorId = 'human_operator_01',
    reason = 'Approved by operator'
  ): Promise<OnChainEscrowRecord> {
    const { data } = await apiClient.post<OnChainEscrowRecord>(
      `/blockchain/escrow/${escrowId}/approve`,
      null,
      { params: { operator_id: operatorId, reason } }
    );
    return data;
  },

  async rejectEscrow(
    escrowId: string,
    operatorId = 'human_operator_01',
    reason = 'Rejected by operator'
  ): Promise<OnChainEscrowRecord> {
    const { data } = await apiClient.post<OnChainEscrowRecord>(
      `/blockchain/escrow/${escrowId}/reject`,
      null,
      { params: { operator_id: operatorId, reason } }
    );
    return data;
  },

  async getBlockchainStatus(): Promise<NEARNodeStatus> {
    const { data } = await apiClient.get<NEARNodeStatus>('/blockchain/status');
    return data;
  },

  async getOnchainTransactions(limit = 50): Promise<OnChainTransactionRecord[]> {
    const { data } = await apiClient.get<OnChainTransactionRecord[]>('/blockchain/transactions', {
      params: { limit },
    });
    return data;
  },

  // -------------------------------------------------------------------------
  // Phase 5: Real-Time Monitoring & Telemetry Endpoints
  // -------------------------------------------------------------------------
  async getEvents(params?: {
    limit?: number;
    offset?: number;
    event_type?: string;
    category?: string;
    severity?: string;
    transaction_id?: string;
    source?: string;
  }): Promise<import('../types').EventListResponse> {
    const { data } = await apiClient.get<import('../types').EventListResponse>('/events', { params });
    return data;
  },

  async getEventById(eventId: string): Promise<import('../types').PayguardEvent> {
    const { data } = await apiClient.get<import('../types').PayguardEvent>(`/events/${eventId}`);
    return data;
  },

  async getTransactionEvents(transactionId: string): Promise<import('../types').PayguardEvent[]> {
    const { data } = await apiClient.get<import('../types').PayguardEvent[]>(`/events/transaction/${transactionId}`);
    return data;
  },

  async getEventMetrics(): Promise<import('../types').EventMetricsResponse> {
    const { data } = await apiClient.get<import('../types').EventMetricsResponse>('/events/metrics');
    return data;
  },

  async getMonitoringMetrics(): Promise<import('../types').MonitoringMetricsResponse> {
    const { data } = await apiClient.get<import('../types').MonitoringMetricsResponse>('/monitoring/metrics');
    return data;
  },

  async getMonitoringHealth(): Promise<import('../types').MonitoringHealthResponse> {
    const { data } = await apiClient.get<import('../types').MonitoringHealthResponse>('/monitoring/health');
    return data;
  },

  // -------------------------------------------------------------------------
  // Phase 6: Advanced AI Intelligence & Behavioral Profiling Endpoints
  // -------------------------------------------------------------------------
  async getAiPerformance(): Promise<AiPerformanceMetrics> {
    const { data } = await apiClient.get<AiPerformanceMetrics>('/ai/agents/performance');
    return data;
  },

  async getAgentProfiles(): Promise<AgentBehavioralProfile[]> {
    const { data } = await apiClient.get<AgentBehavioralProfile[]>('/ai/profiles');
    return data;
  },

  async getAgentProfile(agentId: string): Promise<AgentBehavioralProfile> {
    const { data } = await apiClient.get<AgentBehavioralProfile>(`/ai/profiles/${agentId}`);
    return data;
  },

  async getAiAnomalies(params?: {
    limit?: number;
    agent_id?: string;
    severity?: string;
  }): Promise<AnomalyFinding[]> {
    const { data } = await apiClient.get<AnomalyFinding[]>('/ai/anomalies', { params });
    return data;
  },

  async getAiSecurityFindings(): Promise<SecurityAttackFinding[]> {
    const { data } = await apiClient.get<SecurityAttackFinding[]>('/ai/security/findings');
    return data;
  },

  async getAiEvaluation(transactionId: string): Promise<AiEvaluationResponse> {
    const { data } = await apiClient.get<AiEvaluationResponse>(`/ai/evaluations/${transactionId}`);
    return data;
  },

  async getAiConsensus(transactionId: string): Promise<AiConsensusResponse> {
    const { data } = await apiClient.get<AiConsensusResponse>(`/ai/consensus/${transactionId}`);
    return data;
  },
};

