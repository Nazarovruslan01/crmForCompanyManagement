import { useState, useEffect } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import toast from 'react-hot-toast';
import { api } from '../../lib/api';
import type { Task, Employee } from '../../types';
import { taskSchema, type TaskFormData } from '../../validation/schemas';
import { Modal } from '../ui/Modal';
import { Field, SelectField, TextareaField, FormRow, FormActions } from '../ui/FormField';

interface Props {
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
  initial?: Task;
}

const STATUS_OPTIONS = [
  { value: 'open', label: 'Открыта' },
  { value: 'in_progress', label: 'В работе' },
  { value: 'completed', label: 'Завершена' },
  { value: 'cancelled', label: 'Отменена' },
];

export function TaskForm({ open, onClose, onSaved, initial }: Props) {
  const isEdit = !!initial;
  const [saving, setSaving] = useState(false);
  const [employees, setEmployees] = useState<Employee[]>([]);

  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { errors },
  } = useForm<TaskFormData>({
    resolver: zodResolver(taskSchema),
    defaultValues: {
      title: initial?.title ?? '',
      description: initial?.description ?? '',
      assigned_to: String(initial?.assigned_to ?? ''),
      status: initial?.status ?? 'open',
      due_date: initial?.due_date ?? new Date().toISOString().slice(0, 10),
      ticket: initial?.ticket ? String(initial.ticket) : '',
    },
  });

  useEffect(() => {
    if (!open) return;
    reset({
      title: initial?.title ?? '',
      description: initial?.description ?? '',
      assigned_to: String(initial?.assigned_to ?? ''),
      status: initial?.status ?? 'open',
      due_date: initial?.due_date ?? new Date().toISOString().slice(0, 10),
      ticket: initial?.ticket ? String(initial.ticket) : '',
    });
    api.employees.list().then(r => setEmployees(r.results)).catch(() => {});
  }, [open, initial, reset]);

  async function onSubmit(data: TaskFormData) {
    setSaving(true);
    try {
      const payload = {
        title: data.title,
        description: data.description || null,
        assigned_to: Number(data.assigned_to),
        status: data.status,
        due_date: data.due_date,
        ticket: data.ticket ? Number(data.ticket) : null,
      };
      if (isEdit) {
        await api.tasks.update(initial!.id, payload);
        toast.success('Задача обновлена');
      } else {
        await api.tasks.create(payload);
        toast.success('Задача добавлена');
      }
      onSaved();
      onClose();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Ошибка');
    } finally {
      setSaving(false);
    }
  }

  const employeeOptions = employees.map(e => ({ value: e.id, label: e.user_display }));

  return (
    <Modal open={open} onClose={onClose} title={isEdit ? 'Редактировать задачу' : 'Новая задача'}>
      <form onSubmit={handleSubmit(onSubmit)}>
        <Field
          label="Название"
          required
          {...register('title')}
          placeholder="Название задачи"
          error={errors.title?.message}
        />

        <TextareaField
          label="Описание"
          {...register('description')}
          placeholder="Описание задачи"
          error={errors.description?.message}
        />

        <FormRow>
          <Controller
            name="assigned_to"
            control={control}
            render={({ field }) => (
              <SelectField
                label="Ответственный"
                required
                {...field}
                options={employeeOptions}
                placeholder="Выберите сотрудника"
                error={errors.assigned_to?.message}
              />
            )}
          />
          <Controller
            name="status"
            control={control}
            render={({ field }) => (
              <SelectField
                label="Статус"
                required
                {...field}
                options={STATUS_OPTIONS}
                error={errors.status?.message}
              />
            )}
          />
        </FormRow>

        <Field
          label="Срок"
          required
          type="date"
          {...register('due_date')}
          error={errors.due_date?.message}
        />

        <Field
          label="ID заявки (опционально)"
          type="number"
          {...register('ticket')}
          placeholder="Связанная заявка"
          error={errors.ticket?.message}
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
