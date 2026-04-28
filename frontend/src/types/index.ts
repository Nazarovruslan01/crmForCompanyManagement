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
  refresh: string;
  user: User;
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
