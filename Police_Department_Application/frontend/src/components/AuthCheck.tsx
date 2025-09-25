/**
 * Authentication Check Component
 * Handles authentication flow and displays login interface
 */

import React, { useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '../store/hooks';
import { checkAuthStatus } from '../store/authSlice';
import { LoadingSpinner } from './LoadingSpinner';

export const AuthCheck: React.FC = () => {
  const dispatch = useAppDispatch();
  const { isAuthenticated, loading, error } = useAppSelector(state => state.auth);

  useEffect(() => {
    // Periodically check auth status in development mode
    const interval = setInterval(() => {
      dispatch(checkAuthStatus());
    }, 5000); // Check every 5 seconds

    return () => clearInterval(interval);
  }, [dispatch]);

  const handleRetryAuth = () => {
    dispatch(checkAuthStatus());
  };

  if (loading.status) {
    return (
      <div className="app-loading">
        <LoadingSpinner size="large" />
        <p>Checking authentication...</p>
      </div>
    );
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h1>🚔 Police SEDI</h1>
          <p>Security & Emergency Data Interface</p>
        </div>
        
        <div className="auth-content">
          {error.status ? (
            <div className="alert alert-error">
              <strong>Authentication Error:</strong> {error.status}
            </div>
          ) : (
            <div className="alert alert-info">
              <strong>Development Mode:</strong> Authentication is simulated for development purposes.
            </div>
          )}
          
          <div className="auth-info">
            <h3>System Status</h3>
            <ul>
              <li>🔒 Authentication: {isAuthenticated ? 'Active' : 'Required'}</li>
              <li>🖥️ Environment: Development Mode</li>
              <li>🔄 Auto-checking authentication...</li>
            </ul>
          </div>
          
          <div className="auth-actions">
            <button 
              className="btn btn-primary"
              onClick={handleRetryAuth}
              disabled={loading.status}
            >
              {loading.status ? 'Checking...' : 'Check Authentication'}
            </button>
          </div>
          
          <div className="auth-help">
            <p><strong>Development Note:</strong></p>
            <p>
              In production, this would redirect to Keycloak for OIDC authentication. 
              In development mode, authentication is automatically granted.
            </p>
          </div>
        </div>
      </div>
      
      <style jsx>{`
        .auth-container {
          display: flex;
          align-items: center;
          justify-content: center;
          min-height: 100vh;
          background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
          padding: 2rem;
        }
        
        .auth-card {
          background: white;
          border-radius: 0.5rem;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
          max-width: 500px;
          width: 100%;
          overflow: hidden;
        }
        
        .auth-header {
          background: #f8f9fa;
          padding: 2rem;
          text-align: center;
          border-bottom: 1px solid #e9ecef;
        }
        
        .auth-header h1 {
          font-size: 2rem;
          margin-bottom: 0.5rem;
          color: #495057;
        }
        
        .auth-header p {
          color: #6c757d;
          font-size: 1.1rem;
        }
        
        .auth-content {
          padding: 2rem;
        }
        
        .auth-info {
          margin: 1.5rem 0;
        }
        
        .auth-info h3 {
          margin-bottom: 1rem;
          color: #495057;
        }
        
        .auth-info ul {
          list-style: none;
          padding: 0;
        }
        
        .auth-info li {
          padding: 0.5rem 0;
          border-bottom: 1px solid #f1f3f4;
        }
        
        .auth-info li:last-child {
          border-bottom: none;
        }
        
        .auth-actions {
          text-align: center;
          margin: 1.5rem 0;
        }
        
        .auth-help {
          background: #f8f9fa;
          padding: 1rem;
          border-radius: 0.25rem;
          font-size: 0.9rem;
          color: #6c757d;
        }
        
        .auth-help p {
          margin-bottom: 0.5rem;
        }
        
        .auth-help p:last-child {
          margin-bottom: 0;
        }
      `}</style>
    </div>
  );
};
