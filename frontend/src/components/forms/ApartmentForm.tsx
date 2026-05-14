import { useState, useEffect } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import toast from 'react-hot-toast';
import { api } from '../../lib/api';
import type { Apartment, Building } from '../../types';
import { APARTMENT_STATUS_OPTIONS } from '../../constants/options';
import { apartmentSchema, type ApartmentFormData } from '../../validation/schemas';
import { Modal } from '../ui/Modal';
import { Field, SelectField, FormActions, FormRow } from '../ui/FormField';

interface Props {
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
  initial?: Apartment;
  defaultBuildingId?: number;
}

export function ApartmentForm({ open, onClose, onSaved, initial, defaultBuildingId }: Props) {
  const isEdit = !!initial;
  const [saving, setSaving] = useState(false);
  const [buildings, setBuildings] = useState<Building[]>([]);

  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { errors },
  } = useForm<ApartmentFormData>({
    resolver: zodResolver(apartmentSchema),
    defaultValues: {
      building: String(initial?.building ?? defaultBuildingId ?? ''),
      apartment_number: initial?.apartment_number ?? '',
      floor: String(initial?.floor ?? ''),
      block: initial?.block ?? '',
      square_meters: initial?.square_meters ?? '',
      share_ratio_num: String(initial?.share_ratio_num ?? '1'),
      share_ratio_denom: String(initial?.share_ratio_denom ?? '1'),
      tapu_number: initial?.tapu_number ?? '',
      status: initial?.status ?? 'active',
    },
  });

  useEffect(() => {
    if (!open) return;
    reset({
      building: String(initial?.building ?? defaultBuildingId ?? ''),
      apartment_number: initial?.apartment_number ?? '',
      floor: String(initial?.floor ?? ''),
      block: initial?.block ?? '',
      square_meters: initial?.square_meters ?? '',
      share_ratio_num: String(initial?.share_ratio_num ?? '1'),
      share_ratio_denom: String(initial?.share_ratio_denom ?? '1'),
      tapu_number: initial?.tapu_number ?? '',
      status: initial?.status ?? 'active',
    });
    api.buildings.list().then(r => setBuildings(r.results)).catch(() => {});
  }, [open, initial, defaultBuildingId, reset]);

  async function onSubmit(data: ApartmentFormData) {
    setSaving(true);
    try {
      const payload = {
        building: Number(data.building),
        apartment_number: data.apartment_number,
        floor: data.floor ? Number(data.floor) : null,
        block: data.block || null,
        square_meters: data.square_meters || null,
        share_ratio_num: Number(data.share_ratio_num),
        share_ratio_denom: Number(data.share_ratio_denom),
        tapu_number: data.tapu_number || null,
        status: data.status,
      };
      if (isEdit) {
        await api.apartments.update(initial!.id, payload);
        toast.success('Квартира обновлена');
      } else {
        await api.apartments.create(payload);
        toast.success('Квартира добавлена');
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
    <Modal open={open} onClose={onClose} title={isEdit ? 'Редактировать квартиру' : 'Новая квартира'}>
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

        <FormRow>
          <Field
            label="Номер квартиры"
            required
            {...register('apartment_number')}
            placeholder="42"
            error={errors.apartment_number?.message}
          />
          <Field
            label="Этаж"
            type="number"
            {...register('floor')}
            placeholder="5"
            error={errors.floor?.message}
          />
        </FormRow>

        <FormRow>
          <Field
            label="Блок / секция"
            {...register('block')}
            placeholder="A"
            error={errors.block?.message}
          />
          <Field
            label="Площадь (м²)"
            type="number"
            min="0"
            step="0.01"
            {...register('square_meters')}
            placeholder="85.5"
            error={errors.square_meters?.message}
          />
        </FormRow>

        <FormRow>
          <Field
            label="Доля (числитель)"
            required
            type="number"
            min="1"
            {...register('share_ratio_num')}
            error={errors.share_ratio_num?.message}
          />
          <Field
            label="Доля (знаменатель)"
            required
            type="number"
            min="1"
            {...register('share_ratio_denom')}
            error={errors.share_ratio_denom?.message}
          />
        </FormRow>

        <Field
          label="Номер тапу"
          {...register('tapu_number')}
          placeholder="12345678"
          error={errors.tapu_number?.message}
        />

        <Controller
          name="status"
          control={control}
          render={({ field }) => (
            <SelectField
              label="Статус"
              required
              {...field}
              options={APARTMENT_STATUS_OPTIONS}
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
