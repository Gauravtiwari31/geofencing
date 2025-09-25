/**
 * Redux store configuration for Police SEDI
 * Configures the store with RTK and middleware
 */

import { configureStore } from '@reduxjs/toolkit';
import incidentReducer from './incidentSlice';
import authReducer from './authSlice';

export const store = configureStore({
  reducer: {
    incidents: incidentReducer,
    auth: authReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        // Ignore these action types for serialization checks
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
      },
    }),
  devTools: process.env.NODE_ENV !== 'production',
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
