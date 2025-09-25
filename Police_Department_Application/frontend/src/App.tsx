/**
 * Main Police SEDI Application Component
 * Handles routing, authentication, and layout
 */

import React, { useEffect } from 'react';
import { Provider } from 'react-redux';
import { store } from './store';
import { Dashboard } from './components/Dashboard';
import { AuthCheck } from './components/AuthCheck';
import { LoadingSpinner } from './components/LoadingSpinner';
import { useAppDispatch, useAppSelector } from './store/hooks';
import { checkAuthStatus } from './store/authSlice';
import './App.css';

const AppContent: React.FC = () => {
  const dispatch = useAppDispatch();
  const { isAuthenticated, loading } = useAppSelector(state => state.auth);

  useEffect(() => {
    // Check authentication status on app load
    dispatch(checkAuthStatus());
  }, [dispatch]);

  // Show loading while checking auth
  if (loading.status) {
    return (
      <div className="app-loading">
        <LoadingSpinner />
        <p>Checking authentication...</p>
      </div>
    );
  }

  // Show auth check if not authenticated
  if (!isAuthenticated) {
    return <AuthCheck />;
  }

  // Show main dashboard if authenticated
  return <Dashboard />;
};

const App: React.FC = () => {
  return (
    <Provider store={store}>
      <div className="app">
        <AppContent />
      </div>
    </Provider>
  );
};

export default App;
