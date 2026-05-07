import type {
  AuthResponse,
  MFARequiredResponse,
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

const API_BASE = import.meta.env.VITE_API_BASE || '/api/v2';

class ApiClient {
  private accessToken: string | null = null;
  private refreshPromise: Promise<boolean> | null = null;

  setTokens(access: string) {
    this.accessToken = access;
  }

  clearTokens() {
    this.accessToken = null;
  }

  getAccessToken(): string | null {
    return this.accessToken;
  }

  /** Silent refresh — called on app init to recover session from httpOnly cookie. */
  async silentRefresh(): Promise<boolean> {
    return this.refreshAccessToken();
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    const isFormData = options.body instanceof FormData;
    const headers: Record<string, string> = isFormData
      ? { ...(options.headers as Record<string, string>) }
      : { 'Content-Type': 'application/json', ...(options.headers as Record<string, string>) };

    const token = this.getAccessToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;

    let response = await fetch(url, { ...options, headers, credentials: 'include' });

    if (response.status === 401) {
      const refreshed = await this.refreshAccessToken();
      if (refreshed) {
        headers['Authorization'] = `Bearer ${this.accessToken}`;
        response = await fetch(url, { ...options, headers, credentials: 'include' });
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

  /** Promise-based mutex — concurrent 401s share a single refresh request. */
  private async refreshAccessToken(): Promise<boolean> {
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    this.refreshPromise = this._doRefresh();
    try {
      return await this.refreshPromise;
    } finally {
      this.refreshPromise = null;
    }
  }

  private async _doRefresh(): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE}/auth/token/refresh/`, {
        method: 'POST',
        credentials: 'include',
      });

      if (!response.ok) { this.clearTokens(); return false; }

      const data = await response.json() as { access: string };
      this.accessToken = data.access;
      return true;
    } catch {
      this.clearTokens();
      return false;
    }
  }

  // ─── Auth ───────────────────────────────────────────────────────────────────

  async login(username: string, password: string): Promise<AuthResponse | MFARequiredResponse> {
    const data = await this.request<AuthResponse | MFARequiredResponse>('/accounts/login/', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    if ('access' in data) {
      this.setTokens(data.access);
    }
    return data;
  }

  async verifyMFA(temp_token: string, code: string): Promise<AuthResponse> {
    const data = await this.request<AuthResponse>('/accounts/mfa/verify/', {
      method: 'POST',
      body: JSON.stringify({ temp_token, code }),
    });
    this.setTokens(data.access);
    return data;
  }

  async logout(): Promise<void> {
    try {
      await this.request('/accounts/logout/', { method: 'POST' });
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
