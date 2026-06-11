# CRM Frontend Roadmap

Результат аудита фронтенда и сравнения с бэкендом (2026-06-11).

---

## Текущее состояние

### Бэкенд
Все задачи из `BACKLOG.md` закрыты (P0–P3). Остаётся только инфра-задача P3-3 (pgBouncer).

### Фронтенд
- TypeScript: ✅ 0 ошибок
- ESLint: ✅ 0 предупреждений
- Тесты: ✅ 51/51 passed
- Страниц реализовано: 21/21 (ReportsPage добавлена)

---

## 🔴 Немедленно

### [F0-1] Починить падающие тесты `useList.test.ts`

**Файл:** `frontend/src/hooks/useList.test.ts`

**Проблема:** После добавления `AbortController` в `useList.ts` — `fetcher` вызывается с двумя аргументами `(params, signal)`. Тесты написаны под один аргумент и падают с:
```
expected last "spy" call to have been called with [ ObjectContaining{cursor: "abc123"} ]
received: [ ObjectContaining{cursor: "abc123"}, AbortSignal{} ]
```

**Фикс:** Обновить все `expect(...).toHaveBeenLastCalledWith(...)` — добавить второй аргумент:
```ts
// Было:
expect(fetcher).toHaveBeenLastCalledWith(
  expect.objectContaining({ cursor: 'abc123' }),
);

// Стало:
expect(fetcher).toHaveBeenLastCalledWith(
  expect.objectContaining({ cursor: 'abc123' }),
  expect.any(AbortSignal),
);
```

**Затронутые тесты:**
- `goNext extracts cursor from next URL`
- `goPrevious extracts cursor from previous URL`

**Оценка:** 30 мин

---

## 🟡 P1 — Высокая ценность, бэкенд готов

### [F1-1] Экспорт данных (Reports)

**Новая страница:** `/reports`

**Бэкенд:** `GET/POST /reports/exports/`, `GET /reports/exports/<id>/download/`

**Что делает бэкенд:**
- Создание экспорта → статус `PENDING`
- Celery генерирует файл `PROCESSING → COMPLETED | FAILED`
- Download готового файла

**Типы отчётов:** payments, aidat_charges, meetings, residents, apartments

**Форматы:** csv, xlsx, pdf

**Что реализовать на фронте:**
1. Добавить роут `/reports` в `App.tsx` (только admin/manager)
2. Добавить пункт меню в `DashboardLayout.tsx`
3. Добавить `reports` в `api.ts`:
   ```ts
   reports = {
     list:     (params?, signal?) => ...,
     create:   (data, signal?)    => ...,
     download: (id, signal?)      => ...,
   };
   ```
4. Страница `ReportsPage.tsx`:
   - Форма: тип отчёта + формат + опциональные фильтры → кнопка "Создать"
   - Таблица созданных экспортов (статус, дата, тип, формат)
   - Polling статуса для PENDING/PROCESSING (каждые 3 сек через `useEffect`)
   - Кнопка "Скачать" для COMPLETED
   - Бейдж статуса (pending/processing/completed/failed)

**Оценка:** 1 день

---

### [F1-2] Dashboard аналитика

**Файл:** `frontend/src/pages/DashboardPage.tsx`

**Бэкенд:** 4 endpoint готовы, ни один не используется:

| Endpoint | Что возвращает |
|----------|---------------|
| `GET /dashboard/building-breakdown/` | Статистика по каждому зданию |
| `GET /dashboard/ticket-metrics/` | Среднее время закрытия, breakdown по категориям |
| `GET /dashboard/payment-metrics/` | Collection rate, monthly trend |
| `GET /dashboard/aidat-timeseries/` | Ежемесячный тренд сборов по зданиям |

**Что реализовать:**
1. Добавить 4 метода в `api.ts`:
   ```ts
   dashboard = {
     summary:           (signal?) => ...,
     buildingBreakdown: (signal?) => ...,
     ticketMetrics:     (signal?) => ...,
     paymentMetrics:    (signal?) => ...,
     aidatTimeseries:   (signal?) => ...,
   };
   ```
2. Расширить `DashboardPage.tsx`:
   - Секция "По зданиям" (таблица / мини-карточки)
   - Секция "Заявки" — breakdown по категориям, среднее время закрытия
   - Секция "Платежи" — collection rate, месячный тренд (без чартов — текстовые метрики достаточны на старте)
   - Timeseries aidat — простая таблица по месяцам

