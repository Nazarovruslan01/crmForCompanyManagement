import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { useAuth } from '../hooks/useAuth';
import { api } from '../lib/api';
import { useList } from '../hooks/useList';
import { PageLayout } from '../components/ui/PageLayout';
import { DataTable, type Column } from '../components/ui/DataTable';
import { Badge, type BadgeColor } from '../components/ui/Badge';
import { Pagination } from '../components/ui/Pagination';
import { SearchInput } from '../components/ui/SearchInput';
import { FilterSelect } from '../components/ui/FilterSelect';
import { TabBar } from '../components/ui/TabBar';
import { UserForm } from '../components/forms/UserForm';
import { DepartmentForm } from '../components/forms/DepartmentForm';
import { LogOut, Lock, Mail, Phone, Shield, User, Calendar, Eye, EyeOff } from 'lucide-react';
import type { User as UserType, Department } from '../types';

// ─── Profile Card ──────────────────────────────────────────────────────────

function ProfileCard() {
  const { user } = useAuth();
  if (!user) return null;

  const initial = (user.full_name ?? user.username ?? '?').charAt(0).toUpperCase();
  const roleColor: Record<string, { bg: string; color: string }> = {
    admin:    { bg: '#fff4ed', color: '#F26522' },
    manager:  { bg: '#e6f7ff', color: '#1677ff' },
    worker:   { bg: '#f6ffed', color: '#52c41a' },
    resident: { bg: '#f9f0ff', color: '#722ed1' },
  };
  const roleStyle = roleColor[user.role] ?? roleColor.resident;

  const meta = [
    { icon: User,     label: 'Логин',           value: user.username },
    { icon: Mail,     label: 'Email',            value: user.email || '—' },
    { icon: Phone,    label: 'Телефон',          value: user.phone ?? '—' },
    { icon: Calendar, label: 'Дата регистрации', value: new Date(user.date_joined).toLocaleDateString('ru-RU') },
  ];

  return (
    <div style={{
      background: '#fff', borderRadius: 14,
      border: '1px solid var(--color-gray-3)',
      boxShadow: 'var(--shadow-card)',
      overflow: 'hidden', marginBottom: 20,
    }}>
      <div style={{
        height: 72,
        background: 'linear-gradient(120deg, #FFF4ED 0%, #fff7f0 60%, #f0f4ff 100%)',
        borderBottom: '1px solid var(--color-gray-2)',
      }} />
      <div style={{ padding: '0 24px 24px', marginTop: -36 }}>
        <div style={{
          width: 72, height: 72, borderRadius: '50%',
          background: 'linear-gradient(135deg, #F26522, #D9561A)',
          color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 28, fontWeight: 700,
          border: '3px solid #fff', boxShadow: '0 4px 12px rgba(242,101,34,0.3)',
          marginBottom: 12,
        }}>
          {initial}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap', marginBottom: 20 }}>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 700 }}>{user.full_name ?? user.username}</h2>
          <span style={{
            display: 'inline-flex', alignItems: 'center', gap: 4,
            padding: '3px 10px', borderRadius: 20,
            fontSize: 12, fontWeight: 600,
            background: roleStyle.bg, color: roleStyle.color,
          }}>
            <Shield size={10} /> {user.role_display}
          </span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px 24px' }}>
          {meta.map(({ icon: Icon, label, value }) => (
            <div key={label} style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
              <div style={{
                width: 32, height: 32, borderRadius: 8,
                background: 'var(--color-gray-1)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                flexShrink: 0, marginTop: 2,
              }}>
                <Icon size={15} color="var(--color-gray-7)" />
              </div>
              <div>
                <p style={{ margin: 0, fontSize: 11, color: 'var(--color-gray-6)', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.04em' }}>{label}</p>
                <p style={{ margin: '2px 0 0', fontSize: 13.5, fontWeight: 500 }}>{value}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Password Form ─────────────────────────────────────────────────────────

function PasswordForm() {
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showOld, setShowOld] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null); setSuccess(null);
    if (!oldPassword || !newPassword) { setError('Все поля обязательны'); return; }
    if (newPassword !== confirmPassword) { setError('Пароли не совпадают'); return; }
    if (newPassword.length < 8) { setError('Минимум 8 символов'); return; }
    setLoading(true);
    try {
      const res = await api.changePassword(oldPassword, newPassword);
      setSuccess(res.detail);
      setOldPassword(''); setNewPassword(''); setConfirmPassword('');
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const eyeBtn = (show: boolean, toggle: () => void) => (
    <button type="button" onClick={toggle} style={{
      position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)',
      background: 'none', border: 'none', padding: 0, cursor: 'pointer',
      color: 'var(--color-gray-6)', display: 'flex',
    }}>
      {show ? <EyeOff size={15} /> : <Eye size={15} />}
    </button>
  );

  return (
    <div style={{
      background: '#fff', borderRadius: 14,
      border: '1px solid var(--color-gray-3)',
      boxShadow: 'var(--shadow-card)', padding: 24, marginBottom: 20,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
        <div style={{ width: 36, height: 36, borderRadius: 10, background: 'var(--color-brand-light)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Lock size={17} color="var(--color-brand)" />
        </div>
        <div>
          <h2 style={{ margin: 0, fontSize: 15, fontWeight: 700 }}>Смена пароля</h2>
          <p style={{ margin: 0, fontSize: 12, color: 'var(--color-gray-6)' }}>Минимум 8 символов</p>
        </div>
      </div>
      {error && <div style={{ padding: '10px 14px', borderRadius: 8, background: '#fff2f0', border: '1px solid #ffccc7', color: '#ff4d4f', fontSize: 13, marginBottom: 16 }}>{error}</div>}
      {success && <div style={{ padding: '10px 14px', borderRadius: 8, background: '#f6ffed', border: '1px solid #b7eb8f', color: '#52c41a', fontSize: 13, marginBottom: 16 }}>{success}</div>}
      <form onSubmit={handleSubmit} style={{ display: 'grid', gap: 14 }}>
        <div>
          <label className="form-label">Текущий пароль</label>
          <div style={{ position: 'relative' }}>
            <input type={showOld ? 'text' : 'password'} value={oldPassword} onChange={e => setOldPassword(e.target.value)} className="form-input" style={{ paddingRight: 40 }} placeholder="••••••••" />
            {eyeBtn(showOld, () => setShowOld(!showOld))}
          </div>
        </div>
        <div>
          <label className="form-label">Новый пароль</label>
          <div style={{ position: 'relative' }}>
            <input type={showNew ? 'text' : 'password'} value={newPassword} onChange={e => setNewPassword(e.target.value)} className="form-input" style={{ paddingRight: 40 }} placeholder="••••••••" />
            {eyeBtn(showNew, () => setShowNew(!showNew))}
          </div>
        </div>
        <div>
          <label className="form-label">Подтвердите новый пароль</label>
          <input type="password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} className="form-input" placeholder="••••••••" />
        </div>
        <button type="submit" disabled={loading} className="btn-primary" style={{ justifySelf: 'start' }}>
          {loading ? 'Сохранение...' : 'Изменить пароль'}
        </button>
      </form>
    </div>
  );
}

// ─── Logout Card ───────────────────────────────────────────────────────────

function LogoutCard({ onLogout }: { onLogout: () => void }) {
  const [hover, setHover] = useState(false);
  return (
    <div style={{ background: '#fff', borderRadius: 14, border: '1px solid var(--color-gray-3)', boxShadow: 'var(--shadow-card)', padding: 24 }}>
      <h2 style={{ margin: '0 0 4px', fontSize: 15, fontWeight: 700 }}>Выход из аккаунта</h2>
      <p style={{ margin: '0 0 16px', fontSize: 13, color: 'var(--color-gray-6)' }}>Завершить текущую сессию</p>
      <button
        onClick={onLogout}
        onMouseEnter={() => setHover(true)}
        onMouseLeave={() => setHover(false)}
        style={{
          padding: '9px 18px', borderRadius: 9, border: '1px solid',
          borderColor: hover ? '#ff7875' : 'var(--color-gray-3)',
          background: hover ? '#fff2f0' : '#fff',
          color: '#ff4d4f', fontSize: 13.5, fontWeight: 500,
          cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: 8,
          transition: 'all 150ms ease',
        }}
      >
        <LogOut size={15} /> Выйти
      </button>
    </div>
  );
}

// ─── Users Tab ─────────────────────────────────────────────────────────────

const ROLE_OPTIONS = [
  { value: 'admin',    label: 'Администратор' },
  { value: 'manager',  label: 'Менеджер' },
  { value: 'worker',   label: 'Сотрудник' },
  { value: 'resident', label: 'Жилец' },
];

const roleColor: Record<string, BadgeColor> = {
  admin:    'orange',
  manager:  'blue',
  worker:   'green',
  resident: 'purple',
};

const userColumns: Column<UserType>[] = [
  {
    key: 'name',
    label: 'Пользователь',
    render: u => (
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{
          width: 32, height: 32, borderRadius: '50%',
          background: 'linear-gradient(135deg, #F26522, #D9561A)',
          color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 13, fontWeight: 700, flexShrink: 0,
        }}>
          {(u.full_name || u.username).charAt(0).toUpperCase()}
        </div>
        <div>
          <p style={{ margin: 0, fontWeight: 500, fontSize: 13 }}>{u.full_name || u.username}</p>
          <p style={{ margin: 0, fontSize: 11.5, color: 'var(--color-gray-6)' }}>{u.username}</p>
        </div>
      </div>
    ),
  },
  {
    key: 'role',
    label: 'Роль',
    render: u => <Badge label={u.role_display} color={roleColor[u.role] ?? 'gray'} />,
  },
  {
    key: 'email',
    label: 'Email',
    render: u => u.email || '—',
  },
  {
    key: 'phone',
    label: 'Телефон',
    render: u => u.phone ?? '—',
  },
  {
    key: 'is_active',
    label: 'Статус',
    render: u => <Badge label={u.is_active ? 'Активен' : 'Неактивен'} color={u.is_active ? 'green' : 'gray'} />,
  },
  {
    key: 'date_joined',
    label: 'Создан',
    render: u => new Date(u.date_joined).toLocaleDateString('ru-RU'),
  },
];

function UsersTab() {
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<UserType | undefined>();

  const params = useMemo(() => {
    const p: Record<string, string> = {};
    if (search) p.search = search;
    if (roleFilter) p.role = roleFilter;
    return Object.keys(p).length ? p : undefined;
  }, [search, roleFilter]);

  const { data, loading, error, hasNext, hasPrevious, goNext, goPrevious, refetch } =
    useList<UserType>(p => api.users.list(p), params);

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
        <button
          className="btn-primary"
          onClick={() => { setEditing(undefined); setFormOpen(true); }}
          style={{ padding: '8px 18px', borderRadius: 8, fontSize: 14, fontWeight: 500 }}
        >
          + Добавить пользователя
        </button>
      </div>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 16, flexWrap: 'wrap' }}>
        <SearchInput
          placeholder="Поиск по логину, имени или email"
          onSearch={setSearch}
          style={{ marginBottom: 0, flex: 1, minWidth: 220 }}
        />
        <FilterSelect
          value={roleFilter}
          onChange={setRoleFilter}
          options={ROLE_OPTIONS}
          placeholder="Роль"
        />
      </div>
      <DataTable
        columns={userColumns}
        rows={data}
        loading={loading}
        error={error}
        keyExtractor={u => u.id}
        emptyText="Нет пользователей"
        onRowClick={u => { setEditing(u); setFormOpen(true); }}
      />
      <Pagination hasPrevious={hasPrevious} hasNext={hasNext} onPrevious={goPrevious} onNext={goNext} />
      <UserForm
        key={String(formOpen) + '-' + (editing?.id ?? 'new')}
        open={formOpen}
        onClose={() => setFormOpen(false)}
        onSaved={refetch}
        initial={editing}
      />
    </>
  );
}

// ─── Departments Tab ───────────────────────────────────────────────────────

const departmentColumns: Column<Department>[] = [
  {
    key: 'name',
    label: 'Название',
    render: d => <span className="text-semi">{d.name}</span>,
  },
  {
    key: 'description',
    label: 'Описание',
    render: d => d.description ?? '—',
  },
];

const departmentColumnsWithActions = (onEdit: (d: Department) => void, onDelete: (id: number) => void): Column<Department>[] => [
  ...departmentColumns,
  {
    key: 'actions',
    label: 'Действия',
    render: d => (
      <div style={{ display: 'flex', gap: '8px' }}>
        <button
          onClick={() => onEdit(d)}
          style={{
            background: 'none', border: 'none', color: 'var(--color-brand)',
            cursor: 'pointer', fontSize: 14, padding: '4px 8px',
          }}
        >
          ✎
        </button>
        <button
          onClick={() => onDelete(d.id)}
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

function DepartmentsTab() {
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Department | undefined>();

  const { data, loading, error, hasNext, hasPrevious, goNext, goPrevious, refetch } =
    useList<Department>(p => api.departments.list(p), undefined);

  const handleDelete = async (id: number) => {
    if (!confirm('Удалить отдел?')) return;
    try {
      await api.departments.delete(id);
      toast.success('Отдел удалён');
      refetch();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Ошибка удаления');
    }
  };

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
        <button
          className="btn-primary"
          onClick={() => { setEditing(undefined); setFormOpen(true); }}
          style={{ padding: '8px 18px', borderRadius: 8, fontSize: 14, fontWeight: 500 }}
        >
          + Добавить отдел
        </button>
      </div>
      <DataTable
        columns={departmentColumnsWithActions(
          d => { setEditing(d); setFormOpen(true); },
          handleDelete
        )}
        rows={data}
        loading={loading}
        error={error}
        keyExtractor={d => d.id}
        emptyText="Нет отделов"
      />
      <Pagination hasPrevious={hasPrevious} hasNext={hasNext} onPrevious={goPrevious} onNext={goNext} />
      <DepartmentForm
        open={formOpen}
        onClose={() => { setFormOpen(false); setEditing(undefined); }}
        onSaved={refetch}
        initial={editing}
      />
    </>
  );
}

// ─── Page ──────────────────────────────────────────────────────────────────

const TABS = [
  { value: 'profile', label: 'Профиль' },
  { value: 'users',   label: 'Пользователи' },
  { value: 'departments', label: 'Отделы' },
] as const;

type Tab = typeof TABS[number]['value'];

export function SettingsPage() {
  const { logout, user } = useAuth();
  const navigate = useNavigate();
  const [tab, setTab] = useState<Tab>('profile');

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const isAdmin = user?.role === 'admin' || user?.role === 'manager';

  return (
    <PageLayout title="Настройки">
      {isAdmin && <TabBar tabs={TABS} value={tab} onChange={setTab} style={{ marginBottom: 20 }} />}

      {tab === 'profile' && (
        <div style={{ maxWidth: 600 }}>
          <ProfileCard />
          <PasswordForm />
          <LogoutCard onLogout={handleLogout} />
        </div>
      )}

      {tab === 'users' && isAdmin && <UsersTab />}

      {tab === 'departments' && isAdmin && <DepartmentsTab />}
    </PageLayout>
  );
}
