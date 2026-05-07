/* eslint-disable react-refresh/only-export-components */
import { createContext, useState, useCallback, useEffect, type ReactNode } from 'react';
import type { User } from '../types';
import { api } from '../lib/api';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  mfaPending: boolean;
  login: (username: string, password: string) => Promise<{ requiresMfa: boolean; tempToken?: string }>;
  verifyMFA: (tempToken: string, code: string) => Promise<void>;
  logout: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [mfaPending, setMfaPending] = useState(false);

  useEffect(() => {
    const initAuth = async () => {
      const refreshed = await api.silentRefresh();
      if (refreshed) {
        try {
          const userData = await api.getCurrentUser() as User;
          setUser(userData);
        } catch {
          api.clearTokens();
        }
      }
      setIsLoading(false);
    };

    void initAuth();
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const response = await api.login(username, password);
    if ('requires_mfa' in response) {
      setMfaPending(true);
      return { requiresMfa: true, tempToken: response.temp_token };
    }
    setUser(response.user);
    setMfaPending(false);
    return { requiresMfa: false };
  }, []);

  const verifyMFA = useCallback(async (tempToken: string, code: string) => {
    const response = await api.verifyMFA(tempToken, code);
    setUser(response.user);
    setMfaPending(false);
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.logout();
    } catch {
      // Server-side token blacklist may fail (network error, server down).
      // Always clear local state regardless.
    }
    setUser(null);
    setMfaPending(false);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        mfaPending,
        login,
        verifyMFA,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
