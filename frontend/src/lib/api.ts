import type { AuthResponse } from '../types';

const API_BASE = '/api/v1';

class ApiClient {
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  setTokens(access: string, refresh: string) {
    this.accessToken = access;
    this.refreshToken = refresh;
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
  }

  clearTokens() {
    this.accessToken = null;
    this.refreshToken = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  getAccessToken(): string | null {
    if (!this.accessToken) {
      this.accessToken = localStorage.getItem('access_token');
    }
    return this.accessToken;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    const token = this.getAccessToken();
    if (token) {
      (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (response.status === 401 && this.refreshToken) {
      const refreshed = await this.refreshAccessToken();
      if (refreshed) {
        const retryHeaders = { ...headers };
        (retryHeaders as Record<string, string>)['Authorization'] = `Bearer ${this.accessToken}`;
        const retryResponse = await fetch(url, {
          ...options,
          headers: retryHeaders,
        });
        if (!retryResponse.ok) {
          throw new Error(`HTTP ${retryResponse.status}`);
        }
        return retryResponse.json();
      }
    }

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return response.json();
  }

  private async refreshAccessToken(): Promise<boolean> {
    if (!this.refreshToken) return false;

    try {
      const response = await fetch(`${API_BASE}/auth/token/refresh/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh: this.refreshToken }),
      });

      if (!response.ok) {
        this.clearTokens();
        return false;
      }

      const data = await response.json();
      this.accessToken = data.access;
      localStorage.setItem('access_token', data.access);
      return true;
    } catch {
      this.clearTokens();
      return false;
    }
  }

  // Auth
  async login(username: string, password: string): Promise<AuthResponse> {
    const data = await this.request<AuthResponse>('/accounts/login/', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    this.setTokens(data.access, data.refresh);
    return data;
  }

  async logout(): Promise<void> {
    try {
      await this.request('/accounts/logout/', {
        method: 'POST',
        body: JSON.stringify({ refresh: this.refreshToken }),
      });
    } finally {
      this.clearTokens();
    }
  }

  async getCurrentUser() {
    return this.request('/accounts/me/');
  }

  // Generic CRUD
  async getList<T>(endpoint: string, params?: Record<string, string>) {
    const searchParams = params ? `?${new URLSearchParams(params)}` : '';
    return this.request<{ results: T[]; count: number }>(`${endpoint}/${searchParams}`);
  }

  async get<T>(endpoint: string) {
    return this.request<T>(endpoint);
  }

  async create<T>(endpoint: string, data: Partial<T>) {
    return this.request<T>(`${endpoint}/`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async update<T>(endpoint: string, data: Partial<T>) {
    return this.request<T>(`${endpoint}/`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async delete(endpoint: string) {
    return this.request<void>(`${endpoint}/`, {
      method: 'DELETE',
    });
  }
}

export const api = new ApiClient();
