import axios from 'axios';
import type {
  PolicyResponse,
  PolicyUpdateRequest,
  SecurityMetricsResponse,
  TransactionAnalysisResponse,
  TransactionRecord,
  TransactionRequest,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
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
};
