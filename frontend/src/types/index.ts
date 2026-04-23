export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: 'admin' | 'manager' | 'worker' | 'resident';
  role_display: string;
  phone: string;
  tc_kimlik_no: string;
  is_active: boolean;
  is_staff: boolean;
}

export interface AuthResponse {
  access: string;
  refresh: string;
  user: User;
}

export interface Building {
  id: number;
  name: string;
  address: string;
  city: string;
  district: string;
  management_type: 'self_managed' | 'external_company';
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
  block: string;
  square_meters: string | null;
  share_ratio_num: number;
  share_ratio_denom: number;
  share_ratio: string;
  tapu_number: string | null;
  status: 'active' | 'inactive' | 'pending_handover';
  created_at: string;
  updated_at: string;
}

export interface Ticket {
  id: number;
  apartment: number;
  apartment_detail: ApartmentMinimal;
  category: 'plumbing' | 'electrical' | 'cleaning' | 'security' | 'noise' | 'general';
  category_display: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  priority_display: string;
  status: 'new' | 'assigned' | 'in_progress' | 'resolved' | 'closed';
  status_display: string;
  title: string;
  description: string;
  photo_urls: string[];
  assigned_worker: number | null;
  assigned_worker_display: string | null;
  created_by: number;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
}

export interface ApartmentMinimal {
  id: number;
  building_name: string;
  apartment_number: string;
  block: string;
}
