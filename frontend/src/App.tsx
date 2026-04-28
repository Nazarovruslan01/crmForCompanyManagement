import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { useAuth } from './hooks/useAuth';
import { LoginPage } from './pages/LoginPage';
import { DashboardLayout } from './components/DashboardLayout';
import { DashboardPage } from './pages/DashboardPage';
import { BuildingsPage } from './pages/BuildingsPage';
import { TicketsPage } from './pages/TicketsPage';
import { ResidentsPage } from './pages/ResidentsPage';
import { StaffPage } from './pages/StaffPage';
import { BillingPage } from './pages/BillingPage';
import { NotificationsPage } from './pages/NotificationsPage';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'var(--color-gray-7)',
        fontSize: 14,
      }}>
        Загрузка...
      </div>
    );
  }

  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function AppRoutes() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'var(--color-gray-7)',
        fontSize: 14,
      }}>
        Загрузка...
      </div>
    );
  }

  return (
    <Routes>
      <Route
        path="/login"
        element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginPage />}
      />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard"     element={<DashboardPage />} />
        <Route path="buildings"     element={<BuildingsPage />} />
        <Route path="tickets"       element={<TicketsPage />} />
        <Route path="residents"     element={<ResidentsPage />} />
        <Route path="staff"         element={<StaffPage />} />
        <Route path="billing"       element={<BillingPage />} />
        <Route path="notifications" element={<NotificationsPage />} />
        <Route path="settings"      element={<SettingsStub />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function SettingsStub() {
  return (
    <div className="page-wrapper">
      <div className="page-header"><h1>Настройки</h1></div>
      <div className="page-content" style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: 300,
        color: 'var(--color-gray-7)',
        fontSize: 15,
      }}>
        Раздел в разработке
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