**Оценка:** 4 часа

---

### [F1-3] Квитанции (Billing Receipts)

**Файл:** `frontend/src/pages/BillingPage.tsx`

**Бэкенд:** `GET /billing/receipts/`, `GET /billing/receipts/<id>/`, `POST /billing/receipts/`, `POST /billing/receipts/<id>/download/`

**Что реализовать:**
1. Добавить в `api.ts`:
   ```ts
   receipts = {
     list:     (params?, signal?) => ...,
     get:      (id, signal?)      => ...,
     create:   (data, signal?)    => ...,
     download: (id, signal?)      => ...,
   };
   ```
2. Добавить вкладку "Квитанции" в `BillingPage.tsx`:
   - Таблица (номер, квартира, сумма, дата, статус, ссылка на PDF)
   - Фильтры: статус, период
   - Кнопка "Создать квитанцию"
   - Кнопка "Скачать PDF" для каждой строки

**Оценка:** 3 часа

---

## 🟠 P2 — Полезно, средний объём

### [F2-1] Экстраординарные начисления

**Файл:** `frontend/src/pages/BillingPage.tsx`

**Бэкенд:** `GET/PATCH/DELETE /billing/extraordinary-charges/`

**Что реализовать:**
1. Добавить `extraordinaryCharges = this.crud<ExtraordinaryCharge>(...)` в `api.ts`
2. Вкладка "Доп. начисления" в `BillingPage.tsx` — CRUD-таблица
3. Добавить тип `ExtraordinaryCharge` в `types/index.ts`

**Оценка:** 2 часа

---

### [F2-2] Staff Tasks CRUD

**Файл:** `frontend/src/pages/StaffPage.tsx`

**Бэкенд:** полный CRUD `/staff/tasks/`

**Проблема:** На вкладке "Задачи" нет кнопки "Добавить задачу" — только просмотр.

**Что реализовать:**
1. Расширить `api.tasks` с `this.crud<Task>(...)` вместо только `.list()`
2. Добавить `TaskForm.tsx` в `components/forms/`
3. Кнопки "Добавить", "Редактировать", "Удалить" в таблице задач

**Оценка:** 3 часа

---

### [F2-3] Staff Departments CRUD

**Файл:** `frontend/src/pages/StaffPage.tsx` или `SettingsPage.tsx`

**Бэкенд:** полный CRUD `/staff/departments/`

**Что реализовать:**
1. Расширить `api.departments` с `this.crud<Department>(...)`
2. Управление отделами — вкладка в `SettingsPage.tsx` (admin-only)
3. Форма создания/редактирования отдела

**Оценка:** 2 часа

---

### [F2-4] Meetings: Протоколы и Повестка

**Файл:** `frontend/src/pages/MeetingDetailPage.tsx`

**Бэкенд:** `GET/POST/PATCH/DELETE /meetings/protocols/` и `/meetings/agenda-items/`

**Что реализовать:**
1. Добавить в `api.ts`:
   ```ts
   protocols    = this.crud<Protocol>('/meetings/protocols');
   agendaItems  = this.crud<AgendaItem>('/meetings/agenda-items');
   ```
2. В `MeetingDetailPage.tsx`:
   - Секция "Повестка" — добавление/редактирование/удаление пунктов повестки
   - Секция "Протокол" — создание/редактирование протокола собрания, кнопка скачать PDF

**Оценка:** 4 часа

---

## 🟢 P3 — Улучшения

### [F3-1] Шаблоны уведомлений

**Файл:** `frontend/src/pages/SettingsPage.tsx`

**Бэкенд:** полный CRUD `/notifications/templates/`

**Что реализовать:**
- Вкладка "Шаблоны" в `SettingsPage.tsx` (admin-only)
- CRUD-таблица шаблонов уведомлений (канал, шаблон текста, активен/нет)

**Оценка:** 2 часа

---

### [F3-2] Счётчик непрочитанных уведомлений

**Файл:** `frontend/src/components/DashboardLayout.tsx`

**Бэкенд:** `GET /notifications/logs/unread/`

**Что реализовать:**
- Добавить `api.notificationLogs.unread()` в `api.ts`
- Бейдж с числом непрочитанных на пункте меню "Уведомления"
- Polling каждые 60 сек через `useEffect`

**Оценка:** 1 час

