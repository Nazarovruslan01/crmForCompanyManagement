// ─── Pagination ───────────────────────────────────────────────────────────────
// Backend uses cursor pagination: no `count` field.
export interface PaginatedResponse<T> {
  next: string | null;
  previous: string | null;
  results: T[];
}

// ─── Auth ─────────────────────────────────────────────────────────────────────
export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: 'admin' | 'manager' | 'worker' | 'resident';
  role_display: string;
  phone: string | null;
  tc_kimlik_no: string | null;
  is_active: boolean;
  is_staff: boolean;
  is_superuser: boolean;
  date_joined: string;
  last_login: string | null;
}

export interface AuthResponse {
  access: string;
  user: User;
}

export interface MFARequiredResponse {
  requires_mfa: true;
  temp_token: string;
}

// ─── Properties ───────────────────────────────────────────────────────────────
export interface Building {
  id: number;
  name: string;
  address: string;
  city: string;
  district: string;
  management_type: 'self_managed' | 'external_company';
  management_type_display: string;
  annual_budget: string | null;
  created_at: string;
  updated_at: string;
}

export interface Apartment {
  id: number;
  building: number;
  building_display: string;
  apartment_number: string;
  floor: number | null;
  block: string | null;
  square_meters: string | null;
  share_ratio_num: number;
  share_ratio_denom: number;
  share_ratio: string;
  tapu_number: string | null;
  status: 'active' | 'inactive' | 'pending_handover';
  status_display: string;
  created_at: string;
  updated_at: string;
}

export interface ApartmentMinimal {
  id: number;
  building_name: string;
  apartment_number: string;
  block: string | null;
}

// ─── Residents ────────────────────────────────────────────────────────────────
export interface Resident {
  id: number;
  user: number | null;
  tc_kimlik_no: string | null;
  passport_no: string | null;
  name: string;
  surname: string;
  full_name: string;
  phone: string | null;
  email: string | null;
  is_foreign_owner: boolean;
  owner_type: string;
  owner_type_display: string;
  created_at: string;
  updated_at: string;
}

export interface Ownership {
  id: number;
  resident: number;
  resident_display: string;
  apartment: number;
  apartment_display: string;
  role: string;
  role_display: string;
  share_ratio_num: number;
  share_ratio_denom: number;
  start_date: string;
  end_date: string | null;
  is_primary: boolean;
  created_at: string;
}

