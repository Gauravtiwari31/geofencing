/**
 * Statistics Panel Component
 * Displays incident statistics and key metrics
 */

import React from 'react';
import { useAppSelector } from '../store/hooks';
import { LoadingSpinner } from './LoadingSpinner';

export const StatsPanel: React.FC = () => {
  const { dashboardData, loading, error } = useAppSelector(state => state.incidents);

  if (loading.dashboard) {
    return (
      <div className="panel">
        <div className="panel-header">
          <h2 className="panel-title">📊 Statistics</h2>
        </div>
        <div className="panel-content">
          <div className="flex flex-center">
            <LoadingSpinner />
            <span>Loading statistics...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error.dashboard) {
    return (
      <div className="panel">
        <div className="panel-header">
          <h2 className="panel-title">📊 Statistics</h2>
        </div>
        <div className="panel-content">
          <div className="alert alert-error">
            Failed to load statistics: {error.dashboard}
          </div>
        </div>
      </div>
    );
  }

  if (!dashboardData?.stats) {
    return (
      <div className="panel">
        <div className="panel-header">
          <h2 className="panel-title">📊 Statistics</h2>
        </div>
        <div className="panel-content">
          <div className="alert alert-info">
            No statistics available
          </div>
        </div>
      </div>
    );
  }

  const { stats } = dashboardData;
  const lastUpdated = new Date(dashboardData.last_updated).toLocaleTimeString();

  return (
    <div className="panel">
      <div className="panel-header">
        <h2 className="panel-title">📊 Incident Statistics</h2>
        <span className="text-small">Last updated: {lastUpdated}</span>
      </div>
      
      <div className="panel-content">
        <div className="stats-grid">
          {/* Total Incidents */}
          <div className="stat-card">
            <div className="stat-value">{stats.total_incidents}</div>
            <div className="stat-label">Total Incidents</div>
          </div>

          {/* Active Incidents */}
          <div className="stat-card active">
            <div className="stat-value">{stats.active_incidents}</div>
            <div className="stat-label">Active</div>
          </div>

          {/* Acknowledged Incidents */}
          <div className="stat-card acknowledged">
            <div className="stat-value">{stats.acknowledged_incidents}</div>
            <div className="stat-label">Acknowledged</div>
          </div>

          {/* Resolved Incidents */}
          <div className="stat-card">
            <div className="stat-value">{stats.resolved_incidents}</div>
            <div className="stat-label">Resolved</div>
          </div>

          {/* Recent Activity */}
          <div className="stat-card">
            <div className="stat-value">{stats.recent_activity}</div>
            <div className="stat-label">Last 24h</div>
          </div>
        </div>

        {/* Incident Types Breakdown */}
        <div className="stats-breakdown">
          <h3>By Type</h3>
          <div className="breakdown-grid">
            {Object.entries(stats.by_type).map(([type, count]) => (
              <div key={type} className="breakdown-item">
                <span className={`incident-type ${type}`}>{type}</span>
                <span className="breakdown-count">{count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Score Band Breakdown */}
        {Object.keys(stats.by_score_band).length > 0 && (
          <div className="stats-breakdown">
            <h3>By Priority</h3>
            <div className="breakdown-grid">
              {Object.entries(stats.by_score_band).map(([band, count]) => (
                <div key={band} className="breakdown-item">
                  <span className={`priority-band ${band.toLowerCase()}`}>{band}</span>
                  <span className="breakdown-count">{count}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <style jsx>{`
        .stats-breakdown {
          margin-top: 1.5rem;
          padding-top: 1.5rem;
          border-top: 1px solid #e9ecef;
        }
        
        .stats-breakdown h3 {
          font-size: 1rem;
          font-weight: 600;
          color: #495057;
          margin-bottom: 1rem;
        }
        
        .breakdown-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
          gap: 0.5rem;
        }
        
        .breakdown-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 0.5rem;
          background: #f8f9fa;
          border-radius: 0.25rem;
          font-size: 0.9rem;
        }
        
        .breakdown-count {
          font-weight: 600;
          color: #495057;
        }
        
        .priority-band {
          padding: 0.25rem 0.5rem;
          border-radius: 0.25rem;
          font-size: 0.8rem;
          font-weight: 500;
          text-transform: uppercase;
        }
        
        .priority-band.high {
          background: #fff5f5;
          color: #c53030;
        }
        
        .priority-band.medium {
          background: #fffaf0;
          color: #c05621;
        }
        
        .priority-band.low {
          background: #f0fff4;
          color: #2f855a;
        }
        
        .text-small {
          font-size: 0.8rem;
          color: #6c757d;
        }
      `}</style>
    </div>
  );
};
