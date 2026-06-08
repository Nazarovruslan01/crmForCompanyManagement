import { useState, useEffect } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import toast from 'react-hot-toast';
import { api } from '../../lib/api';
import type { Building } from '../../types';
import { buildingSchema, type BuildingFormData } from '../../validation/schemas';
import { Modal } from '../ui/Modal';
import { Field, SelectField, FormActions } from '../ui/FormField';

interface Props {
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
  initial?: Building;
}

const MANAGEMENT_TYPES = [
  { value: 'self_managed', label: 'Самоуправление' },
  { value: 'external_company', label: 'Управляющая компания' },
];

export function BuildingForm({ open, onClose, onSaved, initial }: Props) {
  const isEdit = !!initial;
  const [saving, setSaving] = useState(false);

  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { errors },
  } = useForm<BuildingFormData>({
    resolver: zodResolver(buildingSchema),
    defaultValues: {
      name: initial?.name ?? '',
      address: initial?.address ?? '',
      city: initial?.city ?? '',
      district: initial?.district ?? '',
      management_type: initial?.management_type ?? 'self_managed',
      annual_budget: initial?.annual_budget ?? '',
    },
  });

  useEffect(() => {
    if (!open) return;
    reset({
      name: initial?.name ?? '',
      address: initial?.address ?? '',
      city: initial?.city ?? '',
      district: initial?.district ?? '',
      management_type: initial?.management_type ?? 'self_managed',
      annual_budget: initial?.annual_budget ?? '',
    });
  }, [open, initial, reset]);

  async function onSubmit(data: BuildingFormData) {
    setSaving(true);
    try {
      const payload = {
        name: data.name,
        address: data.address,
        city: data.city,
        district: data.district,
        management_type: data.management_type,
        annual_budget: data.annual_budget || null,
      };
      if (isEdit) {
        await api.buildings.update(initial!.id, payload);
        toast.success('Здание обновлено');
      } else {
        await api.buildings.create(payload);
        toast.success('Здание добавлено');
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
    <Modal open={open} onClose={onClose} title={isEdit ? 'Редактировать здание' : 'Новое здание'}>
      <form onSubmit={handleSubmit(onSubmit)}>
        <Field
          label="Название"
          required
          {...register('name')}
          placeholder="ЖК Центральный"
          error={errors.name?.message}
        />

        <Field
          label="Адрес"
          required
          {...register('address')}
          placeholder="ул. Ататюрка, 12"
          error={errors.address?.message}
        />

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 16px' }}>
          <Field
            label="Город"
            required
            {...register('city')}
            placeholder="Стамбул"
            error={errors.city?.message}
          />
          <Field
            label="Район"
            required
            {...register('district')}
            placeholder="Кадыкёй"
            error={errors.district?.message}
          />
        </div>

        <Controller
          name="management_type"
          control={control}
          render={({ field }) => (
            <SelectField
              label="Тип управления"
              required
              {...field}
              options={MANAGEMENT_TYPES}
              error={errors.management_type?.message}
            />
          )}
        />

        <Field
          label="Годовой бюджет (₺)"
          type="number"
          min="0"
          step="0.01"
          {...register('annual_budget')}
          placeholder="1000000"
          error={errors.annual_budget?.message}
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
