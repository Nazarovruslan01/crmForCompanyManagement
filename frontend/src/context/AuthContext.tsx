/* eslint-disable react-refresh/only-export-components */
import { createContext, useState, useCallback, useEffect, type ReactNode } from 'react';
import type { User } from '../types';
import { api } from '../lib/api';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      if (!api.getAccessToken()) {
        setIsLoading(false);
        return;
      }

      try {
        const userData = await api.getCurrentUser() as User;
        setUser(userData);
      } catch {
        api.clearTokens();
      } finally {
        setIsLoading(false);
      }
    };

    void checkAuth();
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const response = await api.login(username, password);
    setUser(response.user);
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.logout();
    } catch {
      // Server-side token blacklist may fail (network error, server down).
      // Always clear local state regardless.
    }
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
