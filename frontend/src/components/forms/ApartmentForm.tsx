import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { api } from '../../lib/api';
import type { Apartment, Building } from '../../types';
import { Modal } from '../ui/Modal';
import { Field, SelectField, FormActions, FormRow } from '../ui/FormField';

interface Props {
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
  initial?: Apartment;
  defaultBuildingId?: number;
}

const STATUS_OPTIONS = [
  { value: 'active', label: 'Активна' },
  { value: 'inactive', label: 'Неактивна' },
  { value: 'pending_handover', label: 'Ожидает сдачи' },
];

export function ApartmentForm({ open, onClose, onSaved, initial, defaultBuildingId }: Props) {
  const isEdit = !!initial;
  const [saving, setSaving] = useState(false);
  const [buildings, setBuildings] = useState<Building[]>([]);

  const [form, setForm] = useState({
    building: String(initial?.building ?? defaultBuildingId ?? ''),
    apartment_number: initial?.apartment_number ?? '',
    floor: String(initial?.floor ?? ''),
    block: initial?.block ?? '',
    square_meters: initial?.square_meters ?? '',
    share_ratio_num: String(initial?.share_ratio_num ?? '1'),
    share_ratio_denom: String(initial?.share_ratio_denom ?? '1'),
    tapu_number: initial?.tapu_number ?? '',
    status: initial?.status ?? 'active',
  });

  useEffect(() => {
    if (!open) return;
    api.buildings.list().then(r => setBuildings(r.results)).catch(() => {});
  }, [open]);

  const set = (field: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm(f => ({ ...f, [field]: e.target.value }));

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = {
        building: Number(form.building),
        apartment_number: form.apartment_number,
        floor: form.floor ? Number(form.floor) : null,
        block: form.block || null,
        square_meters: form.square_meters || null,
        share_ratio_num: Number(form.share_ratio_num),
        share_ratio_denom: Number(form.share_ratio_denom),
        tapu_number: form.tapu_number || null,
        status: form.status,
      };
      if (isEdit) {
        await api.apartments.update(initial!.id, payload);
        toast.success('Квартира обновлена');
      } else {
        await api.apartments.create(payload);
        toast.success('Квартира добавлена');
      }
      onSaved();
      onClose();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Ошибка');
    } finally {
      setSaving(false);
    }
  }

  const buildingOptions = buildings.map(b => ({ value: b.id, label: b.name }));

  return (
    <Modal open={open} onClose={onClose} title={isEdit ? 'Редактировать квартиру' : 'Новая квартира'}>
      <form onSubmit={submit}>
        <SelectField
          label="Здание"
          required
          value={form.building}
          onChange={set('building')}
          options={buildingOptions}
          placeholder="Выберите здание"
        />
        <FormRow>
          <Field label="Номер квартиры" required value={form.apartment_number} onChange={set('apartment_number')} placeholder="42" />
          <Field label="Этаж" type="number" value={form.floor} onChange={set('floor')} placeholder="5" />
        </FormRow>
        <FormRow>
          <Field label="Блок / секция" value={form.block} onChange={set('block')} placeholder="A" />
          <Field label="Площадь (м²)" type="number" min="0" step="0.01" value={form.square_meters} onChange={set('square_meters')} placeholder="85.5" />
        </FormRow>
        <FormRow>
          <Field label="Доля (числитель)" required type="number" min="1" value={form.share_ratio_num} onChange={set('share_ratio_num')} />
          <Field label="Доля (знаменатель)" required type="number" min="1" value={form.share_ratio_denom} onChange={set('share_ratio_denom')} />
        </FormRow>
        <Field label="Номер тапу" value={form.tapu_number} onChange={set('tapu_number')} placeholder="12345678" />
        <SelectField
          label="Статус"
          required
          value={form.status}
          onChange={set('status')}
          options={STATUS_OPTIONS}
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
