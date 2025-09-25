/**
 * TypeScript type definitions for Police SEDI
 * Matches the Pydantic schemas from the backend
 */

export type IncidentType = 'SOS' | 'RED_ZONE' | 'DISCONNECTION';
export type IncidentStatus = 'ACTIVE' | 'ACKNOWLEDGED' | 'RESOLVED';
export type ScoreBand = 'HIGH' | 'MEDIUM' | 'LOW';
export type ActionType = 'ACK' | 'VIEW' | 'NOTE';

export interface LocationData {
  lat: number;
  lng: number;
  accuracy: number;
}

export interface Incident {
  alert_id: number;
  tourist_id: string;
  type: IncidentType;
  created_at: string;
  last_status: IncidentStatus;
  last_update_at: string;
  location?: LocationData;
  score_band?: ScoreBand;
  details?: string;
}

export interface IncidentSummary {
  alert_id: number;
  type: IncidentType;
  last_status: IncidentStatus;
  created_at: string;
  score_band?: ScoreBand;
}

export interface Action {
  id: number;
  alert_id: number;
  officer_id: string;
  action: ActionType;
  performed_at: string;
  note?: string;
}

export interface AckRequest {
  alert_id: number;
  tourist_id: string;
  note: string;
  officer_id: string;
}

export interface AckResponse {
  success: boolean;
  message: string;
  action_id?: number;
  timestamp: string;
}

export interface IncidentStats {
  total_incidents: number;
  active_incidents: number;
  acknowledged_incidents: number;
  resolved_incidents: number;
  by_type: Record<string, number>;
  by_score_band: Record<string, number>;
  recent_activity: number;
}

export interface DashboardData {
  stats: IncidentStats;
  recent_incidents: IncidentSummary[];
  urgent_incidents: IncidentSummary[];
  last_updated: string;
}

export interface UserInfo {
  user_id: string;
  username: string;
  role: string;
  authenticated: boolean;
  login_time?: string;
}

export interface AuthStatus {
  authenticated: boolean;
  user?: UserInfo;
  message: string;
}

export interface IncidentFilters {
  type?: IncidentType;
  status?: IncidentStatus;
  score_band?: ScoreBand;
  from_date?: string;
  to_date?: string;
  limit?: number;
  offset?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

// UI-specific types
export interface AlertConfig {
  type: 'success' | 'warning' | 'error' | 'info';
  message: string;
  duration?: number;
}

export interface MapBounds {
  north: number;
  south: number;
  east: number;
  west: number;
}
