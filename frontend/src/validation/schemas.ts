import { z } from 'zod';

// ─── Auth ─────────────────────────────────────────────────────────────────────

export const loginSchema = z.object({
  username: z.string().min(1, 'Введите логин'),
  password: z.string().min(1, 'Введите пароль'),
});

export type LoginFormData = z.infer<typeof loginSchema>;

export const mfaSchema = z.object({
  mfaCode: z.string().length(6, 'Код должен содержать 6 цифр').regex(/^\d+$/, 'Код должен содержать только цифры'),
});

export type MFAFormData = z.infer<typeof mfaSchema>;

// ─── Tickets ──────────────────────────────────────────────────────────────────

export const ticketSchema = z.object({
  apartment: z.string().min(1, 'Выберите квартиру'),
  category: z.enum(['plumbing', 'electrical', 'cleaning', 'security', 'noise', 'general'], { error: 'Выберите категорию' }),
  priority: z.enum(['low', 'medium', 'high', 'urgent'], { error: 'Выберите приоритет' }),
  status: z.enum(['new', 'assigned', 'in_progress', 'resolved', 'closed']).optional(),
  title: z.string().min(3, 'Минимум 3 символа').max(200, 'Максимум 200 символов'),
  description: z.string().min(10, 'Минимум 10 символов').max(2000, 'Максимум 2000 символов'),
  assigned_worker: z.string().optional(),
});

export type TicketFormData = z.infer<typeof ticketSchema>;

// ─── Apartments ─────────────────────────────────────────────────────────────────

export const apartmentSchema = z.object({
  building: z.string().min(1, 'Выберите здание'),
  apartment_number: z.string().min(1, 'Введите номер квартиры').max(20, 'Максимум 20 символов'),
  floor: z.string().optional(),
  block: z.string().optional(),
  square_meters: z.string().optional(),
  share_ratio_num: z.string().min(1, 'Введите числитель'),
  share_ratio_denom: z.string().min(1, 'Введите знаменатель'),
  tapu_number: z.string().optional(),
  status: z.enum(['active', 'inactive', 'pending_handover'], { error: 'Выберите статус' }),
});

export type ApartmentFormData = z.infer<typeof apartmentSchema>;

// ─── Users ──────────────────────────────────────────────────────────────────────

export const userSchema = z.object({
  username: z.string().min(3, 'Минимум 3 символа').max(30, 'Максимум 30 символов'),
  email: z.string().email('Неверный email'),
  first_name: z.string().min(1, 'Введите имя').max(50, 'Максимум 50 символов'),
  last_name: z.string().min(1, 'Введите фамилию').max(50, 'Максимум 50 символов'),
  role: z.string().min(1, 'Выберите роль'),
  phone: z.string().optional(),
  password: z.string().min(8, 'Минимум 8 символов').optional().or(z.literal('')),
  is_active: z.string().optional(),
});

export type UserFormData = z.infer<typeof userSchema>;

// ─── Employees ────────────────────────────────────────────────────────────────

export const employeeSchema = z.object({
  user: z.string().min(1, 'Выберите пользователя'),
  department: z.string().min(1, 'Выберите отдел'),
  role: z.string().min(1, 'Выберите роль'),
  phone: z.string().optional(),
  hire_date: z.string().min(1, 'Выберите дату приёма'),
  is_active: z.boolean(),
});

export type EmployeeFormData = z.infer<typeof employeeSchema>;

// ─── Buildings ──────────────────────────────────────────────────────────────────

export const buildingSchema = z.object({
  name: z.string().min(1, 'Введите название').max(100, 'Максимум 100 символов'),
  address: z.string().min(1, 'Введите адрес').max(200, 'Максимум 200 символов'),
  city: z.string().min(1, 'Введите город').max(50, 'Максимум 50 символов'),
  district: z.string().min(1, 'Введите район').max(50, 'Максимум 50 символов'),
  management_type: z.enum(['self_managed', 'external_company'], { error: 'Выберите тип управления' }),
  annual_budget: z.string().optional(),
});

export type BuildingFormData = z.infer<typeof buildingSchema>;

// ─── Residents ──────────────────────────────────────────────────────────────────

export const residentSchema = z.object({
  name: z.string().min(1, 'Введите имя').max(50, 'Максимум 50 символов'),
  surname: z.string().min(1, 'Введите фамилию').max(50, 'Максимум 50 символов'),
  phone: z.string().optional(),
  email: z.string().email('Неверный email').optional().or(z.literal('')),
  tc_kimlik_no: z.string().optional(),
  passport_no: z.string().optional(),
  is_foreign_owner: z.boolean(),
  owner_type: z.string().min(1, 'Выберите тип владельца'),
});

export type ResidentFormData = z.infer<typeof residentSchema>;

// ─── Documents ──────────────────────────────────────────────────────────────────

export const documentSchema = z.object({
  title: z.string().min(1, 'Введите название').max(200, 'Максимум 200 символов'),
  description: z.string().optional(),
  document_type: z.string().min(1, 'Выберите тип документа'),
  building: z.string().optional(),
  apartment: z.string().optional(),
  resident: z.string().optional(),
});

export type DocumentFormData = z.infer<typeof documentSchema>;

// ─── Meetings ───────────────────────────────────────────────────────────────────

export const meetingSchema = z.object({
  building: z.string().min(1, 'Выберите здание'),
  title: z.string().min(3, 'Минимум 3 символа').max(200, 'Максимум 200 символов'),
  description: z.string().optional(),
  scheduled_date: z.string().min(1, 'Выберите дату'),
  quorum_required: z.string().min(1, 'Введите кворум'),
});

export type MeetingFormData = z.infer<typeof meetingSchema>;
