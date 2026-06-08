import { useState, useEffect } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import toast from 'react-hot-toast';
import { api } from '../../lib/api';
import type { Resident } from '../../types';
import { residentSchema, type ResidentFormData } from '../../validation/schemas';
import { Modal } from '../ui/Modal';
import { Field, SelectField, CheckboxField, FormRow, FormActions } from '../ui/FormField';

interface Props {
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
  initial?: Resident;
}

const OWNER_TYPE_OPTIONS = [
  { value: 'owner', label: 'Собственник' },
  { value: 'tenant', label: 'Арендатор' },
  { value: 'family_member', label: 'Член семьи' },
  { value: 'other', label: 'Другое' },
];

export function ResidentForm({ open, onClose, onSaved, initial }: Props) {
  const isEdit = !!initial;
  const [saving, setSaving] = useState(false);

  const {
    register,
    handleSubmit,
    control,
    reset,
    watch,
    formState: { errors },
  } = useForm<ResidentFormData>({
    resolver: zodResolver(residentSchema),
    defaultValues: {
      name: initial?.name ?? '',
      surname: initial?.surname ?? '',
      phone: initial?.phone ?? '',
      email: initial?.email ?? '',
      tc_kimlik_no: initial?.tc_kimlik_no ?? '',
      passport_no: initial?.passport_no ?? '',
      is_foreign_owner: initial?.is_foreign_owner ?? false,
      owner_type: initial?.owner_type ?? 'owner',
    },
  });

  // eslint-disable-next-line react-hooks/incompatible-library
  const isForeignOwner = watch('is_foreign_owner');

  useEffect(() => {
    if (!open) return;
    reset({
      name: initial?.name ?? '',
      surname: initial?.surname ?? '',
      phone: initial?.phone ?? '',
      email: initial?.email ?? '',
      tc_kimlik_no: initial?.tc_kimlik_no ?? '',
      passport_no: initial?.passport_no ?? '',
      is_foreign_owner: initial?.is_foreign_owner ?? false,
      owner_type: initial?.owner_type ?? 'owner',
    });
  }, [open, initial, reset]);

  async function onSubmit(data: ResidentFormData) {
    setSaving(true);
    try {
      const payload = {
        name: data.name,
        surname: data.surname,
        phone: data.phone || null,
        email: data.email || null,
        tc_kimlik_no: data.is_foreign_owner ? null : (data.tc_kimlik_no || null),
        passport_no: data.is_foreign_owner ? (data.passport_no || null) : null,
        is_foreign_owner: data.is_foreign_owner,
        owner_type: data.owner_type,
      };
      if (isEdit) {
        await api.residents.update(initial!.id, payload);
        toast.success('Резидент обновлён');
      } else {
        await api.residents.create(payload);
        toast.success('Резидент добавлен');
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
    <Modal open={open} onClose={onClose} title={isEdit ? 'Редактировать резидента' : 'Новый резидент'}>
      <form onSubmit={handleSubmit(onSubmit)}>
        <FormRow>
          <Field
            label="Имя"
            required
            {...register('name')}
            placeholder="Ahmet"
            error={errors.name?.message}
          />
          <Field
            label="Фамилия"
            required
            {...register('surname')}
            placeholder="Yılmaz"
            error={errors.surname?.message}
          />
        </FormRow>
        <FormRow>
          <Field
            label="Телефон"
            type="tel"
            {...register('phone')}
            placeholder="+90 555 000 00 00"
            error={errors.phone?.message}
          />
          <Field
            label="Email"
            type="email"
            {...register('email')}
            placeholder="ahmet@example.com"
            error={errors.email?.message}
          />
        </FormRow>
        <Controller
          name="owner_type"
          control={control}
          render={({ field }) => (
            <SelectField
              label="Тип владельца"
              required
              {...field}
              options={OWNER_TYPE_OPTIONS}
              error={errors.owner_type?.message}
            />
          )}
        />
        <Controller
          name="is_foreign_owner"
          control={control}
          render={({ field }) => (
            <CheckboxField
              label="Иностранный владелец"
              checked={field.value}
              onChange={e => field.onChange(e.target.checked)}
            />
          )}
        />
        {isForeignOwner ? (
          <Field
            label="Номер паспорта"
            {...register('passport_no')}
            placeholder="AB1234567"
            error={errors.passport_no?.message}
          />
        ) : (
          <Field
            label="ТС кимлик но"
            {...register('tc_kimlik_no')}
            placeholder="12345678901"
            maxLength={11}
            hint="11-значный идентификационный номер гражданина Турции"
            error={errors.tc_kimlik_no?.message}
          />
        )}
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
