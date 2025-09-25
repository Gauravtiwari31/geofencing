/**
 * API service for communicating with Police SEDI backend
 * Handles all HTTP requests to FastAPI endpoints
 */

import axios, { AxiosInstance, AxiosResponse } from 'axios';
import {
  Incident,
  IncidentSummary,
  DashboardData,
  AckRequest,
  AckResponse,
  AuthStatus,
  UserInfo,
  IncidentFilters,
  IncidentStats,
  Action
} from '../types/incident';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: '', // Use relative URLs since we're served from the same domain
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor for auth (when implemented)
    this.api.interceptors.request.use(
      (config) => {
        // TODO: Add JWT token when OIDC is implemented
        // const token = localStorage.getItem('access_token');
        // if (token) {
        //   config.headers.Authorization = `Bearer ${token}`;
        // }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Error:', error.response?.data || error.message);
        
        // Handle auth errors
        if (error.response?.status === 401) {
          // TODO: Redirect to login when OIDC is implemented
          console.warn('Authentication required');
        }
        
        return Promise.reject(error);
      }
    );
  }

  // Health and system endpoints
  async getHealth(): Promise<any> {
    const response = await this.api.get('/health');
    return response.data;
  }

  // Authentication endpoints
  async getAuthStatus(): Promise<AuthStatus> {
    const response = await this.api.get('/auth/status');
    return response.data;
  }

  async getCurrentUser(): Promise<UserInfo> {
    const response = await this.api.get('/auth/user');
    return response.data;
  }

  async logout(): Promise<void> {
    await this.api.post('/auth/logout');
  }

  // Incident endpoints
  async getIncidents(filters?: IncidentFilters): Promise<IncidentSummary[]> {
    const params = new URLSearchParams();
    
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.append(key, value.toString());
        }
      });
    }

    const response = await this.api.get(`/api/v1/incidents/?${params.toString()}`);
    return response.data;
  }

  async getIncident(alertId: number): Promise<Incident> {
    const response = await this.api.get(`/api/v1/incidents/${alertId}`);
    return response.data;
  }

  async acknowledgeIncident(ackRequest: AckRequest): Promise<AckResponse> {
    const response = await this.api.post(
      `/api/v1/incidents/${ackRequest.alert_id}/ack`,
      ackRequest
    );
    return response.data;
  }

  async getIncidentActions(alertId: number): Promise<Action[]> {
    const response = await this.api.get(`/api/v1/incidents/${alertId}/actions`);
    return response.data;
  }

  async getUrgentIncidents(limit: number = 10): Promise<IncidentSummary[]> {
    const response = await this.api.get(`/api/v1/incidents/urgent?limit=${limit}`);
    return response.data;
  }

  async getDashboardData(): Promise<DashboardData> {
    const response = await this.api.get('/api/v1/incidents/stats/dashboard');
    return response.data;
  }

  async getIncidentStats(): Promise<IncidentStats> {
    const response = await this.api.get('/api/v1/incidents/stats/summary');
    return response.data;
  }

  // Utility methods
  formatError(error: any): string {
    if (error.response?.data?.detail) {
      return error.response.data.detail;
    }
    if (error.response?.data?.message) {
      return error.response.data.message;
    }
    if (error.message) {
      return error.message;
    }
    return 'An unexpected error occurred';
  }

  // Helper method to check API connectivity
  async checkConnectivity(): Promise<boolean> {
    try {
      await this.getHealth();
      return true;
    } catch (error) {
      console.error('API connectivity check failed:', error);
      return false;
    }
  }
}

// Export singleton instance
export const apiService = new ApiService();
export default apiService;
