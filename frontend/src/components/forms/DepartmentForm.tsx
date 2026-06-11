import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import toast from 'react-hot-toast';
import { api } from '../../lib/api';
import type { Department } from '../../types';
import { departmentSchema, type DepartmentFormData } from '../../validation/schemas';
import { Modal } from '../ui/Modal';
import { Field, TextareaField, FormActions } from '../ui/FormField';

interface Props {
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
  initial?: Department;
}

export function DepartmentForm({ open, onClose, onSaved, initial }: Props) {
  const isEdit = !!initial;
  const [saving, setSaving] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<DepartmentFormData>({
    resolver: zodResolver(departmentSchema),
    defaultValues: {
      name: initial?.name ?? '',
      description: initial?.description ?? '',
    },
  });

  useEffect(() => {
    if (!open) return;
    reset({
      name: initial?.name ?? '',
      description: initial?.description ?? '',
    });
  }, [open, initial, reset]);

  async function onSubmit(data: DepartmentFormData) {
    setSaving(true);
    try {
      if (isEdit) {
        await api.departments.update(initial!.id, data);
        toast.success('Отдел обновлён');
      } else {
        await api.departments.create(data);
        toast.success('Отдел добавлен');
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
    <Modal open={open} onClose={onClose} title={isEdit ? 'Редактировать отдел' : 'Новый отдел'}>
      <form onSubmit={handleSubmit(onSubmit)}>
        <Field
          label="Название"
          required
          {...register('name')}
          placeholder="Например: Техническое обслуживание"
          error={errors.name?.message}
        />

        <TextareaField
          label="Описание"
          {...register('description')}
          placeholder="Описание отдела"
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
