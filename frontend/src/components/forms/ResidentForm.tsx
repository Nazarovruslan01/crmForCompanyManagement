import { useState } from 'react';
import toast from 'react-hot-toast';
import { api } from '../../lib/api';
import type { Resident } from '../../types';
import { Modal } from '../ui/Modal';
import { Field, SelectField, CheckboxField, FormRow, FormActions } from '../ui/FormField';

interface Props {
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
  initial?: Resident;
}

const OWNER_TYPE_OPTIONS = [
  { value: 'owner', label: 'Собственник' },
  { value: 'tenant', label: 'Арендатор' },
  { value: 'family_member', label: 'Член семьи' },
  { value: 'other', label: 'Другое' },
];

export function ResidentForm({ open, onClose, onSaved, initial }: Props) {
  const isEdit = !!initial;
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    name: initial?.name ?? '',
    surname: initial?.surname ?? '',
    phone: initial?.phone ?? '',
    email: initial?.email ?? '',
    tc_kimlik_no: initial?.tc_kimlik_no ?? '',
    passport_no: initial?.passport_no ?? '',
    is_foreign_owner: initial?.is_foreign_owner ?? false,
    owner_type: initial?.owner_type ?? 'owner',
  });

  const set = (field: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm(f => ({ ...f, [field]: e.target.value }));

  const toggle = (field: 'is_foreign_owner') => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm(f => ({ ...f, [field]: e.target.checked }));

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = {
        name: form.name,
        surname: form.surname,
        phone: form.phone || null,
        email: form.email || null,
        tc_kimlik_no: form.is_foreign_owner ? null : (form.tc_kimlik_no || null),
        passport_no: form.is_foreign_owner ? (form.passport_no || null) : null,
        is_foreign_owner: form.is_foreign_owner,
        owner_type: form.owner_type,
      };
      if (isEdit) {
        await api.residents.update(initial!.id, payload);
        toast.success('Резидент обновлён');
      } else {
        await api.residents.create(payload);
        toast.success('Резидент добавлен');
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
    <Modal open={open} onClose={onClose} title={isEdit ? 'Редактировать резидента' : 'Новый резидент'}>
      <form onSubmit={submit}>
        <FormRow>
          <Field label="Имя" required value={form.name} onChange={set('name')} placeholder="Ahmet" />
          <Field label="Фамилия" required value={form.surname} onChange={set('surname')} placeholder="Yılmaz" />
        </FormRow>
        <FormRow>
          <Field label="Телефон" type="tel" value={form.phone} onChange={set('phone')} placeholder="+90 555 000 00 00" />
          <Field label="Email" type="email" value={form.email} onChange={set('email')} placeholder="ahmet@example.com" />
        </FormRow>
        <SelectField
          label="Тип владельца"
          required
          value={form.owner_type}
          onChange={set('owner_type')}
          options={OWNER_TYPE_OPTIONS}
        />
        <CheckboxField
          label="Иностранный владелец"
          checked={form.is_foreign_owner}
          onChange={toggle('is_foreign_owner')}
        />
        {form.is_foreign_owner ? (
          <Field label="Номер паспорта" value={form.passport_no} onChange={set('passport_no')} placeholder="AB1234567" />
        ) : (
          <Field
            label="ТС кимлик но"
            value={form.tc_kimlik_no}
            onChange={set('tc_kimlik_no')}
            placeholder="12345678901"
            maxLength={11}
            hint="11-значный идентификационный номер гражданина Турции"
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
