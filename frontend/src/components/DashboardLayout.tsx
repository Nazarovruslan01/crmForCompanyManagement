import { useState } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import type { User } from '../types';
import {
  BarChart2,
  Building2,
  Users,
  ClipboardList,
  Wallet,
  Bell,
  Briefcase,
  Settings,
  ChevronLeft,
  ChevronRight,
  LogOut,
} from 'lucide-react';
import { HouseraLogo } from './HouseraLogo';

type UserRole = User['role'];

interface NavItem {
  to: string;
  icon: React.ElementType;
  label: string;
  roles: UserRole[];
}

const navItems: NavItem[] = [
  { to: '/dashboard',     icon: BarChart2,     label: 'Аналитика',     roles: ['admin', 'manager', 'worker', 'resident'] },
  { to: '/tickets',       icon: ClipboardList, label: 'Заявки',        roles: ['admin', 'manager', 'worker', 'resident'] },
  { to: '/buildings',     icon: Building2,     label: 'Здания',        roles: ['admin', 'manager'] },
  { to: '/residents',     icon: Users,         label: 'Жильцы',        roles: ['admin', 'manager'] },
  { to: '/staff',         icon: Briefcase,     label: 'Сотрудники',    roles: ['admin', 'manager'] },
  { to: '/billing',       icon: Wallet,        label: 'Платежи',       roles: ['admin', 'manager', 'resident'] },
  { to: '/notifications', icon: Bell,          label: 'Уведомления',   roles: ['admin', 'manager', 'worker', 'resident'] },
  { to: '/settings',      icon: Settings,      label: 'Настройки',     roles: ['admin', 'manager', 'worker', 'resident'] },
];

export function DashboardLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const toggleLeft = collapsed
    ? 'calc(var(--collapsed-side-menu-width) - 12px)'
    : 'calc(var(--side-menu-width) - 12px)';

  const initial = (user?.full_name ?? user?.username ?? '?').charAt(0).toUpperCase();

  return (
    <div style={{ display: 'flex', minHeight: '100vh', position: 'relative' }}>

      {/* ── Sidebar ── */}
      <aside className={`sidebar${collapsed ? ' collapsed' : ''}`}>

        {/* Logo */}
        <div className="sidebar-logo">
          <HouseraLogo collapsed={collapsed} height={collapsed ? 48 : 110} />
        </div>

        {/* Nav */}
        <nav className="sidebar-menu">
          {navItems
            .filter(item => user && (user.is_superuser || item.roles.includes(user.role)))
            .map(({ to, icon: Icon, label }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) => `menu-item${isActive ? ' active' : ''}`}
                title={collapsed ? label : undefined}
              >
                <Icon size={20} />
                <span>{label}</span>
              </NavLink>
            ))}
        </nav>

        {/* User block */}
        <div style={{
          padding: collapsed ? '16px' : '16px 20px',
          borderTop: '1px solid var(--color-gray-3)',
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          overflow: 'hidden',
          flexShrink: 0,
        }}>
          <div style={{
            width: 32, height: 32, borderRadius: '50%',
            background: '#F26522', color: '#fff',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 13, fontWeight: 600, flexShrink: 0,
          }}>
            {initial}
          </div>

          {!collapsed && (
            <div style={{ flex: 1, minWidth: 0 }}>
              <p style={{ margin: 0, fontSize: 13, fontWeight: 500, color: '#1f1f1f', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {user?.full_name ?? user?.username}
              </p>
              <p style={{ margin: 0, fontSize: 11, color: '#8c8c8c', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {user?.role_display}
              </p>
            </div>
          )}

          {!collapsed && (
            <button
              onClick={handleLogout}
              title="Выйти"
              style={{
                background: 'none', border: 'none', padding: 4, cursor: 'pointer',
                color: '#8c8c8c', display: 'flex', alignItems: 'center',
                borderRadius: 6, transition: 'color 150ms ease', flexShrink: 0,
              }}
              onMouseEnter={e => (e.currentTarget.style.color = '#1f1f1f')}
              onMouseLeave={e => (e.currentTarget.style.color = '#8c8c8c')}
            >
              <LogOut size={16} />
            </button>
          )}
        </div>
      </aside>

      {/* ── Toggle button (outside sidebar to avoid clip) ── */}
      <button
        className="sidebar-toggle"
        onClick={() => setCollapsed(!collapsed)}
        title={collapsed ? 'Развернуть' : 'Свернуть'}
        style={{ left: toggleLeft }}
      >
        {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
      </button>

      {/* ── Main area ── */}
      <div className={`sub-layout${collapsed ? ' collapsed' : ''}`}>

        {/* Header */}
        <header className="main-header">
          {/* left: date */}
          <div style={{ fontSize: 13, color: 'var(--color-gray-6)', fontWeight: 500 }}>
            {new Date().toLocaleDateString('ru-RU', { weekday: 'long', day: 'numeric', month: 'long' })}
          </div>

          {/* right: user */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ textAlign: 'right' }}>
              <p style={{ margin: 0, fontSize: 13, fontWeight: 600, color: 'var(--color-gray-9)' }}>
                {user?.full_name ?? user?.username}
              </p>
              <p style={{ margin: 0, fontSize: 11, color: 'var(--color-gray-6)' }}>
                {user?.role_display}
              </p>
            </div>
            <div style={{
              width: 36, height: 36, borderRadius: '50%',
              background: 'linear-gradient(135deg, #F26522, #D9561A)',
              color: '#fff',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 14, fontWeight: 700, flexShrink: 0,
              boxShadow: '0 2px 8px rgba(242,101,34,0.3)',
            }}>
              {initial}
            </div>
          </div>
        </header>

        <main style={{ flex: 1 }}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
