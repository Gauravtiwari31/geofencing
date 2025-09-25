/**
 * Main Dashboard Component
 * Police SEDI main interface with statistics, incidents, and map
 */

import React, { useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '../store/hooks';
import { fetchDashboardData, fetchIncidents } from '../store/incidentSlice';
import { getCurrentUser, logout } from '../store/authSlice';
import { StatsPanel } from './StatsPanel';
import { IncidentList } from './IncidentList';
import { MapPanel } from './MapPanel';
import { LoadingSpinner } from './LoadingSpinner';

export const Dashboard: React.FC = () => {
  const dispatch = useAppDispatch();
  const { user, loading: authLoading } = useAppSelector(state => state.auth);
  const { loading: incidentLoading, error } = useAppSelector(state => state.incidents);

  useEffect(() => {
    // Load initial data
    dispatch(getCurrentUser());
    dispatch(fetchDashboardData());
    dispatch(fetchIncidents());

    // Set up periodic refresh
    const interval = setInterval(() => {
      dispatch(fetchDashboardData());
      dispatch(fetchIncidents());
    }, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, [dispatch]);

  const handleLogout = () => {
    dispatch(logout());
  };

  const handleRefresh = () => {
    dispatch(fetchDashboardData());
    dispatch(fetchIncidents());
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <div className="app-title">
            <span>🚔</span>
            <span>Police SEDI Dashboard</span>
          </div>
          
          <div className="user-info">
            {user && (
              <div className="user-badge">
                <strong>{user.username}</strong>
                <span> • {user.role}</span>
              </div>
            )}
            
            <button 
              className="btn btn-primary"
              onClick={handleRefresh}
              disabled={incidentLoading.dashboard || incidentLoading.incidents}
            >
              {incidentLoading.dashboard || incidentLoading.incidents ? (
                <LoadingSpinner size="small" />
              ) : (
                '🔄'
              )}
              Refresh
            </button>
            
            <button 
              className="logout-btn"
              onClick={handleLogout}
              disabled={authLoading.logout}
            >
              {authLoading.logout ? <LoadingSpinner size="small" /> : 'Logout'}
            </button>
          </div>
        </div>
      </header>

      {/* Main Dashboard Content */}
      <main className="dashboard">
        {/* Error display */}
        {(error.dashboard || error.incidents) && (
          <div className="alert alert-error">
            <strong>Error:</strong> {error.dashboard || error.incidents}
            <button className="btn btn-small" onClick={handleRefresh}>
              Retry
            </button>
          </div>
        )}

        {/* Dashboard Grid */}
        <div className="dashboard-grid">
          {/* Statistics Panel */}
          <div className="stats-panel">
            <StatsPanel />
          </div>

          {/* Incidents List */}
          <div className="incidents-panel">
            <IncidentList />
          </div>

          {/* Map Panel */}
          <div className="map-panel">
            <MapPanel />
          </div>
        </div>
      </main>
    </div>
  );
};
