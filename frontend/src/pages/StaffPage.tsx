import { useState, useMemo } from 'react';
import toast from 'react-hot-toast';
import { api } from '../lib/api';
import { useList } from '../hooks/useList';
import { PageLayout } from '../components/ui/PageLayout';
import { DataTable, type Column } from '../components/ui/DataTable';
import { Badge } from '../components/ui/Badge';
import { Pagination } from '../components/ui/Pagination';
import { SearchInput } from '../components/ui/SearchInput';
import { FilterSelect } from '../components/ui/FilterSelect';
import { TabBar } from '../components/ui/TabBar';
import { EmployeeForm } from '../components/forms/EmployeeForm';
import { TaskForm } from '../components/forms/TaskForm';
import { EMPLOYEE_ROLE_OPTIONS, TASK_STATUS_OPTIONS, TASK_STATUS_COLOR } from '../constants/options';
import type { Employee, Task } from '../types';

// ─── Avatar ──────────────────────────────────────────────────────────────────

function Avatar({ name }: { name: string }) {
  const initials = name
    .split(' ')
    .slice(0, 2)
    .map(w => w[0]?.toUpperCase() ?? '')
    .join('');
  return (
    <div style={{
      width: 34, height: 34, borderRadius: '50%',
      background: 'linear-gradient(135deg, #F26522, #D9561A)',
      color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontSize: 13, fontWeight: 700, flexShrink: 0,
      boxShadow: '0 2px 6px rgba(242,101,34,0.25)',
    }}>
      {initials || '?'}
    </div>
  );
}

// ─── Columns ─────────────────────────────────────────────────────────────────

const employeeColumns: Column<Employee>[] = [
  {
    key: 'user',
    label: 'Сотрудник',
    render: e => (
      <div className="info-row">
        <Avatar name={e.user_display} />
        <span className="text-semi">{e.user_display}</span>
      </div>
    ),
  },
  {
    key: 'role',
    label: 'Должность',
    render: e => e.role_display,
  },
  {
    key: 'department',
    label: 'Отдел',
    render: e => e.department_display ?? '—',
  },
  {
    key: 'phone',
    label: 'Телефон',
    render: e => e.phone ?? '—',
  },
  {
    key: 'hire_date',
    label: 'Принят',
    render: e => e.hire_date ? new Date(e.hire_date).toLocaleDateString('ru-RU') : '—',
  },
  {
    key: 'is_active',
    label: 'Статус',
    render: e => (
      <Badge label={e.is_active ? 'Активен' : 'Неактивен'} color={e.is_active ? 'green' : 'gray'} />
    ),
  },
];

const taskColumns = (onEdit: (t: Task) => void, onDelete: (id: number) => void): Column<Task>[] => [
  {
    key: 'title',
    label: 'Задача',
    render: t => (
      <div>
        <p className="heading-sm">{t.title}</p>
        {t.ticket_display && (
          <p className="text-muted-sm">
            Заявка: {t.ticket_display}
          </p>
        )}
      </div>
    ),
  },
  {
    key: 'assigned_to',
    label: 'Исполнитель',
    render: t => (
      <div className="info-row" style={{ gap: 8 }}>
        <Avatar name={t.assigned_to_display} />
        <span style={{ fontSize: 13 }}>{t.assigned_to_display}</span>
      </div>
    ),
  },
  {
    key: 'status',
    label: 'Статус',
    render: t => (
      <Badge
        label={t.status_display}
        color={TASK_STATUS_COLOR[t.status] ?? 'gray'}
      />
    ),
  },
  {
    key: 'due_date',
    label: 'Срок',
    render: t => {
      const due = new Date(t.due_date);
      const overdue = due < new Date() && t.status !== 'completed' && t.status !== 'cancelled';
      return (
        <span style={{ fontSize: 13, color: overdue ? '#ef4444' : undefined }} className={overdue ? 'text-bold' : undefined}>
          {due.toLocaleDateString('ru-RU')}
        </span>
      );
    },
  },
  {
    key: 'actions',
    label: 'Действия',
    render: t => (
      <div style={{ display: 'flex', gap: '8px' }}>
        <button
          onClick={() => onEdit(t)}
          style={{
            background: 'none', border: 'none', color: 'var(--color-brand)',
            cursor: 'pointer', fontSize: 14, padding: '4px 8px',
          }}
        >
          ✎
        </button>
        <button
          onClick={() => onDelete(t.id)}
          style={{
            background: 'none', border: 'none', color: '#ef4444',
            cursor: 'pointer', fontSize: 14, padding: '4px 8px',
          }}
        >
          ✕
        </button>
      </div>
    ),
  },
];

