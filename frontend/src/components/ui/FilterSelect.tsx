interface Option { value: string; label: string }

interface FilterSelectProps {
  value: string;
  onChange: (v: string) => void;
  options: Option[];
  placeholder: string;
}

export function FilterSelect({ value, onChange, options, placeholder }: FilterSelectProps) {
  return (
    <select
      value={value}
      onChange={e => onChange(e.target.value)}
      style={{
        height: 38,
        padding: '0 32px 0 12px',
        borderRadius: 9,
        border: `1px solid ${value ? 'var(--color-brand)' : 'var(--color-gray-3)'}`,
        background: value ? 'var(--color-brand-light)' : '#fff',
        color: value ? 'var(--color-brand)' : 'var(--color-gray-7)',
        fontSize: 13,
        fontWeight: value ? 600 : 400,
        cursor: 'pointer',
        outline: 'none',
        appearance: 'none',
        backgroundImage: `url("data:image/svg+xml,%3Csvg width='10' height='6' viewBox='0 0 10 6' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M1 1L5 5L9 1' stroke='%23adb5bd' stroke-width='1.5' stroke-linecap='round'/%3E%3C/svg%3E")`,
        backgroundRepeat: 'no-repeat',
        backgroundPosition: 'right 10px center',
        transition: 'border-color 150ms, background 150ms, color 150ms',
        flexShrink: 0,
      }}
    >
      <option value="">{placeholder}</option>
      {options.map(o => (
        <option key={o.value} value={o.value}>{o.label}</option>
      ))}
    </select>
  );
}