---

### [B-P3-3] pgBouncer (бэкенд, инфра)

**Файл:** `crm_backend/config/settings/production.py`

**Проблема:** `CONN_MAX_AGE=60` без pgBouncer. При масштабировании Gunicorn + Celery Workers каждый процесс держит соединение открытым → исчерпание `max_connections` PostgreSQL.

**Фикс:**
- Установить pgBouncer перед PostgreSQL
- Добавить `CONN_HEALTH_CHECKS=True` в настройки DB
- Или использовать `django-db-pool`

**Оценка:** инфра-задача, 0.5 дня

---

## Сводная таблица

| ID | Приоритет | Описание | Файлы | Оценка | Статус |
|----|-----------|----------|-------|--------|--------|
| F0-1 | 🔴 | Починить тесты useList (AbortSignal) | `hooks/useList.test.ts` | 30 мин | ☑️ 2026-06-10 |
| F1-1 | 🟡 | Reports страница + polling | `pages/ReportsPage.tsx`, `api.ts` | 1 день | ☑️ 2026-06-11 |
| F1-2 | 🟡 | Dashboard аналитика (4 endpoint) | `pages/DashboardPage.tsx`, `api.ts` | 4 часа | ☑️ 2026-06-11 |
| F1-3 | 🟡 | Billing Receipts (list + download) | `pages/BillingPage.tsx`, `api.ts` | 3 часа | ☑️ 2026-06-11 |
| F2-1 | 🟠 | Extraordinary Charges CRUD | `pages/BillingPage.tsx`, `api.ts` | 2 часа | ☐ |
| F2-2 | 🟠 | Staff Tasks CRUD | `pages/StaffPage.tsx`, `forms/TaskForm.tsx` | 3 часа | ☐ |
| F2-3 | 🟠 | Staff Departments CRUD | `pages/SettingsPage.tsx`, `api.ts` | 2 часа | ☐ |
| F2-4 | 🟠 | Meetings Protocols + Agenda Items | `pages/MeetingDetailPage.tsx`, `api.ts` | 4 часа | ☐ |
| F3-1 | 🟢 | Notification Templates CRUD | `pages/SettingsPage.tsx` | 2 часа | ☐ |
| F3-2 | 🟢 | Unread notifications бейдж | `components/DashboardLayout.tsx` | 1 час | ☐ |
| B-P3-3 | 🟢 | pgBouncer / connection pooling | `settings/production.py` | 0.5 дня | ☐ |

---

## Аудит страниц

| Страница | Статус | Замечания |
|----------|--------|-----------|
| DashboardPage | ✅ | Все 5 endpoint интегрированы (summary + buildingBreakdown + ticketMetrics + paymentMetrics + aidatTimeseries) |
| BuildingsPage | ✅ | Полная |
| BuildingDetailPage | ✅ | Список квартир без прямых действий (нормально, есть шахматная доска) |
| BuildingSetupPage | ✅ | Отличный мастер настройки (3 шага) |
| ChessboardPage | ✅ | Полная визуализация с цветовой кодировкой |
| ApartmentDetailPage | ✅ | 3 таба (Жильцы, Заявки, Платежи), полная |
| TicketsPage | ✅ | Полная (поиск, 3 фильтра, табы по статусам, пагинация) |
| TicketDetailPage | ✅ | Rich: комментарии, вложения, смена статуса, назначение исполнителя |
| ResidentsPage | ✅ | Полная |
| ResidentDetailPage | ✅ | Полная |
| ReportsPage | ✅ | Полная (F1-1 ☑️ — create form + polling + download) |
| StaffPage | ⚠️ | На вкладке "Задачи" нет создания/редактирования/удаления → F2-2 |
| BillingPage | ⚠️ | Вкладка "Квитанции" добавлена (F1-3 ☑️), ожидает "Доп. начисления" (F2-1) |
| DocumentsPage | ✅ | Полная |
| MeetingsPage | ✅ | Полная |
| MeetingDetailPage | ⚠️ | Нет управления пунктами повестки и протоколом → F2-4 |
| NotificationsPage | ✅ | Read-only журнал (корректно для своей роли) |
| SettingsPage | ⚠️ | Нет управления отделами и шаблонами уведомлений → F2-3, F3-1 |
| LoginPage | ✅ | Полная, включая MFA |
| NotFoundPage | ✅ | — |