// ─── Tabs ────────────────────────────────────────────────────────────────────

const TABS = [
  { value: 'employees', label: 'Сотрудники' },
  { value: 'tasks',     label: 'Задачи' },
] as const;

type Tab = typeof TABS[number]['value'];

// ─── Page ────────────────────────────────────────────────────────────────────

export function StaffPage() {
  const [tab, setTab] = useState<Tab>('employees');

  // Employees state
  const [empSearch, setEmpSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Employee | undefined>();

  // Tasks state
  const [taskSearch, setTaskSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [taskFormOpen, setTaskFormOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | undefined>();

  const empParams = useMemo(() => {
    const p: Record<string, string> = {};
    if (empSearch) p.search = empSearch;
    if (roleFilter) p.role = roleFilter;
    return Object.keys(p).length ? p : undefined;
  }, [empSearch, roleFilter]);

  const taskParams = useMemo(() => {
    const p: Record<string, string> = {};
    if (taskSearch) p.search = taskSearch;
    if (statusFilter) p.status = statusFilter;
    return Object.keys(p).length ? p : undefined;
  }, [taskSearch, statusFilter]);

  const {
    data: employees, loading: empLoading, error: empError,
    hasNext: empNext, hasPrevious: empPrev, goNext: empGoNext, goPrevious: empGoPrev, refetch,
  } = useList<Employee>(p => api.employees.list(p), empParams);

  const {
    data: tasks, loading: taskLoading, error: taskError,
    hasNext: taskNext, hasPrevious: taskPrev, goNext: taskGoNext, goPrevious: taskGoPrev,
    refetch: refetchTasks,
  } = useList<Task>(p => api.tasks.list(p), taskParams);

  const handleTaskDelete = async (id: number) => {
    if (!confirm('Удалить задачу?')) return;
    try {
      await api.tasks.delete(id);
      toast.success('Задача удалена');
      refetchTasks();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Ошибка удаления');
    }
  };

  return (
    <PageLayout
      title="Сотрудники"
      actions={
        tab === 'employees' ? (
          <button
            className="btn-primary btn-sm"
            onClick={() => { setEditing(undefined); setFormOpen(true); }}
          >
            + Добавить сотрудника
          </button>
        ) : tab === 'tasks' ? (
          <button
            className="btn-primary btn-sm"
            onClick={() => { setEditingTask(undefined); setTaskFormOpen(true); }}
          >
            + Добавить задачу
          </button>
        ) : undefined
      }
    >
      <TabBar tabs={TABS} value={tab} onChange={setTab} />

      {tab === 'employees' && (
        <>
          <div className="filter-row">
            <div className="search-wrap">
              <SearchInput
                placeholder="Поиск по имени"
                onSearch={setEmpSearch}
              />
            </div>
            <FilterSelect
              value={roleFilter}
              onChange={setRoleFilter}
              options={EMPLOYEE_ROLE_OPTIONS}
              placeholder="Должность"
            />
          </div>
          <DataTable
            columns={employeeColumns}
            rows={employees}
            loading={empLoading}
            error={empError}
            keyExtractor={e => e.id}
            emptyText="Нет сотрудников"
            onRowClick={e => { setEditing(e); setFormOpen(true); }}
          />
          <Pagination hasPrevious={empPrev} hasNext={empNext} onPrevious={empGoPrev} onNext={empGoNext} />
        </>
      )}

      {tab === 'tasks' && (
        <>
          <div className="filter-row">
            <div className="search-wrap">
              <SearchInput
                placeholder="Поиск по задаче"
                onSearch={setTaskSearch}
              />
            </div>
            <FilterSelect
              value={statusFilter}
              onChange={setStatusFilter}
              options={TASK_STATUS_OPTIONS}
              placeholder="Статус"
            />
          </div>
          <DataTable
            columns={taskColumns(
              t => { setEditingTask(t); setTaskFormOpen(true); },
              handleTaskDelete
            )}
            rows={tasks}
            loading={taskLoading}
            error={taskError}
            keyExtractor={t => t.id}
            emptyText="Нет задач"
          />
          <Pagination hasPrevious={taskPrev} hasNext={taskNext} onPrevious={taskGoPrev} onNext={taskGoNext} />
        </>
      )}

      <EmployeeForm
        open={formOpen}
        onClose={() => setFormOpen(false)}
        onSaved={refetch}
        initial={editing}
      />

      <TaskForm
        open={taskFormOpen}
        onClose={() => { setTaskFormOpen(false); setEditingTask(undefined); }}
        onSaved={refetchTasks}
        initial={editingTask}
      />
    </PageLayout>
  );
}
