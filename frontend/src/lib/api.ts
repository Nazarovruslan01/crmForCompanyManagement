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
  BuildingBreakdown,
  TicketMetrics,
  PaymentMetrics,
  AidatTimeseries,
  ExportReport,
  ExportReportType,
  ExportFormat,
  Receipt,
  ExtraordinaryCharge,
  AgendaItem,
  MeetingProtocol,
  NotificationTemplate,
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
    list:   (params?: Record<string, string>, signal?: AbortSignal) => this.list<User>('/accounts/users/', params, signal),
    get:    (id: number, signal?: AbortSignal)                      => this.request<User>(`/accounts/users/${id}/`, { signal }),
    create: (data: Record<string, unknown>, signal?: AbortSignal)   => this.request<User>('/accounts/users/', { method: 'POST', body: JSON.stringify(data), signal }),
    update: (id: number, data: Record<string, unknown>, signal?: AbortSignal) => this.request<User>(`/accounts/users/${id}/`, { method: 'PATCH', body: JSON.stringify(data), signal }),
  };

  async changePassword(old_password: string, new_password: string): Promise<{ detail: string }> {
    return this.request<{ detail: string }>('/accounts/password/change/', {
      method: 'POST',
      body: JSON.stringify({ old_password, new_password }),
    });
  }

  // ─── Generic list helper ────────────────────────────────────────────────────
  // Cursor pagination: { next, previous, results }

  private list<T>(path: string, params?: Record<string, string>, signal?: AbortSignal): Promise<PaginatedResponse<T>> {
    const qs = params ? `?${new URLSearchParams(params)}` : '';
    return this.request<PaginatedResponse<T>>(`${path}${qs}`, { signal });
  }

  /** Generic CRUD factory — replaces boilerplate per-entity definitions. */
  crud<T>(basePath: string) {
    return {
      list:   (params?: Record<string, string>, signal?: AbortSignal) => this.list<T>(`${basePath}/`, params, signal),
      get:    (id: number, signal?: AbortSignal)              => this.request<T>(`${basePath}/${id}/`, { signal }),
      create: (data: Partial<T>, signal?: AbortSignal)       => this.request<T>(`${basePath}/`,   { method: 'POST', body: JSON.stringify(data), signal }),
      update: (id: number, data: Partial<T>, signal?: AbortSignal) => this.request<T>(`${basePath}/${id}/`, { method: 'PATCH', body: JSON.stringify(data), signal }),
      delete: (id: number, signal?: AbortSignal)              => this.request<void>(`${basePath}/${id}/`, { method: 'DELETE', signal }),
    };
  }

  // ─── Properties ─────────────────────────────────────────────────────────────

  buildings = {
    ...this.crud<Building>('/properties/buildings'),
    chessboard: (id: number, signal?: AbortSignal) => this.request<ChessboardResponse>(`/properties/buildings/${id}/chessboard/`, { signal }),
    generateApartments: (id: number, data: {
      blocks: { name: string; floors: number; apartments_per_floor: number; numbering: 'floor_based' | 'sequential' }[];
      clear_existing?: boolean;
    }, signal?: AbortSignal) => this.request<{ created: number; building_id: number }>(
      `/properties/buildings/${id}/generate_apartments/`,
      { method: 'POST', body: JSON.stringify(data), signal },
    ),
  };
  apartments   = this.crud<Apartment>  ('/properties/apartments');

  residents      = this.crud<Resident>       ('/residents/residents');
  ownerships     = {
    list:        (params?: Record<string, string>, signal?: AbortSignal) => this.list<Ownership>('/residents/ownerships/', params, signal),
    byApartment: (apartmentId: number, signal?: AbortSignal) => this.request<Ownership[]>(`/residents/ownerships/by_apartment/?apartment_id=${apartmentId}`, { signal }),
  };
  personalAccounts = { list: (params?: Record<string, string>, signal?: AbortSignal) => this.list<PersonalAccount>('/residents/accounts/', params, signal) };

  // ─── Tickets ────────────────────────────────────────────────────────────────

  tickets = {
    ...this.crud<Ticket>('/tickets/tickets'),
    resolve: (id: number, signal?: AbortSignal) => this.request<Ticket>(`/tickets/tickets/${id}/resolve/`, { method: 'POST', signal }),
    close:   (id: number, signal?: AbortSignal) => this.request<Ticket>(`/tickets/tickets/${id}/close/`,  { method: 'POST', signal }),
  };

  comments = { list: (params?: Record<string, string>, signal?: AbortSignal) => this.list<TicketComment>('/tickets/comments/', params, signal), create: (data: Partial<TicketComment>, signal?: AbortSignal) => this.request<TicketComment>('/tickets/comments/', { method: 'POST', body: JSON.stringify(data), signal }) };

  // ─── Billing ────────────────────────────────────────────────────────────────

  aidatCharges = {
    list: (params?: Record<string, string>, signal?: AbortSignal) => this.list<AidatCharge>('/billing/aidat-charges/', params, signal),
    get: (id: number, signal?: AbortSignal) => this.request<AidatCharge>(`/billing/aidat-charges/${id}/`, { signal }),
    overdue: (params?: Record<string, string>, signal?: AbortSignal) => this.list<AidatCharge>('/billing/aidat-charges/overdue/', params, signal),
  };

  payments = {
    list: (params?: Record<string, string>, signal?: AbortSignal) => this.list<Payment>('/billing/payments/', params, signal),
    get: (id: number, signal?: AbortSignal) => this.request<Payment>(`/billing/payments/${id}/`, { signal }),
    create: (data: Partial<Payment>, idempotencyKey?: string, signal?: AbortSignal) =>
      this.request<Payment>('/billing/payments/', {
        method: 'POST',
        headers: idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : {},
        body: JSON.stringify(data),
        signal,
      }),
  };

  receipts = {
    list:     (params?: Record<string, string>, signal?: AbortSignal) => this.list<Receipt>('/billing/receipts/', params, signal),
    get:      (id: number, signal?: AbortSignal) => this.request<Receipt>(`/billing/receipts/${id}/`, { signal }),
    download: (id: number, signal?: AbortSignal) => this.downloadFile(`/billing/receipts/${id}/download/`, signal),
  };

  extraordinaryCharges = this.crud<ExtraordinaryCharge>('/billing/extraordinary-charges');

  reports = {
    list:     (params?: Record<string, string>, signal?: AbortSignal) => this.list<ExportReport>('/reports/exports/', params, signal),
    create:   (data: { report_type: ExportReportType; format: ExportFormat; filters?: Record<string, unknown> }, signal?: AbortSignal) =>
                this.request<ExportReport>('/reports/exports/', { method: 'POST', body: JSON.stringify(data), signal }),
    download: (id: number, signal?: AbortSignal) => this.downloadFile(`/reports/exports/${id}/download/`, signal),
  };

  // ─── Staff ──────────────────────────────────────────────────────────────────

  employees    = this.crud<Employee>      ('/staff/employees');
  departments  = this.crud<Department>    ('/staff/departments');
  tasks        = this.crud<Task>          ('/staff/tasks');

  // ─── Notifications ───────────────────────────────────────────────────────────

  notificationLogs      = {
    list: (params?: Record<string, string>, signal?: AbortSignal) => this.list<NotificationLog>('/notifications/logs/', params, signal),
  };
  notificationTemplates = this.crud<NotificationTemplate>('/notifications/templates');

  // ─── Documents ───────────────────────────────────────────────────────────────

  documents = {
    ...this.crud<Document>('/documents/documents'),
    upload: (formData: FormData, signal?: AbortSignal) =>
      this.request<Document>('/documents/documents/', { method: 'POST', body: formData, signal }),
  };

  // ─── Meetings ─────────────────────────────────────────────────────────────────

  meetings = {
    ...this.crud<Meeting>('/meetings/meetings'),
    start: (id: number, signal?: AbortSignal) => this.request<Meeting>(`/meetings/meetings/${id}/start/`, { method: 'POST', signal }),
    close: (id: number, signal?: AbortSignal) => this.request<Meeting>(`/meetings/meetings/${id}/close/`,  { method: 'POST', signal }),
    vote:  (id: number, agendaItemId: number, voteChoice: 'yes' | 'no' | 'abstain', signal?: AbortSignal) =>
      this.request<Meeting>(`/meetings/meetings/${id}/vote/`, {
        method: 'POST',
        body: JSON.stringify({ agenda_item: agendaItemId, vote_choice: voteChoice }),
        signal,
      }),
  };

  agendaItems = this.crud<AgendaItem>('/meetings/agenda-items');
  protocols   = this.crud<MeetingProtocol>('/meetings/protocols');

  // ─── File download ───────────────────────────────────────────────────────────

  async downloadFile(endpoint: string, signal?: AbortSignal): Promise<{ blob: Blob; filename?: string }> {
    const url = `${API_BASE}${endpoint}`;
    const headers: Record<string, string> = {};
    const token = this.getAccessToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;

    let response = await fetch(url, { headers, credentials: 'include', signal });

    if (response.status === 401) {
      const refreshed = await this.refreshAccessToken();
      if (refreshed) {
        headers['Authorization'] = `Bearer ${this.accessToken}`;
        response = await fetch(url, { headers, credentials: 'include', signal });
      }
    }

    if (!response.ok) {
      const text = await response.text().catch(() => '');
      const isJson = response.headers.get('content-type')?.includes('application/json');
      let body: Record<string, unknown> = {};
      if (isJson) { try { body = JSON.parse(text) as Record<string, unknown>; } catch { /* ignore */ } }
      const message = (body.detail ?? body.error ?? (text.slice(0, 120) || `HTTP ${response.status}`)) as string;
      throw new Error(message);
    }

    const disposition = response.headers.get('Content-Disposition');
    const filenameMatch = disposition?.match(/filename="?([^";\n]+)"?/);
    const rawFilename = filenameMatch?.[1];
    const safeFilename = rawFilename
      ? rawFilename.replace(/[^a-zA-Z0-9._\-() ]/g, '_').replace(/^\.+/, '')
      : undefined;
    return { blob: await response.blob(), filename: safeFilename };
  }

  // ─── Dashboard ───────────────────────────────────────────────────────────────

  private dashboardEndpoint<T>(key: string) {
    return (signal?: AbortSignal) => this.request<T>(`/dashboard/${key}/`, { signal });
  }

  dashboard = {
    summary: this.dashboardEndpoint<DashboardSummary>('summary'),
    buildingBreakdown: this.dashboardEndpoint<BuildingBreakdown>('building-breakdown'),
    ticketMetrics: this.dashboardEndpoint<TicketMetrics>('ticket-metrics'),
    paymentMetrics: this.dashboardEndpoint<PaymentMetrics>('payment-metrics'),
    aidatTimeseries: this.dashboardEndpoint<AidatTimeseries>('aidat-timeseries'),
  };
}

export const api = new ApiClient();
