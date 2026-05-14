import { useState, useEffect } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import toast from 'react-hot-toast';
import { api } from '../../lib/api';
import type { Employee, Department } from '../../types';
import { employeeSchema, type EmployeeFormData } from '../../validation/schemas';
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

  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { errors },
  } = useForm<EmployeeFormData>({
    resolver: zodResolver(employeeSchema),
    defaultValues: {
      user: String(initial?.user ?? ''),
      department: String(initial?.department ?? ''),
      role: initial?.role ?? 'worker',
      phone: initial?.phone ?? '',
      is_active: initial?.is_active ?? true,
      hire_date: initial?.hire_date ?? new Date().toISOString().slice(0, 10),
    },
  });

  useEffect(() => {
    if (!open) return;
    reset({
      user: String(initial?.user ?? ''),
      department: String(initial?.department ?? ''),
      role: initial?.role ?? 'worker',
      phone: initial?.phone ?? '',
      is_active: initial?.is_active ?? true,
      hire_date: initial?.hire_date ?? new Date().toISOString().slice(0, 10),
    });
    api.departments.list().then(r => setDepartments(r.results)).catch(() => {});
  }, [open, initial, reset]);

  async function onSubmit(data: EmployeeFormData) {
    setSaving(true);
    try {
      const payload = {
        user: Number(data.user),
        department: Number(data.department),
        role: data.role,
        phone: data.phone || null,
        is_active: data.is_active,
        hire_date: data.hire_date,
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
      <form onSubmit={handleSubmit(onSubmit)}>
        <Field
          label="ID пользователя"
          required={!isEdit}
          type="number"
          min="1"
          {...register('user')}
          placeholder="ID существующего пользователя"
          hint="Введите ID пользователя из системы"
          error={errors.user?.message}
        />

        <Controller
          name="department"
          control={control}
          render={({ field }) => (
            <SelectField
              label="Отдел"
              required
              {...field}
              options={deptOptions}
              placeholder="Выберите отдел"
              error={errors.department?.message}
            />
          )}
        />

        <FormRow>
          <Controller
            name="role"
            control={control}
            render={({ field }) => (
              <SelectField
                label="Роль"
                required
                {...field}
                options={ROLE_OPTIONS}
                error={errors.role?.message}
              />
            )}
          />
          <Field
            label="Телефон"
            type="tel"
            {...register('phone')}
            placeholder="+90 555 000 00 00"
            error={errors.phone?.message}
          />
        </FormRow>

        <Field
          label="Дата приёма"
          required
          type="date"
          {...register('hire_date')}
          error={errors.hire_date?.message}
        />

        <Controller
          name="is_active"
          control={control}
          render={({ field }) => (
            <CheckboxField
              label="Активен"
              checked={field.value}
              onChange={e => field.onChange(e.target.checked)}
            />
          )}
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
