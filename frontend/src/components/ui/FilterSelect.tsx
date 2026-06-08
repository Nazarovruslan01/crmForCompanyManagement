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
      className={`filter-select ${value ? 'filter-select--active' : ''}`}
    >
      <option value="">{placeholder}</option>
      {options.map(o => (
        <option key={o.value} value={o.value}>{o.label}</option>
      ))}
    </select>
  );
}
