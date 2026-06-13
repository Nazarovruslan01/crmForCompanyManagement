import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import toast from 'react-hot-toast';
import { api } from '../../lib/api';
import type { AgendaItem } from '../../types';
import { agendaItemSchema, type AgendaItemFormData } from '../../validation/schemas';
import { Modal } from '../ui/Modal';
import { Field, TextareaField, FormActions } from '../ui/FormField';

interface Props {
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
  meetingId: number;
  initial?: AgendaItem;
}

export function AgendaItemForm({ open, onClose, onSaved, meetingId, initial }: Props) {
  const isEdit = !!initial;
  const [saving, setSaving] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<AgendaItemFormData>({
    resolver: zodResolver(agendaItemSchema),
    defaultValues: {
      title: initial?.title ?? '',
      description: initial?.description ?? '',
      order: initial?.order ? String(initial.order) : '',
    },
  });

  useEffect(() => {
    if (!open) return;
    reset({
      title: initial?.title ?? '',
      description: initial?.description ?? '',
      order: initial?.order ? String(initial.order) : '',
    });
  }, [open, initial, reset]);

  async function onSubmit(data: AgendaItemFormData) {
    setSaving(true);
    try {
      const payload = {
        meeting: meetingId,
        title: data.title,
        description: data.description || '',
        order: data.order ? Number(data.order) : 0,
      };
      if (isEdit) {
        await api.agendaItems.update(initial!.id, payload);
        toast.success('Пункт повестки обновлён');
      } else {
        await api.agendaItems.create(payload);
        toast.success('Пункт повестки добавлен');
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
    <Modal open={open} onClose={onClose} title={isEdit ? 'Редактировать пункт' : 'Новый пункт повестки'}>
      <form onSubmit={handleSubmit(onSubmit)}>
        <Field
          label="Название"
          required
          {...register('title')}
          placeholder="Название пункта повестки"
          error={errors.title?.message}
        />

        <TextareaField
          label="Описание"
          {...register('description')}
          placeholder="Описание пункта"
          error={errors.description?.message}
        />

        <Field
          label="Порядок"
          type="number"
          min="1"
          {...register('order')}
          placeholder="Порядковый номер"
          error={errors.order?.message}
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
