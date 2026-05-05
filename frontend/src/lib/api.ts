import type {
  AuthResponse,
  PaginatedResponse,
  Building,
  Apartment,
  Resident,
  Ownership,
  PersonalAccount,
  Ticket,
  TicketComment,
  AidatCharge,
  Payment,
  Department,
  Employee,
  Task,
  NotificationLog,
  Document,
  Meeting,
  User,
  ChessboardResponse,
  DashboardSummary,
} from '../types';

const API_BASE = '/api/v2';

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

  private getRefreshToken(): string | null {
    if (!this.refreshToken) {
      this.refreshToken = localStorage.getItem('refresh_token');
    }
    return this.refreshToken;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    const isFormData = options.body instanceof FormData;
    const headers: Record<string, string> = isFormData
      ? { ...(options.headers as Record<string, string>) }
      : { 'Content-Type': 'application/json', ...(options.headers as Record<string, string>) };

    const token = this.getAccessToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;

    let response = await fetch(url, { ...options, headers });

    if (response.status === 401) {
      const refreshed = await this.refreshAccessToken();
      if (refreshed) {
        headers['Authorization'] = `Bearer ${this.accessToken}`;
        response = await fetch(url, { ...options, headers });
      }
    }

    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      const message = body?.detail ?? body?.error ?? `HTTP ${response.status}`;
      throw new Error(message as string);
    }

    if (response.status === 204) return undefined as T;
    return response.json() as Promise<T>;
  }

  private async refreshAccessToken(): Promise<boolean> {
    const refresh = this.getRefreshToken();
    if (!refresh) return false;

    try {
      const response = await fetch(`${API_BASE}/auth/token/refresh/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh }),
      });

      if (!response.ok) { this.clearTokens(); return false; }

      const data = await response.json() as { access: string };
      this.accessToken = data.access;
      localStorage.setItem('access_token', data.access);
      return true;
    } catch {
      this.clearTokens();
      return false;
    }
  }

  // ─── Auth ───────────────────────────────────────────────────────────────────

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
        body: JSON.stringify({ refresh: this.getRefreshToken() }),
      });
    } finally {
      this.clearTokens();
    }
  }

  async getCurrentUser(): Promise<User> {
    return this.request<User>('/accounts/me/');
  }

  users = {
    list:   (params?: Record<string, string>) => this.list<User>('/accounts/users/', params),
    get:    (id: number)                      => this.request<User>(`/accounts/users/${id}/`),
    create: (data: Record<string, unknown>)   => this.request<User>('/accounts/users/', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: number, data: Record<string, unknown>) => this.request<User>(`/accounts/users/${id}/`, { method: 'PATCH', body: JSON.stringify(data) }),
  };

  async changePassword(old_password: string, new_password: string): Promise<{ detail: string }> {
    return this.request<{ detail: string }>('/accounts/password/change/', {
      method: 'POST',
      body: JSON.stringify({ old_password, new_password }),
    });
  }

  // ─── Generic list helper ────────────────────────────────────────────────────
  // Cursor pagination: { next, previous, results }

  private list<T>(path: string, params?: Record<string, string>): Promise<PaginatedResponse<T>> {
    const qs = params ? `?${new URLSearchParams(params)}` : '';
    return this.request<PaginatedResponse<T>>(`${path}${qs}`);
  }

  /** Generic CRUD factory — replaces boilerplate per-entity definitions. */
  crud<T>(basePath: string) {
    return {
      list:   (params?: Record<string, string>) => this.list<T>(`${basePath}/`, params),
      get:    (id: number)              => this.request<T>(`${basePath}/${id}/`),
      create: (data: Partial<T>)       => this.request<T>(`${basePath}/`,   { method: 'POST', body: JSON.stringify(data) }),
      update: (id: number, data: Partial<T>) => this.request<T>(`${basePath}/${id}/`, { method: 'PATCH', body: JSON.stringify(data) }),
      delete: (id: number)              => this.request<void>(`${basePath}/${id}/`, { method: 'DELETE' }),
    };
  }

  // ─── Properties ─────────────────────────────────────────────────────────────

  buildings = {
    ...this.crud<Building>('/properties/buildings'),
    chessboard: (id: number) => this.request<ChessboardResponse>(`/properties/buildings/${id}/chessboard/`),
    generateApartments: (id: number, data: {
      blocks: { name: string; floors: number; apartments_per_floor: number; numbering: 'floor_based' | 'sequential' }[];
      clear_existing?: boolean;
    }) => this.request<{ created: number; building_id: number }>(
      `/properties/buildings/${id}/generate_apartments/`,
      { method: 'POST', body: JSON.stringify(data) },
    ),
  };
  apartments   = this.crud<Apartment>  ('/properties/apartments');

  residents      = this.crud<Resident>       ('/residents/residents');
  ownerships     = {
    list:        (params?: Record<string, string>) => this.list<Ownership>('/residents/ownerships/', params),
    byApartment: (apartmentId: number) => this.request<Ownership[]>(`/residents/ownerships/by_apartment/?apartment_id=${apartmentId}`),
  };
  personalAccounts = { list: (params?: Record<string, string>) => this.list<PersonalAccount>('/residents/accounts/', params) };

  // ─── Tickets ────────────────────────────────────────────────────────────────

  tickets = {
    ...this.crud<Ticket>('/tickets/tickets'),
    resolve: (id: number) => this.request<Ticket>(`/tickets/tickets/${id}/resolve/`, { method: 'POST' }),
    close:   (id: number) => this.request<Ticket>(`/tickets/tickets/${id}/close/`,  { method: 'POST' }),
  };

  comments = { list: (params?: Record<string, string>) => this.list<TicketComment>('/tickets/comments/', params), create: (data: Partial<TicketComment>) => this.request<TicketComment>('/tickets/comments/', { method: 'POST', body: JSON.stringify(data) }) };

  // ─── Billing ────────────────────────────────────────────────────────────────

  aidatCharges = {
    list: (params?: Record<string, string>) => this.list<AidatCharge>('/billing/aidat-charges/', params),
    get: (id: number) => this.request<AidatCharge>(`/billing/aidat-charges/${id}/`),
    overdue: (params?: Record<string, string>) => this.list<AidatCharge>('/billing/aidat-charges/overdue/', params),
  };

  payments = {
    list: (params?: Record<string, string>) => this.list<Payment>('/billing/payments/', params),
    get: (id: number) => this.request<Payment>(`/billing/payments/${id}/`),
    create: (data: Partial<Payment>, idempotencyKey?: string) =>
      this.request<Payment>('/billing/payments/', {
        method: 'POST',
        headers: idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : {},
        body: JSON.stringify(data),
      }),
  };

  // ─── Staff ──────────────────────────────────────────────────────────────────

  employees    = this.crud<Employee>      ('/staff/employees');
  departments  = { list: (params?: Record<string, string>) => this.list<Department>('/staff/departments/', params) };
  tasks        = { list: (params?: Record<string, string>) => this.list<Task>('/staff/tasks/', params) };

  // ─── Notifications ───────────────────────────────────────────────────────────

  notificationLogs = {
    list: (params?: Record<string, string>) => this.list<NotificationLog>('/notifications/logs/', params),
  };

  // ─── Documents ───────────────────────────────────────────────────────────────

  documents = {
    ...this.crud<Document>('/documents/documents'),
    upload: (formData: FormData) =>
      this.request<Document>('/documents/documents/', { method: 'POST', body: formData }),
  };

  // ─── Meetings ─────────────────────────────────────────────────────────────────

  meetings = {
    ...this.crud<Meeting>('/meetings/meetings'),
    start: (id: number) => this.request<Meeting>(`/meetings/meetings/${id}/start/`, { method: 'POST' }),
    close: (id: number) => this.request<Meeting>(`/meetings/meetings/${id}/close/`,  { method: 'POST' }),
    vote:  (id: number, agendaItemId: number, voteChoice: 'yes' | 'no' | 'abstain') =>
      this.request<Meeting>(`/meetings/meetings/${id}/vote/`, {
        method: 'POST',
        body: JSON.stringify({ agenda_item: agendaItemId, vote_choice: voteChoice }),
      }),
  };

  // ─── Dashboard ───────────────────────────────────────────────────────────────

  dashboard = {
    summary: () => this.request<DashboardSummary>('/dashboard/summary/'),
  };
}

export const api = new ApiClient();
