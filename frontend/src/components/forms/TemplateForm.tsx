import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useState } from 'react';
import toast from 'react-hot-toast';
import { api } from '../../lib/api';
import type { NotificationTemplate } from '../../types';
import { notificationTemplateSchema, type NotificationTemplateFormData } from '../../validation/schemas';
import { Modal } from '../ui/Modal';
import { Field, SelectField, TextareaField, CheckboxField, FormActions } from '../ui/FormField';

const NOTIFICATION_TYPE_OPTIONS = [
  { value: 'aidat_reminder',       label: 'Напоминание о квартплате' },
  { value: 'aidat_overdue',        label: 'Просрочка квартплаты' },
  { value: 'payment_confirmation', label: 'Подтверждение платежа' },
  { value: 'ticket_created',       label: 'Заявка создана' },
  { value: 'ticket_assigned',      label: 'Заявка назначена' },
  { value: 'ticket_resolved',      label: 'Заявка решена' },
  { value: 'meeting_reminder',     label: 'Напоминание о собрании' },
  { value: 'general',              label: 'Общее' },
];

const CHANNEL_OPTIONS = [
  { value: 'push',     label: 'Push-уведомление' },
  { value: 'sms',      label: 'SMS' },
  { value: 'email',    label: 'Email' },
  { value: 'telegram', label: 'Telegram' },
];

interface Props {
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
  initial?: NotificationTemplate;
}

export function TemplateForm({ open, onClose, onSaved, initial }: Props) {
  const isEdit = !!initial;
  const [saving, setSaving] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<NotificationTemplateFormData>({
    resolver: zodResolver(notificationTemplateSchema),
    defaultValues: {
      name: initial?.name ?? '',
      notification_type: initial?.notification_type ?? '',
      channel: initial?.channel ?? '',
      subject: initial?.subject ?? '',
      body_template: initial?.body_template ?? '',
      is_active: initial?.is_active ?? true,
    },
  });

  useEffect(() => {
    if (!open) return;
    reset({
      name: initial?.name ?? '',
      notification_type: initial?.notification_type ?? '',
      channel: initial?.channel ?? '',
      subject: initial?.subject ?? '',
      body_template: initial?.body_template ?? '',
      is_active: initial?.is_active ?? true,
    });
  }, [open, initial, reset]);

  async function onSubmit(data: NotificationTemplateFormData) {
    setSaving(true);
    try {
      if (isEdit) {
        await api.notificationTemplates.update(initial!.id, data);
        toast.success('Шаблон обновлён');
      } else {
        await api.notificationTemplates.create(data);
        toast.success('Шаблон создан');
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
    <Modal open={open} onClose={onClose} title={isEdit ? 'Редактировать шаблон' : 'Новый шаблон'}>
      <form onSubmit={handleSubmit(onSubmit)}>
        <Field
          label="Название"
          required
          {...register('name')}
          placeholder="Например: Напоминание об оплате"
          error={errors.name?.message}
        />

        <SelectField
          label="Тип уведомления"
          required
          {...register('notification_type')}
          options={NOTIFICATION_TYPE_OPTIONS}
          placeholder="Выберите тип"
          error={errors.notification_type?.message}
        />

        <SelectField
          label="Канал отправки"
          required
          {...register('channel')}
          options={CHANNEL_OPTIONS}
          placeholder="Выберите канал"
          error={errors.channel?.message}
        />

        <Field
          label="Тема письма"
          {...register('subject')}
          placeholder="Заполните для Email-канала"
          error={errors.subject?.message}
        />

        <TextareaField
          label="Шаблон сообщения"
          required
          {...register('body_template')}
          rows={5}
          placeholder="Используйте {name}, {apartment}, {amount} для подстановки"
          hint="Доступные переменные: {name}, {apartment}, {amount}, {due_date}"
          error={errors.body_template?.message}
        />

        <CheckboxField
          label="Активен"
          hint="Неактивные шаблоны не используются при отправке уведомлений"
          {...register('is_active')}
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
