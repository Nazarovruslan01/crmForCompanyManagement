import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import toast from 'react-hot-toast';
import { api } from '../../lib/api';
import type { MeetingProtocol } from '../../types';
import { protocolSchema, type ProtocolFormData } from '../../validation/schemas';
import { Modal } from '../ui/Modal';
import { TextareaField, FormActions } from '../ui/FormField';

interface Props {
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
  meetingId: number;
  initial?: MeetingProtocol;
}

export function MeetingProtocolForm({ open, onClose, onSaved, meetingId, initial }: Props) {
  const isEdit = !!initial;
  const [saving, setSaving] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ProtocolFormData>({
    resolver: zodResolver(protocolSchema),
    defaultValues: {
      content: initial?.content ?? '',
    },
  });

  useEffect(() => {
    if (!open) return;
    reset({
      content: initial?.content ?? '',
    });
  }, [open, initial, reset]);

  async function onSubmit(data: ProtocolFormData) {
    setSaving(true);
    try {
      const payload = {
        meeting: meetingId,
        content: data.content,
      };
      if (isEdit) {
        await api.protocols.update(initial!.id, payload);
        toast.success('Протокол обновлён');
      } else {
        await api.protocols.create(payload);
        toast.success('Протокол создан');
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
    <Modal open={open} onClose={onClose} title={isEdit ? 'Редактировать протокол' : 'Новый протокол'} width={620}>
      <form onSubmit={handleSubmit(onSubmit)}>
        <TextareaField
          label="Текст протокола"
          required
          {...register('content')}
          placeholder="Содержание протокола собрания..."
          error={errors.content?.message}
          rows={10}
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
