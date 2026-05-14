import { useState, useEffect } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import toast from 'react-hot-toast';
import { api } from '../../lib/api';
import type { Meeting, Building } from '../../types';
import { meetingSchema, type MeetingFormData } from '../../validation/schemas';
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

  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { errors },
  } = useForm<MeetingFormData>({
    resolver: zodResolver(meetingSchema),
    defaultValues: {
      building: String(initial?.building ?? ''),
      title: initial?.title ?? '',
      description: initial?.description ?? '',
      scheduled_date: initial?.scheduled_date
        ? initial.scheduled_date.slice(0, 16)
        : '',
      quorum_required: String(initial?.quorum_required ?? 50),
    },
  });

  useEffect(() => {
    if (!open) return;
    reset({
      building: String(initial?.building ?? ''),
      title: initial?.title ?? '',
      description: initial?.description ?? '',
      scheduled_date: initial?.scheduled_date
        ? initial.scheduled_date.slice(0, 16)
        : '',
      quorum_required: String(initial?.quorum_required ?? 50),
    });
    api.buildings.list().then(r => setBuildings(r.results)).catch(() => {});
  }, [open, initial, reset]);

  async function onSubmit(data: MeetingFormData) {
    setSaving(true);
    try {
      const payload = {
        building: Number(data.building),
        title: data.title,
        description: data.description,
        scheduled_date: data.scheduled_date,
        quorum_required: Number(data.quorum_required),
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
      <form onSubmit={handleSubmit(onSubmit)}>
        <Controller
          name="building"
          control={control}
          render={({ field }) => (
            <SelectField
              label="Здание"
              required
              {...field}
              options={buildingOptions}
              placeholder="Выберите здание"
              error={errors.building?.message}
            />
          )}
        />
        <Field
          label="Название"
          required
          {...register('title')}
          placeholder="Годовое общее собрание"
          error={errors.title?.message}
        />
        <FormRow>
          <Field
            label="Дата и время"
            required
            type="datetime-local"
            {...register('scheduled_date')}
            error={errors.scheduled_date?.message}
          />
          <Field
            label="Кворум (%)"
            required
            type="number"
            {...register('quorum_required')}
            placeholder="50"
            error={errors.quorum_required?.message}
          />
        </FormRow>
        <TextareaField
          label="Описание / повестка"
          {...register('description')}
          placeholder="Обсуждение бюджета, выборы председателя..."
          rows={4}
          error={errors.description?.message}
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
