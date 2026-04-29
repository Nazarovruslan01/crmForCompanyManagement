import type { InputHTMLAttributes, SelectHTMLAttributes, TextareaHTMLAttributes } from 'react';

const labelStyle: React.CSSProperties = {
  display: 'block', fontSize: 13, fontWeight: 500,
  color: 'var(--color-gray-8)', marginBottom: 5,
};

const inputStyle: React.CSSProperties = {
  width: '100%', boxSizing: 'border-box',
  padding: '8px 11px', borderRadius: 8, fontSize: 14,
  border: '1.5px solid var(--color-gray-3)', outline: 'none',
  background: '#fff', color: 'var(--color-gray-9)',
  transition: 'border-color 150ms',
};

const fieldWrap: React.CSSProperties = { marginBottom: 16 };

interface BaseProps {
  label: string;
  required?: boolean;
  hint?: string;
  error?: string;
}

type InputProps = BaseProps & InputHTMLAttributes<HTMLInputElement>;

export function Field({ label, required, hint, error, ...input }: InputProps) {
  return (
    <div style={fieldWrap}>
      <label style={labelStyle}>
        {label} {required && <span style={{ color: '#e53e3e' }}>*</span>}
      </label>
      <input
        {...input}
        style={{
          ...inputStyle,
          borderColor: error ? '#e53e3e' : 'var(--color-gray-3)',
        }}
        onFocus={e => { e.currentTarget.style.borderColor = error ? '#e53e3e' : 'var(--color-brand)'; }}
        onBlur={e => { e.currentTarget.style.borderColor = error ? '#e53e3e' : 'var(--color-gray-3)'; }}
      />
      {hint && !error && <p style={{ margin: '4px 0 0', fontSize: 12, color: 'var(--color-gray-6)' }}>{hint}</p>}
      {error && <p style={{ margin: '4px 0 0', fontSize: 12, color: '#e53e3e' }}>{error}</p>}
    </div>
  );
}

interface SelectProps extends BaseProps, SelectHTMLAttributes<HTMLSelectElement> {
  options: { value: string | number; label: string }[];
  placeholder?: string;
}

export function SelectField({ label, required, hint, error, options, placeholder, ...rest }: SelectProps) {
  return (
    <div style={fieldWrap}>
      <label style={labelStyle}>
        {label} {required && <span style={{ color: '#e53e3e' }}>*</span>}
      </label>
      <select
        {...rest}
        style={{
          ...inputStyle,
          borderColor: error ? '#e53e3e' : 'var(--color-gray-3)',
          appearance: 'none',
          backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%23888' stroke-width='1.5' fill='none' stroke-linecap='round'/%3E%3C/svg%3E")`,
          backgroundRepeat: 'no-repeat',
          backgroundPosition: 'right 10px center',
          paddingRight: 32,
        }}
        onFocus={e => { e.currentTarget.style.borderColor = 'var(--color-brand)'; }}
        onBlur={e => { e.currentTarget.style.borderColor = error ? '#e53e3e' : 'var(--color-gray-3)'; }}
      >
        {placeholder && <option value="">{placeholder}</option>}
        {options.map(o => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
      {hint && !error && <p style={{ margin: '4px 0 0', fontSize: 12, color: 'var(--color-gray-6)' }}>{hint}</p>}
      {error && <p style={{ margin: '4px 0 0', fontSize: 12, color: '#e53e3e' }}>{error}</p>}
    </div>
  );
}

type TextareaProps = BaseProps & TextareaHTMLAttributes<HTMLTextAreaElement>;

export function TextareaField({ label, required, hint, error, ...rest }: TextareaProps) {
  return (
    <div style={fieldWrap}>
      <label style={labelStyle}>
        {label} {required && <span style={{ color: '#e53e3e' }}>*</span>}
      </label>
      <textarea
        {...rest}
        rows={rest.rows ?? 4}
        style={{
          ...inputStyle,
          resize: 'vertical', minHeight: 88,
          borderColor: error ? '#e53e3e' : 'var(--color-gray-3)',
        }}
        onFocus={e => { e.currentTarget.style.borderColor = error ? '#e53e3e' : 'var(--color-brand)'; }}
        onBlur={e => { e.currentTarget.style.borderColor = error ? '#e53e3e' : 'var(--color-gray-3)'; }}
      />
      {hint && !error && <p style={{ margin: '4px 0 0', fontSize: 12, color: 'var(--color-gray-6)' }}>{hint}</p>}
      {error && <p style={{ margin: '4px 0 0', fontSize: 12, color: '#e53e3e' }}>{error}</p>}
    </div>
  );
}

interface CheckboxProps extends BaseProps, InputHTMLAttributes<HTMLInputElement> {}

export function CheckboxField({ label, hint, error, ...input }: CheckboxProps) {
  return (
    <div style={{ ...fieldWrap, display: 'flex', alignItems: 'flex-start', gap: 10 }}>
      <input
        type="checkbox"
        {...input}
        style={{ marginTop: 2, accentColor: 'var(--color-brand)', width: 16, height: 16, flexShrink: 0 }}
      />
      <div>
        <label style={{ ...labelStyle, marginBottom: 0 }}>{label}</label>
        {hint && <p style={{ margin: '2px 0 0', fontSize: 12, color: 'var(--color-gray-6)' }}>{hint}</p>}
        {error && <p style={{ margin: '2px 0 0', fontSize: 12, color: '#e53e3e' }}>{error}</p>}
      </div>
    </div>
  );
}

export function FormRow({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 16px' }}>
      {children}
    </div>
  );
}

export function FormActions({ children }: { children: React.ReactNode }) {
  return (
    <div style={{
      display: 'flex', justifyContent: 'flex-end', gap: 10,
      paddingTop: 8, borderTop: '1px solid var(--color-gray-3)', marginTop: 8,
    }}>
      {children}
    </div>
  );
}
