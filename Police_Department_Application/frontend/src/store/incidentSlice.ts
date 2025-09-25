/**
 * Redux slice for incident state management
 * Handles incidents, filters, loading states, and errors
 */

import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import {
  Incident,
  IncidentSummary,
  DashboardData,
  IncidentFilters,
  AckRequest,
  AckResponse
} from '../types/incident';
import apiService from '../services/api';

// Async thunks for API calls
export const fetchIncidents = createAsyncThunk(
  'incidents/fetchIncidents',
  async (filters?: IncidentFilters) => {
    return await apiService.getIncidents(filters);
  }
);

export const fetchIncidentDetails = createAsyncThunk(
  'incidents/fetchIncidentDetails',
  async (alertId: number) => {
    return await apiService.getIncident(alertId);
  }
);

export const acknowledgeIncident = createAsyncThunk(
  'incidents/acknowledgeIncident',
  async (ackRequest: AckRequest) => {
    return await apiService.acknowledgeIncident(ackRequest);
  }
);

export const fetchDashboardData = createAsyncThunk(
  'incidents/fetchDashboardData',
  async () => {
    return await apiService.getDashboardData();
  }
);

export const fetchUrgentIncidents = createAsyncThunk(
  'incidents/fetchUrgentIncidents',
  async (limit: number = 10) => {
    return await apiService.getUrgentIncidents(limit);
  }
);

// State interface
interface IncidentState {
  // Data
  incidents: IncidentSummary[];
  currentIncident: Incident | null;
  dashboardData: DashboardData | null;
  urgentIncidents: IncidentSummary[];
  
  // UI state
  filters: IncidentFilters;
  selectedIncidentId: number | null;
  isIncidentDetailsOpen: boolean;
  
  // Loading states
  loading: {
    incidents: boolean;
    currentIncident: boolean;
    dashboard: boolean;
    urgent: boolean;
    acknowledging: boolean;
  };
  
  // Error states
  error: {
    incidents: string | null;
    currentIncident: string | null;
    dashboard: string | null;
    urgent: string | null;
    acknowledging: string | null;
  };
  
  // Last updated timestamps
  lastUpdated: {
    incidents: string | null;
    dashboard: string | null;
    urgent: string | null;
  };
}

// Initial state
const initialState: IncidentState = {
  incidents: [],
  currentIncident: null,
  dashboardData: null,
  urgentIncidents: [],
  
  filters: {
    limit: 50,
    offset: 0,
    sort_by: 'created_at',
    sort_order: 'desc'
  },
  selectedIncidentId: null,
  isIncidentDetailsOpen: false,
  
  loading: {
    incidents: false,
    currentIncident: false,
    dashboard: false,
    urgent: false,
    acknowledging: false
  },
  
  error: {
    incidents: null,
    currentIncident: null,
    dashboard: null,
    urgent: null,
    acknowledging: null
  },
  
  lastUpdated: {
    incidents: null,
    dashboard: null,
    urgent: null
  }
};

