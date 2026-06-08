import { useState, useEffect, useRef } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Upload } from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '../../lib/api';
import type { Building } from '../../types';
import { documentSchema, type DocumentFormData } from '../../validation/schemas';
import { Modal } from '../ui/Modal';
import { Field, SelectField, TextareaField, FormActions } from '../ui/FormField';

interface Props {
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
}

const DOC_TYPE_OPTIONS = [
  { value: 'contract', label: 'Договор' },
  { value: 'protocol', label: 'Протокол собрания' },
  { value: 'receipt',  label: 'Квитанция' },
  { value: 'act',      label: 'Акт' },
  { value: 'other',    label: 'Прочее' },
];

export function DocumentForm({ open, onClose, onSaved }: Props) {
  const [saving, setSaving] = useState(false);
  const [buildings, setBuildings] = useState<Building[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { errors },
  } = useForm<DocumentFormData>({
    resolver: zodResolver(documentSchema),
    defaultValues: {
      title: '',
      document_type: 'other',
      description: '',
      building: '',
    },
  });

  useEffect(() => {
    if (!open) return;
    reset({
      title: '',
      document_type: 'other',
      description: '',
      building: '',
    });
    api.buildings.list().then(r => { setBuildings(r.results); setFile(null); }).catch(() => { setFile(null); });
  }, [open, reset]);

  async function onSubmit(data: DocumentFormData) {
    setSaving(true);
    try {
      const fd = new FormData();
      fd.append('title', data.title);
      fd.append('document_type', data.document_type);
      if (data.description) fd.append('description', data.description);
      if (data.building) fd.append('building', data.building);
      if (file) fd.append('file', file);

      await api.documents.upload(fd);
      toast.success('Документ загружен');
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
    <Modal open={open} onClose={onClose} title="Загрузить документ" width={520}>
      <form onSubmit={handleSubmit(onSubmit)}>
        <Field
          label="Название"
          required
          {...register('title')}
          placeholder="Договор управления №123"
          error={errors.title?.message}
        />
        <Controller
          name="document_type"
          control={control}
          render={({ field }) => (
            <SelectField
              label="Тип документа"
              required
              {...field}
              options={DOC_TYPE_OPTIONS}
              error={errors.document_type?.message}
            />
          )}
        />
        <Controller
          name="building"
          control={control}
          render={({ field }) => (
            <SelectField
              label="Здание"
              {...field}
              options={buildingOptions}
              placeholder="Не привязан"
              error={errors.building?.message}
            />
          )}
        />
        <TextareaField
          label="Описание"
          {...register('description')}
          placeholder="Краткое описание документа..."
          rows={3}
          error={errors.description?.message}
        />

        {/* File picker */}
        <div style={{ marginBottom: 16 }}>
          <label style={{ fontSize: 13, fontWeight: 500, color: 'var(--color-gray-8)', display: 'block', marginBottom: 6 }}>
            Файл
          </label>
          <input
            ref={fileRef}
            type="file"
            style={{ display: 'none' }}
            onChange={e => setFile(e.target.files?.[0] ?? null)}
          />
          <div
            onClick={() => fileRef.current?.click()}
            style={{
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '10px 14px', borderRadius: 9, cursor: 'pointer',
              border: `1.5px dashed ${file ? 'var(--color-brand)' : 'var(--color-gray-4)'}`,
              background: file ? 'var(--color-brand-light)' : '#fafafa',
              transition: 'all 150ms',
            }}
          >
            <Upload size={16} color={file ? 'var(--color-brand)' : 'var(--color-gray-6)'} />
            <span style={{
              fontSize: 13,
              color: file ? 'var(--color-brand)' : 'var(--color-gray-6)',
              fontWeight: file ? 500 : 400,
            }}>
              {file ? file.name : 'Нажмите для выбора файла'}
            </span>
            {file && (
              <span style={{ marginLeft: 'auto', fontSize: 11.5, color: 'var(--color-gray-6)' }}>
                {(file.size / 1024).toFixed(0)} КБ
              </span>
            )}
          </div>
        </div>

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
            {saving ? 'Загрузка...' : 'Загрузить'}
          </button>
        </FormActions>
      </form>
    </Modal>
  );
}
