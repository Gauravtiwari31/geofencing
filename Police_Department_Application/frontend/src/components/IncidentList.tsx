/**
 * Incident List Component
 * Displays list of incidents with filtering and actions
 */

import React, { useState } from 'react';
import { useAppDispatch, useAppSelector } from '../store/hooks';
import { acknowledgeIncident, setFilters, openIncidentDetails } from '../store/incidentSlice';
import { LoadingSpinner } from './LoadingSpinner';
import { IncidentType, IncidentStatus, AckRequest } from '../types/incident';

export const IncidentList: React.FC = () => {
  const dispatch = useAppDispatch();
  const { 
    incidents, 
    loading, 
    error, 
    filters 
  } = useAppSelector(state => state.incidents);
  
  const { user } = useAppSelector(state => state.auth);
  
  const [ackingIncident, setAckingIncident] = useState<number | null>(null);

  const handleFilterChange = (key: string, value: any) => {
    dispatch(setFilters({ [key]: value || undefined }));
  };

  const handleIncidentClick = (alertId: number) => {
    dispatch(openIncidentDetails(alertId));
  };

  const handleAcknowledge = async (incident: any) => {
    if (!user || ackingIncident) return;

    setAckingIncident(incident.alert_id);
    
    const ackRequest: AckRequest = {
      alert_id: incident.alert_id,
      tourist_id: incident.tourist_id || '', // We'll need to get this from incident details
      note: `Acknowledged by ${user.username}`,
      officer_id: user.user_id
    };

    try {
      await dispatch(acknowledgeIncident(ackRequest)).unwrap();
    } catch (error) {
      console.error('Failed to acknowledge incident:', error);
    } finally {
      setAckingIncident(null);
    }
  };

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const getTimeAgo = (timestamp: string) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffMs = now.getTime() - time.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <h2 className="panel-title">🚨 Active Incidents</h2>
        <span className="incident-count">{incidents.length} incidents</span>
      </div>

      {/* Filters */}
      <div className="panel-filters">
        <select 
          value={filters.type || ''} 
          onChange={(e) => handleFilterChange('type', e.target.value)}
          className="filter-select"
        >
          <option value="">All Types</option>
          <option value="SOS">SOS</option>
          <option value="RED_ZONE">Red Zone</option>
          <option value="DISCONNECTION">Disconnection</option>
        </select>

        <select 
          value={filters.status || ''} 
          onChange={(e) => handleFilterChange('status', e.target.value)}
          className="filter-select"
        >
          <option value="">All Status</option>
          <option value="ACTIVE">Active</option>
          <option value="ACKNOWLEDGED">Acknowledged</option>
          <option value="RESOLVED">Resolved</option>
        </select>

        <select 
          value={filters.score_band || ''} 
          onChange={(e) => handleFilterChange('score_band', e.target.value)}
          className="filter-select"
        >
          <option value="">All Priorities</option>
          <option value="HIGH">High</option>
          <option value="MEDIUM">Medium</option>
          <option value="LOW">Low</option>
        </select>
      </div>

      <div className="panel-content">
        {loading.incidents && (
          <div className="flex flex-center">
            <LoadingSpinner />
            <span>Loading incidents...</span>
          </div>
        )}

        {error.incidents && (
          <div className="alert alert-error">
            Failed to load incidents: {error.incidents}
          </div>
        )}

        {!loading.incidents && !error.incidents && incidents.length === 0 && (
          <div className="alert alert-info">
            No incidents found matching the current filters.
          </div>
        )}

        {!loading.incidents && incidents.length > 0 && (
          <div className="incident-list">
            {incidents.map((incident) => (
              <div 
                key={incident.alert_id} 
                className="incident-item"
                onClick={() => handleIncidentClick(incident.alert_id)}
              >
                <div className="incident-info">
                  <div className="incident-id">
                    Alert #{incident.alert_id}
                  </div>
                  <div className="incident-meta">
                    <span className={`incident-type ${incident.type}`}>
                      {incident.type.replace('_', ' ')}
                    </span>
                    <span className="incident-time">
                      {getTimeAgo(incident.created_at)}
                    </span>
                    {incident.score_band && (
                      <span className={`priority-badge ${incident.score_band.toLowerCase()}`}>
                        {incident.score_band}
                      </span>
                    )}
                  </div>
                </div>

                <div className="incident-actions">
                  <span className={`incident-status ${incident.last_status}`}>
                    {incident.last_status}
                  </span>

                  {incident.last_status === 'ACTIVE' && user && (
                    <button
                      className="btn btn-success btn-sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleAcknowledge(incident);
                      }}
                      disabled={ackingIncident === incident.alert_id}
                    >
                      {ackingIncident === incident.alert_id ? (
                        <LoadingSpinner size="small" />
                      ) : (
                        '✓ ACK'
                      )}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <style jsx>{`
        .panel-filters {
          padding: 1rem 1.5rem;
          background: #f8f9fa;
          border-bottom: 1px solid #e9ecef;
          display: flex;
          gap: 1rem;
          flex-wrap: wrap;
        }
        
        .filter-select {
          padding: 0.5rem;
          border: 1px solid #ced4da;
          border-radius: 0.25rem;
          background: white;
          font-size: 0.9rem;
          min-width: 120px;
        }
        
        .incident-count {
          font-size: 0.9rem;
          color: #6c757d;
          background: rgba(0, 0, 0, 0.05);
          padding: 0.25rem 0.75rem;
          border-radius: 1rem;
        }
        
        .incident-actions {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }
        
        .btn-sm {
          padding: 0.25rem 0.75rem;
          font-size: 0.8rem;
        }
        
        .priority-badge {
          padding: 0.25rem 0.5rem;
          border-radius: 0.25rem;
          font-size: 0.7rem;
          font-weight: 600;
          text-transform: uppercase;
        }
        
        .priority-badge.high {
          background: #fff5f5;
          color: #c53030;
        }
        
        .priority-badge.medium {
          background: #fffaf0;
          color: #c05621;
        }
        
        .priority-badge.low {
          background: #f0fff4;
          color: #2f855a;
        }
        
        .incident-time {
          font-size: 0.8rem;
          color: #6c757d;
        }
      `}</style>
    </div>
  );
};
