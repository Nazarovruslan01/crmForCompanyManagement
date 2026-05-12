import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { api } from '../../lib/api';
import type { Employee, Department } from '../../types';
import { Modal } from '../ui/Modal';
import { Field, SelectField, CheckboxField, FormRow, FormActions } from '../ui/FormField';

interface Props {
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
  initial?: Employee;
}

const ROLE_OPTIONS = [
  { value: 'manager', label: 'Менеджер' },
  { value: 'worker', label: 'Рабочий' },
  { value: 'admin', label: 'Администратор' },
  { value: 'technician', label: 'Техник' },
  { value: 'security', label: 'Охрана' },
  { value: 'cleaner', label: 'Уборщик' },
];

export function EmployeeForm({ open, onClose, onSaved, initial }: Props) {
  const isEdit = !!initial;
  const [saving, setSaving] = useState(false);
  const [departments, setDepartments] = useState<Department[]>([]);

  const [form, setForm] = useState({
    user: String(initial?.user ?? ''),
    department: String(initial?.department ?? ''),
    role: initial?.role ?? 'worker',
    phone: initial?.phone ?? '',
    is_active: initial?.is_active ?? true,
    hire_date: initial?.hire_date ?? new Date().toISOString().slice(0, 10),
  });

  useEffect(() => {
    if (!open) return;
    api.departments.list().then(r => setDepartments(r.results)).catch(() => {});
  }, [open]);

  const set = (field: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm(f => ({ ...f, [field]: e.target.value }));

  const toggle = (field: 'is_active') => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm(f => ({ ...f, [field]: e.target.checked }));

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = {
        user: Number(form.user),
        department: Number(form.department),
        role: form.role,
        phone: form.phone || null,
        is_active: form.is_active,
        hire_date: form.hire_date,
      };
      if (isEdit) {
        await api.employees.update(initial!.id, payload);
        toast.success('Сотрудник обновлён');
      } else {
        await api.employees.create(payload);
        toast.success('Сотрудник добавлен');
      }
      onSaved();
      onClose();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Ошибка');
    } finally {
      setSaving(false);
    }
  }

  const deptOptions = departments.map(d => ({ value: d.id, label: d.name }));

  return (
    <Modal open={open} onClose={onClose} title={isEdit ? 'Редактировать сотрудника' : 'Новый сотрудник'}>
      <form onSubmit={submit}>
        <Field
          label="ID пользователя"
          required={!isEdit}
          type="number"
          min="1"
          value={form.user}
          onChange={set('user')}
          placeholder="ID существующего пользователя"
          hint="Введите ID пользователя из системы"
        />
        <SelectField
          label="Отдел"
          required
          value={form.department}
          onChange={set('department')}
          options={deptOptions}
          placeholder="Выберите отдел"
        />
        <FormRow>
          <SelectField
            label="Роль"
            required
            value={form.role}
            onChange={set('role')}
            options={ROLE_OPTIONS}
          />
          <Field label="Телефон" type="tel" value={form.phone} onChange={set('phone')} placeholder="+90 555 000 00 00" />
        </FormRow>
        <Field
          label="Дата приёма"
          required
          type="date"
          value={form.hire_date}
          onChange={set('hire_date')}
        />
        <CheckboxField
          label="Активен"
          checked={form.is_active}
          onChange={toggle('is_active')}
        />
        <FormActions>
          <button
            type="button"
            onClick={onClose}
            className="btn-ghost"
            style={{
              border: '1.5px solid var(--color-gray-3)', background: '#fff',
              cursor: 'pointer', color: 'var(--color-gray-7)',
            }}
          >
            Отмена
          </button>
          <button
            type="submit"
            disabled={saving}
            className="btn-primary"
            style={{ padding: '9px 20px', borderRadius: 8, fontSize: 14, fontWeight: 500 }}
          >
            {saving ? 'Сохранение...' : isEdit ? 'Сохранить' : 'Создать'}
          </button>
        </FormActions>
      </form>
    </Modal>
  );
}
