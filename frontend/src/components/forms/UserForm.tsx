import { useState, useEffect } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import toast from 'react-hot-toast';
import { api } from '../../lib/api';
import type { User } from '../../types';
import { userSchema, type UserFormData } from '../../validation/schemas';
import { Modal } from '../ui/Modal';
import { Field, SelectField, FormRow, FormActions } from '../ui/FormField';

interface Props {
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
  initial?: User;
}

const ROLE_OPTIONS = [
  { value: 'admin',    label: 'Администратор' },
  { value: 'manager',  label: 'Менеджер' },
  { value: 'worker',   label: 'Сотрудник' },
  { value: 'resident', label: 'Жилец' },
];

const STATUS_OPTIONS = [
  { value: 'true',  label: 'Активен' },
  { value: 'false', label: 'Деактивирован' },
];

export function UserForm({ open, onClose, onSaved, initial }: Props) {
  const isEdit = !!initial;
  const [saving, setSaving] = useState(false);

  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { errors },
  } = useForm<UserFormData>({
    resolver: zodResolver(userSchema),
    defaultValues: {
      username: initial?.username ?? '',
      email: initial?.email ?? '',
      first_name: initial?.first_name ?? '',
      last_name: initial?.last_name ?? '',
      role: initial?.role ?? 'worker',
      phone: initial?.phone ?? '',
      password: '',
    },
  });

  useEffect(() => {
    if (!open) return;
    reset({
      username: initial?.username ?? '',
      email: initial?.email ?? '',
      first_name: initial?.first_name ?? '',
      last_name: initial?.last_name ?? '',
      role: initial?.role ?? 'worker',
      phone: initial?.phone ?? '',
      password: '',
    });
  }, [open, initial, reset]);

  async function onSubmit(data: UserFormData) {
    setSaving(true);
    try {
      const payload: Record<string, unknown> = {
        username: data.username,
        email: data.email,
        first_name: data.first_name,
        last_name: data.last_name,
        role: data.role,
        phone: data.phone || null,
      };
      if (!isEdit) payload.password = data.password;
      if (isEdit) payload.is_active = data.is_active === 'true';

      if (isEdit) {
        await api.users.update(initial!.id, payload);
        toast.success('Пользователь обновлён');
      } else {
        await api.users.create(payload);
        toast.success('Пользователь создан');
      }
      onSaved();
      onClose();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Ошибка');
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={isEdit ? 'Редактировать пользователя' : 'Новый пользователь'}
      width={540}
    >
      <form onSubmit={handleSubmit(onSubmit)}>
        <FormRow>
          <Field
            label="Имя"
            {...register('first_name')}
            placeholder="Иван"
            error={errors.first_name?.message}
          />
          <Field
            label="Фамилия"
            {...register('last_name')}
            placeholder="Иванов"
            error={errors.last_name?.message}
          />
        </FormRow>

        <Field
          label="Логин"
          required
          {...register('username')}
          placeholder="ivan_ivanov"
          error={errors.username?.message}
        />

        <Field
          label="Email"
          type="email"
          {...register('email')}
          placeholder="ivan@example.com"
          error={errors.email?.message}
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
            {...register('phone')}
            placeholder="+7 999 123-45-67"
            error={errors.phone?.message}
          />
        </FormRow>

        {!isEdit && (
          <Field
            label="Пароль"
            required
            type="password"
            {...register('password')}
            placeholder="Минимум 8 символов"
            error={errors.password?.message}
          />
        )}

        {isEdit && (
          <Controller
            name="is_active"
            control={control}
            render={({ field }) => (
              <SelectField
                label="Статус"
                {...field}
                options={STATUS_OPTIONS}
                error={errors.is_active?.message}
              />
            )}
          />
        )}

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
