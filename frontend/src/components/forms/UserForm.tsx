import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { api } from '../../lib/api';
import type { User } from '../../types';
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

export function UserForm({ open, onClose, onSaved, initial }: Props) {
  const isEdit = !!initial;
  const [saving, setSaving] = useState(false);

  const [form, setForm] = useState({
    username:   initial?.username ?? '',
    email:      initial?.email ?? '',
    first_name: initial?.first_name ?? '',
    last_name:  initial?.last_name ?? '',
    role:       initial?.role ?? 'worker',
    phone:      initial?.phone ?? '',
    password:   '',
    is_active:  String(initial?.is_active ?? true),
  });

  useEffect(() => {
    if (open && initial) {
      setForm({
        username:   initial.username,
        email:      initial.email,
        first_name: initial.first_name,
        last_name:  initial.last_name,
        role:       initial.role,
        phone:      initial.phone ?? '',
        password:   '',
        is_active:  String(initial.is_active),
      });
    } else if (open && !initial) {
      setForm({ username: '', email: '', first_name: '', last_name: '', role: 'worker', phone: '', password: '', is_active: 'true' });
    }
  }, [open, initial]);

  const set = (field: keyof typeof form) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
      setForm(f => ({ ...f, [field]: e.target.value }));

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!isEdit && form.password.length < 8) {
      toast.error('Пароль должен быть не менее 8 символов');
      return;
    }
    setSaving(true);
    try {
      const payload: Record<string, unknown> = {
        username:   form.username,
        email:      form.email,
        first_name: form.first_name,
        last_name:  form.last_name,
        role:       form.role,
        phone:      form.phone || null,
      };
      if (!isEdit) payload.password = form.password;
      if (isEdit)  payload.is_active = form.is_active === 'true';

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
      <form onSubmit={submit}>
        <FormRow>
          <Field label="Имя" value={form.first_name} onChange={set('first_name')} placeholder="Иван" />
          <Field label="Фамилия" value={form.last_name} onChange={set('last_name')} placeholder="Иванов" />
        </FormRow>
        <Field
          label="Логин"
          required
          value={form.username}
          onChange={set('username')}
          placeholder="ivan_ivanov"
        />
        <Field
          label="Email"
          type="email"
          value={form.email}
          onChange={set('email')}
          placeholder="ivan@example.com"
        />
        <FormRow>
          <SelectField
            label="Роль"
            required
            value={form.role}
            onChange={set('role')}
            options={ROLE_OPTIONS}
          />
          <Field
            label="Телефон"
            value={form.phone}
            onChange={set('phone')}
            placeholder="+7 999 123-45-67"
          />
        </FormRow>
        {!isEdit && (
          <Field
            label="Пароль"
            required
            type="password"
            value={form.password}
            onChange={set('password')}
            placeholder="Минимум 8 символов"
          />
        )}
        {isEdit && (
          <SelectField
            label="Статус"
            value={form.is_active}
            onChange={set('is_active')}
            options={[
              { value: 'true',  label: 'Активен' },
              { value: 'false', label: 'Деактивирован' },
            ]}
          />
        )}
        <FormActions>
          <button
            type="button"
            onClick={onClose}
            style={{
              padding: '9px 20px', borderRadius: 8, fontSize: 14, fontWeight: 500,
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