export interface PersonalAccount {
  id: number;
  apartment: number;
  apartment_display: string;
  account_number: string;
  balance: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// ─── Tickets ──────────────────────────────────────────────────────────────────
export type TicketCategory = 'plumbing' | 'electrical' | 'cleaning' | 'security' | 'noise' | 'general';
export type TicketPriority = 'low' | 'medium' | 'high' | 'urgent';
export type TicketStatus = 'new' | 'assigned' | 'in_progress' | 'resolved' | 'closed';

export interface TicketAttachment {
  id: number;
  ticket: number;
  file_url: string;
  file_name: string;
  file_type: string;
  uploaded_by: number;
  uploaded_by_display: string;
  uploaded_at: string;
}

export interface Ticket {
  id: number;
  apartment: number;
  apartment_detail: ApartmentMinimal;
  category: TicketCategory;
  category_display: string;
  priority: TicketPriority;
  priority_display: string;
  status: TicketStatus;
  status_display: string;
  title: string;
  description: string;
  photo_urls: string[] | null;
  assigned_worker: number | null;
  assigned_worker_display: string | null;
  created_by: number;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
  comments?: TicketComment[];
  attachments?: TicketAttachment[];
}

export interface TicketComment {
  id: number;
  ticket: number;
  author: number;
  author_display: string;
  content: string;
  photo_urls: string[] | null;
  created_at: string;
}

// ─── Billing ──────────────────────────────────────────────────────────────────
export type AidatStatus = 'pending' | 'overdue' | 'paid' | 'cancelled';

export interface AidatCharge {
  id: number;
  apartment: number;
  apartment_display: string;
  billing_period_start: string;
  billing_period_end: string;
  base_amount: string;
  late_fee_rate: string | null;
  due_date: string;
  status: AidatStatus;
  status_display: string;
  paid_at: string | null;
  paid_amount: string | null;
  created_at: string;
  updated_at: string;
}

export interface Payment {
  id: number;
  apartment: number;
  apartment_display: string;
  charge_type: 'aidat' | 'extraordinary';
  charge_type_display: string;
  charge_id: number;
  amount: string;
  currency: string;
  payment_method: string;
  payment_method_display: string;
  bank_reference: string | null;
  receipt_number: string;
  idempotency_key: string;
  paid_at: string;
  created_at: string;
}

// ─── Staff ────────────────────────────────────────────────────────────────────
export interface Department {
  id: number;
  name: string;
  description: string | null;
}

export interface Employee {
  id: number;
  user: number;
  user_display: string;
  department: number;
  department_display: string;
  role: string;
  role_display: string;
  phone: string | null;
  is_active: boolean;
  hire_date: string;
  created_at: string;
  updated_at: string;
}

export interface Task {
  id: number;
  title: string;
  description: string | null;
  ticket: number | null;
  ticket_display: string | null;
  assigned_to: number;
  assigned_to_display: string;
  status: string;
  status_display: string;
  due_date: string;
  created_by: number;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

// ─── Documents ────────────────────────────────────────────────────────────────
export type DocumentType = 'contract' | 'protocol' | 'receipt' | 'act' | 'other';

export interface Document {
  id: number;
  title: string;
  description: string;
  file: string | null;
  document_type: DocumentType;
  document_type_display: string;
  building: number | null;
  building_display: string | null;
  apartment: number | null;
  apartment_display: string | null;
  resident: number | null;
  resident_display: string | null;
  uploaded_by: number | null;
  uploaded_by_display: string | null;
  created_at: string;
  updated_at: string;
}

// ─── Meetings ─────────────────────────────────────────────────────────────────
export type MeetingStatus = 'scheduled' | 'active' | 'completed' | 'cancelled';

export interface AgendaItem {
  id: number;
  meeting: number;
  title: string;
  description: string;
  order: number;
  created_at: string;
}

export interface Vote {
  id: number;
  agenda_item: number;
  resident: number;
  resident_display: string;
  vote_choice: 'yes' | 'no' | 'abstain';
  vote_choice_display: string;
  created_at: string;
}

export interface MeetingProtocol {
  id: number;
  meeting: number;
  content: string;
  file: string | null;
  approved_at: string | null;
  created_at: string;
}

export interface Meeting {
  id: number;
  building: number;
  building_display: string;
  title: string;
  description: string;
  scheduled_date: string;
  status: MeetingStatus;
  status_display: string;
  quorum_required: number;
  created_by: number | null;
  created_by_display: string | null;
  agenda_items: AgendaItem[];
  votes?: Vote[];
  protocol?: MeetingProtocol | null;
  created_at: string;
  updated_at: string;
}

// ─── Notifications ────────────────────────────────────────────────────────────
export interface NotificationLog {
  id: number;
  template: number;
  recipient: number;
  recipient_display: string;
  channel: string;
  channel_display: string;
  subject: string | null;
  body: string;
  status: 'pending' | 'sent' | 'delivered' | 'failed';
  status_display: string;
  external_id: string | null;
  error_message: string | null;
  sent_at: string | null;
  delivered_at: string | null;
  created_at: string;
}

// ─── Chessboard (Shakhmatka) ──────────────────────────────────────────────────

export interface ChessboardResident {
  id: number;
  name: string;
  surname: string;
  full_name: string;
  phone: string | null;
  owner_type: string;
}

export interface ChessboardApartment {
  id: number;
  apartment_number: string;
  floor: number | null;
  block: string | null;
  status: 'active' | 'inactive' | 'pending_handover';
  status_display: string;
  latest_aidat_status: AidatStatus | null;
  total_debt: string;
  primary_resident: ChessboardResident | null;
  residents: ChessboardResident[];
}

export interface ChessboardFloor {
  floor: number;
  apartments: ChessboardApartment[];
}

export interface ChessboardBlock {
  block: string;
  floors: ChessboardFloor[];
}

export interface ChessboardResponse {
  building: {
    id: number;
    name: string;
  };
  blocks: ChessboardBlock[];
}

// ─── Dashboard ───────────────────────────────────────────────────────────────

export interface DashboardSummary {
  buildings_count: number;
  active_tickets_count: number;
  residents_count: number;
  overdue_charges_count: number;
  total_debt: string;
  occupancy_rate: number;
  recent_tickets: Ticket[];
}

export interface BuildingBreakdownItem {
  building_id: number;
  building_name: string;
  apartment_count: number;
  occupied_count: number;
  occupancy_rate: number;
  pending_charges_count: number;
  overdue_charges_count: number;
  total_debt: string;
  active_tickets_count: number;
  resolved_tickets_count: number;
}

export interface BuildingBreakdown {
  buildings: BuildingBreakdownItem[];
}

export interface TicketMetricsCategory {
  category: string;
  count: number;
  percentage: number;
}

export interface TicketMetrics {
  avg_resolution_time_hours: number | null;
  by_category: Record<string, number>;
  by_status: Record<string, number>;
}

export interface PaymentMetricsTrend {
  month: string;
  collected: string;
  total: string;
}

export interface PaymentMetrics {
  total_collected: string;
  total_billed: string;
  total_due: string;
  collection_rate: number;
  monthly_trend: PaymentMetricsTrend[];
}

export interface AidatTimeseriesData {
  month: string;
  building_name: string;
  amount: string;
}

export interface AidatTimeseries {
  data: AidatTimeseriesData[];
}

// ─── Reports ──────────────────────────────────────────────────────────────────

export type ExportReportType = 'payments' | 'aidat_charges' | 'meetings' | 'residents' | 'apartments';
export type ExportFormat     = 'csv' | 'xlsx' | 'pdf';
export type ExportStatus     = 'pending' | 'processing' | 'completed' | 'failed';

export interface ExportReport {
  id: number;
  report_type: ExportReportType;
  format: ExportFormat;
  status: ExportStatus;
  filters: Record<string, unknown>;
  file: string | null;
  error_message: string;
  created_at: string;
  completed_at: string | null;
}

// ─── Notification Templates ───────────────────────────────────────────────────

export type NotificationChannel = 'push' | 'sms' | 'email' | 'telegram';
export type NotificationEventType =
  | 'aidat_reminder' | 'aidat_overdue' | 'payment_confirmation'
  | 'ticket_created' | 'ticket_assigned' | 'ticket_resolved'
  | 'meeting_reminder' | 'general';

export interface NotificationTemplate {
  id: number;
  name: string;
  notification_type: NotificationEventType;
  notification_type_display: string;
  channel: NotificationChannel;
  channel_display: string;
  subject: string;
  body_template: string;
  is_active: boolean;
}

// ─── Billing Receipts ─────────────────────────────────────────────────────────

export interface Receipt {
  id: number;
  payment: number;
  pdf_url: string | null;
  generated_at: string;
}

// ─── Extraordinary Charges ────────────────────────────────────────────────

export type ExtraordinaryChargeStatus = 'proposed' | 'approved' | 'rejected' | 'collecting' | 'collected';

export interface ExtraordinaryCharge {
  id: number;
  building: number;
  building_display: string;
  description: string;
  total_amount: string;
  assembly_resolution_number: string | null;
  approval_date: string | null;
  status: ExtraordinaryChargeStatus;
  status_display: string;
  due_date: string | null;
  created_at: string;
  updated_at: string;
}
