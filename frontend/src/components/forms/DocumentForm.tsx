import { useState, useEffect, useRef } from 'react';
import { Upload } from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '../../lib/api';
import type { Building } from '../../types';
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

  const [form, setForm] = useState({
    title: '',
    document_type: 'other',
    description: '',
    building: '',
  });

  useEffect(() => {
    if (!open) return;
    api.buildings.list().then(r => setBuildings(r.results)).catch(() => {});
  }, [open]);

  const set = (field: keyof typeof form) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
      setForm(f => ({ ...f, [field]: e.target.value }));

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const fd = new FormData();
      fd.append('title', form.title);
      fd.append('document_type', form.document_type);
      if (form.description) fd.append('description', form.description);
      if (form.building) fd.append('building', form.building);
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
      <form onSubmit={submit}>
        <Field
          label="Название"
          required
          value={form.title}
          onChange={set('title')}
          placeholder="Договор управления №123"
        />
        <SelectField
          label="Тип документа"
          required
          value={form.document_type}
          onChange={set('document_type')}
          options={DOC_TYPE_OPTIONS}
        />
        <SelectField
          label="Здание"
          value={form.building}
          onChange={set('building')}
          options={buildingOptions}
          placeholder="Не привязан"
        />
        <TextareaField
          label="Описание"
          value={form.description}
          onChange={set('description')}
          placeholder="Краткое описание документа..."
          rows={3}
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
