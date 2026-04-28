import { api } from '../lib/api';
import { useList } from '../hooks/useList';
import { PageLayout } from '../components/ui/PageLayout';
import { DataTable, type Column } from '../components/ui/DataTable';
import { Badge } from '../components/ui/Badge';
import type { Employee } from '../types';

const columns: Column<Employee>[] = [
  {
    key: 'user',
    label: 'Сотрудник',
    render: e => <span style={{ fontWeight: 500 }}>{e.user_display}</span>,
  },
  {
    key: 'role',
    label: 'Должность',
    render: e => e.role_display,
  },
  {
    key: 'department',
    label: 'Отдел',
    render: e => e.department_display,
  },
  {
    key: 'phone',
    label: 'Телефон',
    render: e => e.phone ?? '—',
  },
  {
    key: 'hire_date',
    label: 'Принят',
    render: e => new Date(e.hire_date).toLocaleDateString('ru-RU'),
  },
  {
    key: 'is_active',
    label: 'Статус',
    render: e => (
      <Badge label={e.is_active ? 'Активен' : 'Неактивен'} color={e.is_active ? 'green' : 'gray'} />
    ),
  },
];

export function StaffPage() {
  const { data, loading, error } = useList<Employee>(p => api.employees.list(p));

  return (
    <PageLayout title="Сотрудники">
      <DataTable
        columns={columns}
        rows={data}
        loading={loading}
        error={error}
        keyExtractor={e => e.id}
        emptyText="Нет сотрудников"
      />
    </PageLayout>
  );
}
