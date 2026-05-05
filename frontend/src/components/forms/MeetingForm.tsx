import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { api } from '../../lib/api';
import type { Meeting, Building } from '../../types';
import { Modal } from '../ui/Modal';
import { Field, SelectField, TextareaField, FormRow, FormActions } from '../ui/FormField';

interface Props {
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
  initial?: Meeting;
}

export function MeetingForm({ open, onClose, onSaved, initial }: Props) {
  const isEdit = !!initial;
  const [saving, setSaving] = useState(false);
  const [buildings, setBuildings] = useState<Building[]>([]);

  const [form, setForm] = useState({
    building: String(initial?.building ?? ''),
    title: initial?.title ?? '',
    description: initial?.description ?? '',
    scheduled_date: initial?.scheduled_date
      ? initial.scheduled_date.slice(0, 16)
      : '',
    quorum_required: String(initial?.quorum_required ?? 50),
  });

  useEffect(() => {
    if (!open) return;
    api.buildings.list().then(r => setBuildings(r.results)).catch(() => {});
  }, [open]);

  useEffect(() => {
    if (open && initial) {
      setForm({
        building: String(initial.building),
        title: initial.title,
        description: initial.description ?? '',
        scheduled_date: initial.scheduled_date?.slice(0, 16) ?? '',
        quorum_required: String(initial.quorum_required ?? 50),
      });
    } else if (open && !initial) {
      setForm({ building: '', title: '', description: '', scheduled_date: '', quorum_required: '50' });
    }
  }, [open, initial]);

  const set = (field: keyof typeof form) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
      setForm(f => ({ ...f, [field]: e.target.value }));

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = {
        building: Number(form.building),
        title: form.title,
        description: form.description,
        scheduled_date: form.scheduled_date,
        quorum_required: Number(form.quorum_required),
      };
      if (isEdit) {
        await api.meetings.update(initial!.id, payload);
        toast.success('Собрание обновлено');
      } else {
        await api.meetings.create(payload);
        toast.success('Собрание создано');
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
    <Modal
      open={open}
      onClose={onClose}
      title={isEdit ? 'Редактировать собрание' : 'Новое собрание'}
      width={540}
    >
      <form onSubmit={submit}>
        <SelectField
          label="Здание"
          required
          value={form.building}
          onChange={set('building')}
          options={buildingOptions}
          placeholder="Выберите здание"
        />
        <Field
          label="Название"
          required
          value={form.title}
          onChange={set('title')}
          placeholder="Годовое общее собрание"
        />
        <FormRow>
          <Field
            label="Дата и время"
            required
            type="datetime-local"
            value={form.scheduled_date}
            onChange={set('scheduled_date')}
          />
          <Field
            label="Кворум (%)"
            required
            type="number"
            value={form.quorum_required}
            onChange={set('quorum_required')}
            placeholder="50"
          />
        </FormRow>
        <TextareaField
          label="Описание / повестка"
          value={form.description}
          onChange={set('description')}
          placeholder="Обсуждение бюджета, выборы председателя..."
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
