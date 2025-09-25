/**
 * Map Panel Component
 * Displays incidents on an interactive map (placeholder for now)
 */

import React from 'react';
import { useAppSelector } from '../store/hooks';

export const MapPanel: React.FC = () => {
  const { incidents, dashboardData } = useAppSelector(state => state.incidents);

  // Count incidents with location data
  const incidentsWithLocation = incidents.filter(incident => 
    // We'll need to fetch full incident details to get location data
    true // For now, assume all incidents could have location
  );

  return (
    <div className="panel">
      <div className="panel-header">
        <h2 className="panel-title">🗺️ Incident Map</h2>
        <span className="map-info">
          {incidentsWithLocation.length} incidents with location
        </span>
      </div>
      
      <div className="panel-content">
        <div className="map-placeholder">
          <div className="map-icon">🗺️</div>
          <h3>Interactive Map</h3>
          <p>
            OpenStreetMap integration with Leaflet will be implemented here.
            This will show:
          </p>
          <ul>
            <li>📍 Real-time incident locations</li>
            <li>🔴 Red polygon markers for incidents</li>
            <li>🔍 10x10 meter precision zoom</li>
            <li>📱 Click to view incident details</li>
          </ul>
          
          <div className="map-stats">
            <div className="map-stat">
              <strong>{incidents.length}</strong>
              <span>Total Incidents</span>
            </div>
            <div className="map-stat">
              <strong>{dashboardData?.urgent_incidents.length || 0}</strong>
              <span>Urgent</span>
            </div>
            <div className="map-stat">
              <strong>{dashboardData?.stats.active_incidents || 0}</strong>
              <span>Active</span>
            </div>
          </div>
          
          <div className="map-legend">
            <h4>Legend</h4>
            <div className="legend-item">
              <span className="legend-color sos"></span>
              <span>SOS Emergency</span>
            </div>
            <div className="legend-item">
              <span className="legend-color red-zone"></span>
              <span>Red Zone Violation</span>
            </div>
            <div className="legend-item">
              <span className="legend-color disconnection"></span>
              <span>Device Disconnection</span>
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        .map-placeholder {
          text-align: center;
          padding: 2rem;
          color: #6c757d;
          background: #f8f9fa;
          border-radius: 0.5rem;
          min-height: 400px;
          display: flex;
          flex-direction: column;
          justify-content: center;
          align-items: center;
        }
        
        .map-icon {
          font-size: 4rem;
          margin-bottom: 1rem;
          opacity: 0.5;
        }
        
        .map-placeholder h3 {
          margin-bottom: 1rem;
          color: #495057;
        }
        
        .map-placeholder ul {
          text-align: left;
          margin: 1rem 0;
          max-width: 300px;
        }
        
        .map-placeholder li {
          margin: 0.5rem 0;
        }
        
        .map-stats {
          display: flex;
          gap: 2rem;
          margin: 1.5rem 0;
        }
        
        .map-stat {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 0.25rem;
        }
        
        .map-stat strong {
          font-size: 1.5rem;
          color: #495057;
        }
        
        .map-stat span {
          font-size: 0.8rem;
          color: #6c757d;
          text-transform: uppercase;
        }
        
        .map-legend {
          background: white;
          padding: 1rem;
          border-radius: 0.25rem;
          border: 1px solid #e9ecef;
          margin-top: 1rem;
        }
        
        .map-legend h4 {
          margin-bottom: 0.75rem;
          color: #495057;
          font-size: 0.9rem;
        }
        
        .legend-item {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          margin: 0.5rem 0;
          font-size: 0.8rem;
        }
        
        .legend-color {
          width: 16px;
          height: 16px;
          border-radius: 50%;
          display: inline-block;
        }
        
        .legend-color.sos {
          background: #dc3545;
        }
        
        .legend-color.red-zone {
          background: #fd7e14;
        }
        
        .legend-color.disconnection {
          background: #6c757d;
        }
        
        .map-info {
          font-size: 0.8rem;
          color: #6c757d;
        }
      `}</style>
    </div>
  );
};
