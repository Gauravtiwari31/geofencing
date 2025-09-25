/**
 * Redux slice for authentication state management
 * Handles user authentication and session management
 */

import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { AuthStatus, UserInfo } from '../types/incident';
import apiService from '../services/api';

// Async thunks for auth operations
export const checkAuthStatus = createAsyncThunk(
  'auth/checkAuthStatus',
  async () => {
    return await apiService.getAuthStatus();
  }
);

export const getCurrentUser = createAsyncThunk(
  'auth/getCurrentUser',
  async () => {
    return await apiService.getCurrentUser();
  }
);

export const logout = createAsyncThunk(
  'auth/logout',
  async () => {
    await apiService.logout();
  }
);

// State interface
interface AuthState {
  isAuthenticated: boolean;
  user: UserInfo | null;
  loading: {
    status: boolean;
    user: boolean;
    logout: boolean;
  };
  error: {
    status: string | null;
    user: string | null;
    logout: string | null;
  };
  lastChecked: string | null;
}

// Initial state
const initialState: AuthState = {
  isAuthenticated: false,
  user: null,
  loading: {
    status: false,
    user: false,
    logout: false
  },
  error: {
    status: null,
    user: null,
    logout: null
  },
  lastChecked: null
};

// Slice
const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    // Clear errors
    clearError: (state, action: PayloadAction<keyof AuthState['error']>) => {
      state.error[action.payload] = null;
    },
    clearAllErrors: (state) => {
      Object.keys(state.error).forEach(key => {
        state.error[key as keyof AuthState['error']] = null;
      });
    },
    
    // Reset auth state (for logout)
    resetAuthState: (state) => {
      state.isAuthenticated = false;
      state.user = null;
      state.lastChecked = null;
      state.error = {
        status: null,
        user: null,
        logout: null
      };
    }
  },
  extraReducers: (builder) => {
    // Check auth status
    builder
      .addCase(checkAuthStatus.pending, (state) => {
        state.loading.status = true;
        state.error.status = null;
      })
      .addCase(checkAuthStatus.fulfilled, (state, action) => {
        state.loading.status = false;
        state.isAuthenticated = action.payload.authenticated;
        state.user = action.payload.user || null;
        state.lastChecked = new Date().toISOString();
      })
      .addCase(checkAuthStatus.rejected, (state, action) => {
        state.loading.status = false;
        state.error.status = action.error.message || 'Failed to check authentication status';
        state.isAuthenticated = false;
        state.user = null;
      });

    // Get current user
    builder
      .addCase(getCurrentUser.pending, (state) => {
        state.loading.user = true;
        state.error.user = null;
      })
      .addCase(getCurrentUser.fulfilled, (state, action) => {
        state.loading.user = false;
        state.user = action.payload;
        state.isAuthenticated = action.payload.authenticated;
      })
      .addCase(getCurrentUser.rejected, (state, action) => {
        state.loading.user = false;
        state.error.user = action.error.message || 'Failed to get user information';
      });

    // Logout
    builder
      .addCase(logout.pending, (state) => {
        state.loading.logout = true;
        state.error.logout = null;
      })
      .addCase(logout.fulfilled, (state) => {
        state.loading.logout = false;
        state.isAuthenticated = false;
        state.user = null;
        state.lastChecked = null;
      })
      .addCase(logout.rejected, (state, action) => {
        state.loading.logout = false;
        state.error.logout = action.error.message || 'Failed to logout';
      });
  }
});

// Export actions
export const {
  clearError,
  clearAllErrors,
  resetAuthState
} = authSlice.actions;

// Export reducer
export default authSlice.reducer;
