import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { api } from '../../lib/api';
import type { Ticket, Apartment, Employee } from '../../types';
import { Modal } from '../ui/Modal';
import { Field, SelectField, TextareaField, FormRow, FormActions } from '../ui/FormField';

interface Props {
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
  initial?: Ticket;
}

const CATEGORY_OPTIONS = [
  { value: 'plumbing', label: 'Сантехника' },
  { value: 'electrical', label: 'Электрика' },
  { value: 'cleaning', label: 'Уборка' },
  { value: 'security', label: 'Безопасность' },
  { value: 'noise', label: 'Шум' },
  { value: 'general', label: 'Общее' },
];

const PRIORITY_OPTIONS = [
  { value: 'low', label: 'Низкий' },
  { value: 'medium', label: 'Средний' },
  { value: 'high', label: 'Высокий' },
  { value: 'urgent', label: 'Срочный' },
];

const STATUS_OPTIONS = [
  { value: 'new', label: 'Новая' },
  { value: 'assigned', label: 'Назначена' },
  { value: 'in_progress', label: 'В работе' },
  { value: 'resolved', label: 'Решена' },
  { value: 'closed', label: 'Закрыта' },
];

export function TicketForm({ open, onClose, onSaved, initial }: Props) {
  const isEdit = !!initial;
  const [saving, setSaving] = useState(false);
  const [apartments, setApartments] = useState<Apartment[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);

  const [form, setForm] = useState({
    apartment: String(initial?.apartment ?? ''),
    category: initial?.category ?? 'general',
    priority: initial?.priority ?? 'medium',
    status: initial?.status ?? 'new',
    title: initial?.title ?? '',
    description: initial?.description ?? '',
    assigned_worker: String(initial?.assigned_worker ?? ''),
  });

  useEffect(() => {
    if (!open) return;
    Promise.all([
      api.apartments.list().then(r => setApartments(r.results)),
      api.employees.list().then(r => setEmployees(r.results)),
    ]).catch(() => {});
  }, [open]);

  const set = (field: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setForm(f => ({ ...f, [field]: e.target.value }));

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = {
        apartment: Number(form.apartment),
        category: form.category,
        priority: form.priority,
        status: form.status,
        title: form.title,
        description: form.description,
        assigned_worker: form.assigned_worker ? Number(form.assigned_worker) : null,
      };
      if (isEdit) {
        await api.tickets.update(initial!.id, payload);
        toast.success('Заявка обновлена');
      } else {
        await api.tickets.create(payload);
        toast.success('Заявка создана');
      }
      onSaved();
      onClose();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Ошибка');
    } finally {
      setSaving(false);
    }
  }

  const apartmentOptions = apartments.map(a => ({
    value: a.id,
    label: `${a.building_display} — кв. ${a.apartment_number}${a.block ? ` (блок ${a.block})` : ''}`,
  }));

  const workerOptions = employees.map(e => ({
    value: e.user,
    label: e.user_display,
  }));

  return (
    <Modal open={open} onClose={onClose} title={isEdit ? 'Редактировать заявку' : 'Новая заявка'} width={580}>
      <form onSubmit={submit}>
        <SelectField
          label="Квартира"
          required
          value={form.apartment}
          onChange={set('apartment')}
          options={apartmentOptions}
          placeholder="Выберите квартиру"
        />
        <Field label="Заголовок" required value={form.title} onChange={set('title')} placeholder="Течёт кран в ванной" />
        <FormRow>
          <SelectField
            label="Категория"
            required
            value={form.category}
            onChange={set('category')}
            options={CATEGORY_OPTIONS}
          />
          <SelectField
            label="Приоритет"
            required
            value={form.priority}
            onChange={set('priority')}
            options={PRIORITY_OPTIONS}
          />
        </FormRow>
        {isEdit && (
          <SelectField
            label="Статус"
            required
            value={form.status}
            onChange={set('status')}
            options={STATUS_OPTIONS}
          />
        )}
        <SelectField
          label="Исполнитель"
          value={form.assigned_worker}
          onChange={set('assigned_worker')}
          options={workerOptions}
          placeholder="Не назначен"
        />
        <TextareaField
          label="Описание"
          required
          value={form.description}
          onChange={set('description')}
          placeholder="Подробно опишите проблему..."
          rows={4}
        />
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
