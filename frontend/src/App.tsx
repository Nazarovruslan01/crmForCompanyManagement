import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { useAuth } from './hooks/useAuth';
import { LoadingSpinner } from './components/ui/LoadingSpinner';
import type { User } from './types';
import { LoginPage } from './pages/LoginPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { DashboardLayout } from './components/DashboardLayout';
import { DashboardPage } from './pages/DashboardPage';
import { BuildingsPage } from './pages/BuildingsPage';
import { BuildingDetailPage } from './pages/BuildingDetailPage';
import { ChessboardPage } from './pages/ChessboardPage';
import { TicketsPage } from './pages/TicketsPage';
import { TicketDetailPage } from './pages/TicketDetailPage';
import { ResidentsPage } from './pages/ResidentsPage';
import { ResidentDetailPage } from './pages/ResidentDetailPage';
import { ApartmentDetailPage } from './pages/ApartmentDetailPage';
import { BuildingSetupPage } from './pages/BuildingSetupPage';
import { StaffPage } from './pages/StaffPage';
import { BillingPage } from './pages/BillingPage';
import { DocumentsPage } from './pages/DocumentsPage';
import { MeetingsPage } from './pages/MeetingsPage';
import { MeetingDetailPage } from './pages/MeetingDetailPage';
import { NotificationsPage } from './pages/NotificationsPage';
import { SettingsPage } from './pages/SettingsPage';
import { ErrorBoundary } from './components/ErrorBoundary';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function AuthorizeRoute({ children, allowedRoles }: { children: React.ReactNode; allowedRoles: User['role'][] }) {
  const { isAuthenticated, isLoading, user } = useAuth();

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (!user || !allowedRoles.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }
  return <>{children}</>;
}

export function AppRoutes() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingSpinner />;
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
        <Route path="buildings"     element={<AuthorizeRoute allowedRoles={['admin', 'manager']}><BuildingsPage /></AuthorizeRoute>} />
        <Route path="buildings/:id" element={<AuthorizeRoute allowedRoles={['admin', 'manager']}><BuildingDetailPage /></AuthorizeRoute>} />
        <Route path="buildings/:id/chessboard" element={<AuthorizeRoute allowedRoles={['admin', 'manager']}><ChessboardPage /></AuthorizeRoute>} />
        <Route path="buildings/:id/setup" element={<AuthorizeRoute allowedRoles={['admin', 'manager']}><BuildingSetupPage /></AuthorizeRoute>} />
        <Route path="apartments/:id" element={<ProtectedRoute><ApartmentDetailPage /></ProtectedRoute>} />
        <Route path="tickets"       element={<TicketsPage />} />
        <Route path="tickets/:id"    element={<TicketDetailPage />} />
        <Route path="residents"     element={<ProtectedRoute><ResidentsPage /></ProtectedRoute>} />
        <Route path="residents/:id" element={<ProtectedRoute><ResidentDetailPage /></ProtectedRoute>} />
        <Route path="staff"         element={<AuthorizeRoute allowedRoles={['admin', 'manager']}><StaffPage /></AuthorizeRoute>} />
        <Route path="billing"       element={<AuthorizeRoute allowedRoles={['admin', 'manager']}><BillingPage /></AuthorizeRoute>} />
        <Route path="documents"     element={<AuthorizeRoute allowedRoles={['admin', 'manager']}><DocumentsPage /></AuthorizeRoute>} />
        <Route path="meetings"      element={<AuthorizeRoute allowedRoles={['admin', 'manager']}><MeetingsPage /></AuthorizeRoute>} />
        <Route path="meetings/:id"  element={<AuthorizeRoute allowedRoles={['admin', 'manager']}><MeetingDetailPage /></AuthorizeRoute>} />
        <Route path="notifications" element={<AuthorizeRoute allowedRoles={['admin', 'manager']}><NotificationsPage /></AuthorizeRoute>} />
        <Route path="settings"      element={<AuthorizeRoute allowedRoles={['admin', 'manager']}><SettingsPage /></AuthorizeRoute>} />
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ErrorBoundary>
          <AppRoutes />
        </ErrorBoundary>
      </AuthProvider>
    </BrowserRouter>
  );
}
