import { useState } from 'react';
import toast from 'react-hot-toast';
import { api } from '../../lib/api';
import type { Building } from '../../types';
import { Modal } from '../ui/Modal';
import { Field, SelectField, FormActions } from '../ui/FormField';

interface Props {
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
  initial?: Building;
}

const MANAGEMENT_TYPES = [
  { value: 'self_managed', label: 'Самоуправление' },
  { value: 'external_company', label: 'Управляющая компания' },
];

export function BuildingForm({ open, onClose, onSaved, initial }: Props) {
  const isEdit = !!initial;
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    name: initial?.name ?? '',
    address: initial?.address ?? '',
    city: initial?.city ?? '',
    district: initial?.district ?? '',
    management_type: initial?.management_type ?? 'self_managed',
    annual_budget: initial?.annual_budget ?? '',
  });

  const set = (field: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm(f => ({ ...f, [field]: e.target.value }));

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = {
        name: form.name,
        address: form.address,
        city: form.city,
        district: form.district,
        management_type: form.management_type,
        annual_budget: form.annual_budget || null,
      };
      if (isEdit) {
        await api.buildings.update(initial!.id, payload);
        toast.success('Здание обновлено');
      } else {
        await api.buildings.create(payload);
        toast.success('Здание добавлено');
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
    <Modal open={open} onClose={onClose} title={isEdit ? 'Редактировать здание' : 'Новое здание'}>
      <form onSubmit={submit}>
        <Field label="Название" required value={form.name} onChange={set('name')} placeholder="ЖК Центральный" />
        <Field label="Адрес" required value={form.address} onChange={set('address')} placeholder="ул. Ататюрка, 12" />
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 16px' }}>
          <Field label="Город" required value={form.city} onChange={set('city')} placeholder="Стамбул" />
          <Field label="Район" required value={form.district} onChange={set('district')} placeholder="Кадыкёй" />
        </div>
        <SelectField
          label="Тип управления"
          required
          value={form.management_type}
          onChange={set('management_type')}
          options={MANAGEMENT_TYPES}
        />
        <Field
          label="Годовой бюджет (₺)"
          type="number"
          min="0"
          step="0.01"
          value={form.annual_budget}
          onChange={set('annual_budget')}
          placeholder="1000000"
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
