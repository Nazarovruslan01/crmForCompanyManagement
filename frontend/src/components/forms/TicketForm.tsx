import { useState, useEffect } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import toast from 'react-hot-toast';
import { api } from '../../lib/api';
import type { Ticket, Apartment, Employee } from '../../types';
import { TICKET_CATEGORY_OPTIONS, TICKET_PRIORITY_OPTIONS, TICKET_STATUS_OPTIONS } from '../../constants/options';
import { ticketSchema, type TicketFormData } from '../../validation/schemas';
import { Modal } from '../ui/Modal';
import { Field, SelectField, TextareaField, FormRow, FormActions } from '../ui/FormField';

interface Props {
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
  initial?: Ticket;
}

export function TicketForm({ open, onClose, onSaved, initial }: Props) {
  const isEdit = !!initial;
  const [saving, setSaving] = useState(false);
  const [apartments, setApartments] = useState<Apartment[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);

  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { errors },
  } = useForm<TicketFormData>({
    resolver: zodResolver(ticketSchema),
    defaultValues: {
      apartment: String(initial?.apartment ?? ''),
      category: initial?.category ?? 'general',
      priority: initial?.priority ?? 'medium',
      status: initial?.status ?? 'new',
      title: initial?.title ?? '',
      description: initial?.description ?? '',
      assigned_worker: String(initial?.assigned_worker ?? ''),
    },
  });

  useEffect(() => {
    if (!open) return;
    reset({
      apartment: String(initial?.apartment ?? ''),
      category: initial?.category ?? 'general',
      priority: initial?.priority ?? 'medium',
      status: initial?.status ?? 'new',
      title: initial?.title ?? '',
      description: initial?.description ?? '',
      assigned_worker: String(initial?.assigned_worker ?? ''),
    });
    Promise.all([
      api.apartments.list().then(r => setApartments(r.results)),
      api.employees.list().then(r => setEmployees(r.results)),
    ]).catch(() => {});
  }, [open, initial, reset]);

  async function onSubmit(data: TicketFormData) {
    setSaving(true);
    try {
      const payload = {
        apartment: Number(data.apartment),
        category: data.category,
        priority: data.priority,
        status: data.status || 'new',
        title: data.title,
        description: data.description,
        assigned_worker: data.assigned_worker ? Number(data.assigned_worker) : null,
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
      <form onSubmit={handleSubmit(onSubmit)}>
        <Controller
          name="apartment"
          control={control}
          render={({ field }) => (
            <SelectField
              label="Квартира"
              required
              {...field}
              options={apartmentOptions}
              placeholder="Выберите квартиру"
              error={errors.apartment?.message}
            />
          )}
        />

        <Field
          label="Заголовок"
          required
          {...register('title')}
          placeholder="Течёт кран в ванной"
          error={errors.title?.message}
        />

        <FormRow>
          <Controller
            name="category"
            control={control}
            render={({ field }) => (
              <SelectField
                label="Категория"
                required
                {...field}
                options={TICKET_CATEGORY_OPTIONS}
                error={errors.category?.message}
              />
            )}
          />
          <Controller
            name="priority"
            control={control}
            render={({ field }) => (
              <SelectField
                label="Приоритет"
                required
                {...field}
                options={TICKET_PRIORITY_OPTIONS}
                error={errors.priority?.message}
              />
            )}
          />
        </FormRow>

        {isEdit && (
          <Controller
            name="status"
            control={control}
            render={({ field }) => (
              <SelectField
                label="Статус"
                required
                {...field}
                options={TICKET_STATUS_OPTIONS}
                error={errors.status?.message}
              />
            )}
          />
        )}

        <Controller
          name="assigned_worker"
          control={control}
          render={({ field }) => (
            <SelectField
              label="Исполнитель"
              {...field}
              options={workerOptions}
              placeholder="Не назначен"
              error={errors.assigned_worker?.message}
            />
          )}
        />

        <TextareaField
          label="Описание"
          required
          {...register('description')}
          placeholder="Подробно опишите проблему..."
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
