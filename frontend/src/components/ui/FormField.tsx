import type { InputHTMLAttributes, SelectHTMLAttributes, TextareaHTMLAttributes } from 'react';

interface BaseProps {
  label: string;
  required?: boolean;
  hint?: string;
  error?: string;
}

type InputProps = BaseProps & InputHTMLAttributes<HTMLInputElement>;

export function Field({ label, required, hint, error, className = '', ...input }: InputProps) {
  return (
    <div className="form-field-wrap">
      <label htmlFor={input.name} className="form-label">
        {label} {required && <span className="required-asterisk">*</span>}
      </label>
      <input
        {...input}
        className={`form-input ${error ? 'form-input--error' : ''} ${className}`}
      />
      {hint && !error && <p className="form-hint">{hint}</p>}
      {error && <p className="form-error">{error}</p>}
    </div>
  );
}

interface SelectProps extends BaseProps, SelectHTMLAttributes<HTMLSelectElement> {
  options: { value: string | number; label: string }[];
  placeholder?: string;
}

export function SelectField({ label, required, hint, error, options, placeholder, className = '', ...rest }: SelectProps) {
  return (
    <div className="form-field-wrap">
      <label className="form-label">
        {label} {required && <span className="required-asterisk">*</span>}
      </label>
      <select
        {...rest}
        className={`form-select ${error ? 'form-select--error' : ''} ${className}`}
      >
        {placeholder && <option value="">{placeholder}</option>}
        {options.map(o => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
      {hint && !error && <p className="form-hint">{hint}</p>}
      {error && <p className="form-error">{error}</p>}
    </div>
  );
}

type TextareaProps = BaseProps & TextareaHTMLAttributes<HTMLTextAreaElement>;

export function TextareaField({ label, required, hint, error, className = '', ...rest }: TextareaProps) {
  return (
    <div className="form-field-wrap">
      <label className="form-label">
        {label} {required && <span className="required-asterisk">*</span>}
      </label>
      <textarea
        {...rest}
        rows={rest.rows ?? 4}
        className={`form-textarea ${error ? 'form-textarea--error' : ''} ${className}`}
      />
      {hint && !error && <p className="form-hint">{hint}</p>}
      {error && <p className="form-error">{error}</p>}
    </div>
  );
}

interface CheckboxProps extends BaseProps, InputHTMLAttributes<HTMLInputElement> {}

export function CheckboxField({ label, hint, error, className = '', ...input }: CheckboxProps) {
  return (
    <div className={`checkbox-field ${className}`}>
      <input
        type="checkbox"
        id={input.name}
        {...input}
      />
      <div>
        <label htmlFor={input.name} className="form-label" style={{ marginBottom: 0 }}>{label}</label>
        {hint && <p className="form-hint" style={{ margin: '2px 0 0' }}>{hint}</p>}
        {error && <p className="form-error" style={{ margin: '2px 0 0' }}>{error}</p>}
      </div>
    </div>
  );
}

export function FormRow({ children }: { children: React.ReactNode }) {
  return (
    <div className="form-row">
      {children}
    </div>
  );
}

export function FormActions({ children }: { children: React.ReactNode }) {
  return (
    <div className="form-actions">
      {children}
    </div>
  );
}