// Slice
const incidentSlice = createSlice({
  name: 'incidents',
  initialState,
  reducers: {
    // Filters
    setFilters: (state, action: PayloadAction<Partial<IncidentFilters>>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearFilters: (state) => {
      state.filters = {
        limit: 50,
        offset: 0,
        sort_by: 'created_at',
        sort_order: 'desc'
      };
    },
    
    // UI state
    setSelectedIncident: (state, action: PayloadAction<number | null>) => {
      state.selectedIncidentId = action.payload;
    },
    openIncidentDetails: (state, action: PayloadAction<number>) => {
      state.selectedIncidentId = action.payload;
      state.isIncidentDetailsOpen = true;
    },
    closeIncidentDetails: (state) => {
      state.isIncidentDetailsOpen = false;
      state.selectedIncidentId = null;
      state.currentIncident = null;
    },
    
    // Clear errors
    clearError: (state, action: PayloadAction<keyof IncidentState['error']>) => {
      state.error[action.payload] = null;
    },
    clearAllErrors: (state) => {
      Object.keys(state.error).forEach(key => {
        state.error[key as keyof IncidentState['error']] = null;
      });
    },
    
    // Real-time updates (for SSE)
    addNewIncident: (state, action: PayloadAction<IncidentSummary>) => {
      // Add to beginning of list if not already present
      const exists = state.incidents.find(inc => inc.alert_id === action.payload.alert_id);
      if (!exists) {
        state.incidents.unshift(action.payload);
      }
    },
    updateIncidentStatus: (state, action: PayloadAction<{ alert_id: number; status: string }>) => {
      const incident = state.incidents.find(inc => inc.alert_id === action.payload.alert_id);
      if (incident) {
        incident.last_status = action.payload.status as any;
      }
      // Also update current incident if it matches
      if (state.currentIncident && state.currentIncident.alert_id === action.payload.alert_id) {
        state.currentIncident.last_status = action.payload.status as any;
      }
    }
  },
  extraReducers: (builder) => {
    // Fetch incidents
    builder
      .addCase(fetchIncidents.pending, (state) => {
        state.loading.incidents = true;
        state.error.incidents = null;
      })
      .addCase(fetchIncidents.fulfilled, (state, action) => {
        state.loading.incidents = false;
        state.incidents = action.payload;
        state.lastUpdated.incidents = new Date().toISOString();
      })
      .addCase(fetchIncidents.rejected, (state, action) => {
        state.loading.incidents = false;
        state.error.incidents = action.error.message || 'Failed to fetch incidents';
      });

    // Fetch incident details
    builder
      .addCase(fetchIncidentDetails.pending, (state) => {
        state.loading.currentIncident = true;
        state.error.currentIncident = null;
      })
      .addCase(fetchIncidentDetails.fulfilled, (state, action) => {
        state.loading.currentIncident = false;
        state.currentIncident = action.payload;
      })
      .addCase(fetchIncidentDetails.rejected, (state, action) => {
        state.loading.currentIncident = false;
        state.error.currentIncident = action.error.message || 'Failed to fetch incident details';
      });

    // Acknowledge incident
    builder
      .addCase(acknowledgeIncident.pending, (state) => {
        state.loading.acknowledging = true;
        state.error.acknowledging = null;
      })
      .addCase(acknowledgeIncident.fulfilled, (state, action) => {
        state.loading.acknowledging = false;
        
        // Update the incident status in the list
        const incident = state.incidents.find(inc => inc.alert_id === action.meta.arg.alert_id);
        if (incident) {
          incident.last_status = 'ACKNOWLEDGED';
        }
        
        // Update current incident if it matches
        if (state.currentIncident && state.currentIncident.alert_id === action.meta.arg.alert_id) {
          state.currentIncident.last_status = 'ACKNOWLEDGED';
        }
      })
      .addCase(acknowledgeIncident.rejected, (state, action) => {
        state.loading.acknowledging = false;
        state.error.acknowledging = action.error.message || 'Failed to acknowledge incident';
      });

    // Fetch dashboard data
    builder
      .addCase(fetchDashboardData.pending, (state) => {
        state.loading.dashboard = true;
        state.error.dashboard = null;
      })
      .addCase(fetchDashboardData.fulfilled, (state, action) => {
        state.loading.dashboard = false;
        state.dashboardData = action.payload;
        state.lastUpdated.dashboard = new Date().toISOString();
      })
      .addCase(fetchDashboardData.rejected, (state, action) => {
        state.loading.dashboard = false;
        state.error.dashboard = action.error.message || 'Failed to fetch dashboard data';
      });

    // Fetch urgent incidents
    builder
      .addCase(fetchUrgentIncidents.pending, (state) => {
        state.loading.urgent = true;
        state.error.urgent = null;
      })
      .addCase(fetchUrgentIncidents.fulfilled, (state, action) => {
        state.loading.urgent = false;
        state.urgentIncidents = action.payload;
        state.lastUpdated.urgent = new Date().toISOString();
      })
      .addCase(fetchUrgentIncidents.rejected, (state, action) => {
        state.loading.urgent = false;
        state.error.urgent = action.error.message || 'Failed to fetch urgent incidents';
      });
  }
});

// Export actions
export const {
  setFilters,
  clearFilters,
  setSelectedIncident,
  openIncidentDetails,
  closeIncidentDetails,
  clearError,
  clearAllErrors,
  addNewIncident,
  updateIncidentStatus
} = incidentSlice.actions;

// Export reducer
export default incidentSlice.reducer;
