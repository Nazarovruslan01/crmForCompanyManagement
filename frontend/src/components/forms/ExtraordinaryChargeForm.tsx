import { useState, useEffect } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import toast from 'react-hot-toast';
import { api } from '../../lib/api';
import type { ExtraordinaryCharge, Building } from '../../types';
import { extraordinaryChargeSchema, type ExtraordinaryChargeFormData } from '../../validation/schemas';
import { Modal } from '../ui/Modal';
import { Field, SelectField, TextareaField, FormRow, FormActions } from '../ui/FormField';

interface Props {
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
  initial?: ExtraordinaryCharge;
}

const STATUS_OPTIONS = [
  { value: 'proposed', label: 'Предложено' },
  { value: 'approved', label: 'Одобрено' },
  { value: 'rejected', label: 'Отклонено' },
  { value: 'collecting', label: 'Сбор' },
  { value: 'collected', label: 'Собрано' },
];

export function ExtraordinaryChargeForm({ open, onClose, onSaved, initial }: Props) {
  const isEdit = !!initial;
  const [saving, setSaving] = useState(false);
  const [buildings, setBuildings] = useState<Building[]>([]);

  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { errors },
  } = useForm<ExtraordinaryChargeFormData>({
    resolver: zodResolver(extraordinaryChargeSchema),
    defaultValues: {
      building: String(initial?.building ?? ''),
      description: initial?.description ?? '',
      total_amount: initial?.total_amount ?? '',
      assembly_resolution_number: initial?.assembly_resolution_number ?? '',
      approval_date: initial?.approval_date ?? '',
      status: initial?.status ?? 'proposed',
      due_date: initial?.due_date ?? '',
    },
  });

  useEffect(() => {
    if (!open) return;
    reset({
      building: String(initial?.building ?? ''),
      description: initial?.description ?? '',
      total_amount: initial?.total_amount ?? '',
      assembly_resolution_number: initial?.assembly_resolution_number ?? '',
      approval_date: initial?.approval_date ?? '',
      status: initial?.status ?? 'proposed',
      due_date: initial?.due_date ?? '',
    });
    api.buildings.list().then(r => setBuildings(r.results)).catch(() => {});
  }, [open, initial, reset]);

  async function onSubmit(data: ExtraordinaryChargeFormData) {
    setSaving(true);
    try {
      const payload = {
        building: Number(data.building),
        description: data.description,
        total_amount: data.total_amount,
        assembly_resolution_number: data.assembly_resolution_number || null,
        approval_date: data.approval_date || null,
        status: data.status,
        due_date: data.due_date || null,
      };
      if (isEdit) {
        await api.extraordinaryCharges.update(initial!.id, payload);
        toast.success('Начисление обновлено');
      } else {
        await api.extraordinaryCharges.create(payload);
        toast.success('Начисление добавлено');
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
    <Modal open={open} onClose={onClose} title={isEdit ? 'Редактировать начисление' : 'Новое начисление'}>
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

        <TextareaField
          label="Описание"
          required
          {...register('description')}
          placeholder="Например: Ремонт лифта"
          error={errors.description?.message}
        />

        <FormRow>
          <Field
            label="Общая сумма"
            required
            type="number"
            step="0.01"
            {...register('total_amount')}
            placeholder="0.00"
            error={errors.total_amount?.message}
          />
          <Field
            label="Дата платежа"
            type="date"
            {...register('due_date')}
            error={errors.due_date?.message}
          />
        </FormRow>

        <FormRow>
          <Field
            label="Номер резолюции"
            {...register('assembly_resolution_number')}
            placeholder="Например: РВ-2024-001"
            error={errors.assembly_resolution_number?.message}
          />
          <Field
            label="Дата одобрения"
            type="date"
            {...register('approval_date')}
            error={errors.approval_date?.message}
          />
        </FormRow>

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
