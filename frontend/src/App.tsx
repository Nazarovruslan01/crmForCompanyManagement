import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { useAuth } from './hooks/useAuth';
import { LoadingSpinner } from './components/ui/LoadingSpinner';
import type { User } from './types';
import { LoginPage } from './pages/LoginPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { DashboardLayout } from './components/DashboardLayout';
import { ErrorBoundary } from './components/ErrorBoundary';

const DashboardPage = lazy(() => import('./pages/DashboardPage').then(m => ({ default: m.DashboardPage })));
const BuildingsPage = lazy(() => import('./pages/BuildingsPage').then(m => ({ default: m.BuildingsPage })));
const BuildingDetailPage = lazy(() => import('./pages/BuildingDetailPage').then(m => ({ default: m.BuildingDetailPage })));
const ChessboardPage = lazy(() => import('./pages/ChessboardPage').then(m => ({ default: m.ChessboardPage })));
const TicketsPage = lazy(() => import('./pages/TicketsPage').then(m => ({ default: m.TicketsPage })));
const TicketDetailPage = lazy(() => import('./pages/TicketDetailPage').then(m => ({ default: m.TicketDetailPage })));
const ResidentsPage = lazy(() => import('./pages/ResidentsPage').then(m => ({ default: m.ResidentsPage })));
const ResidentDetailPage = lazy(() => import('./pages/ResidentDetailPage').then(m => ({ default: m.ResidentDetailPage })));
const ApartmentDetailPage = lazy(() => import('./pages/ApartmentDetailPage').then(m => ({ default: m.ApartmentDetailPage })));
const BuildingSetupPage = lazy(() => import('./pages/BuildingSetupPage').then(m => ({ default: m.BuildingSetupPage })));
const StaffPage = lazy(() => import('./pages/StaffPage').then(m => ({ default: m.StaffPage })));
const BillingPage = lazy(() => import('./pages/BillingPage').then(m => ({ default: m.BillingPage })));
const DocumentsPage = lazy(() => import('./pages/DocumentsPage').then(m => ({ default: m.DocumentsPage })));
const MeetingsPage = lazy(() => import('./pages/MeetingsPage').then(m => ({ default: m.MeetingsPage })));
const MeetingDetailPage = lazy(() => import('./pages/MeetingDetailPage').then(m => ({ default: m.MeetingDetailPage })));
const NotificationsPage = lazy(() => import('./pages/NotificationsPage').then(m => ({ default: m.NotificationsPage })));
const SettingsPage = lazy(() => import('./pages/SettingsPage').then(m => ({ default: m.SettingsPage })));

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (!isAuthenticated) return <Navigate to="/login" replace state={{ from: location }} />;
  return <>{children}</>;
}

function AuthorizeRoute({ children, allowedRoles }: { children: React.ReactNode; allowedRoles: User['role'][] }) {
  const { isAuthenticated, isLoading, user } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (!isAuthenticated) return <Navigate to="/login" replace state={{ from: location }} />;
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
        <Route path="tickets"       element={<ProtectedRoute><TicketsPage /></ProtectedRoute>} />
        <Route path="tickets/:id"    element={<ProtectedRoute><TicketDetailPage /></ProtectedRoute>} />
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
          <Suspense fallback={<LoadingSpinner />}>
            <AppRoutes />
          </Suspense>
        </ErrorBoundary>
      </AuthProvider>
    </BrowserRouter>
  );
}
