# Frontend — Core

React 19 + TypeScript 6 + Vite 8 + Tailwind v4. Root: `frontend/`.

## Routing

- `src/App.tsx` — all routes. Pages are **lazy-loaded** via `React.lazy()`.
- Named export pattern: all pages use `export function PageName`.
- Lazy import pattern: `lazy(() => import('./pages/Foo').then(m => ({ default: m.Foo })))`
- Auth guards: `ProtectedRoute` (any auth) and `AuthorizeRoute` (role-based).
- Both guards preserve redirect: `state={{ from: location }}` → `Navigate to="/login"`.
- Roles: `admin`, `manager`, `staff`.

## API Client (`src/lib/api.ts`)

- Singleton `ApiClient` class with in-memory `accessToken`.
- Auto-refresh via HttpOnly cookie on 401; deduplicates concurrent refreshes with `refreshPromise`.
- `AbortSignal` passed through to fetch for cancellation.
- Base URL: `VITE_API_BASE` env var or `/api/v2`.

## State Management

- Server state: **TanStack React Query 5** — all API calls go through Query hooks in `src/hooks/queries/`.
- Auth state: `AuthContext` (`src/context/AuthContext.tsx`) — provides `user`, `isAuthenticated`, `isLoading`.
- No Redux/Zustand.

## Forms

- **react-hook-form 7** + **Zod 4** schemas (in `src/validation/schemas.ts`) + `@hookform/resolvers`.
- All form components in `src/components/forms/`.
- Select option arrays live in `src/constants/options.ts`.

## UI Components (`src/components/ui/`)

Key components and their props constraints:
- `SearchInput` — does **not** accept `style` prop; use className or wrapper div.
- `TabBar` — does **not** accept `style` prop.
- `Badge`, `DataTable`, `DetailPageLayout`, `FilterSelect`, `FormField`, `LoadingSpinner`, `Modal`, `PageLayout`, `Pagination`.

## TypeScript Invariants

- Strict mode.
- Page exports are **named**, never default.
- Union type fields (e.g. `status: "active" | "inactive" | "pending_handover"`) must not be widened to `string` — use `as const` or cast explicitly.
- `SearchInput` and `TabBar` do not expose `style` prop — use wrapper elements instead.

## Testing

- Unit: Vitest + @testing-library/react. Test files colocated (`*.test.tsx`).
- E2E: Playwright — specs in `frontend/e2e/`. Auth setup in `auth.setup.ts`.
- E2E settings: `config/settings/e2e.py` + `e2e_reset` management command.

## Known Pending Work

- Chessboard page (`/buildings/:id/chessboard`) — `ChessboardPage` component exists, backend ready. Full frontend grid (block tabs, floor grid, colored cells, apartment modal) not yet implemented beyond the existing stub.
