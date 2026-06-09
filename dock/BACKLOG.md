# Backend Stabilization Backlog

Результат анализа бекенда (2026-06-08). Отсортировано по приоритету.

---

## 🔴 P0 — Критические

### [P0-1] `alert_failed_payments` — загрузка всех записей в RAM
**Файл:** `crm_backend/core/tasks.py:684`
**Проблема:** `sum(c.total_due for c in overdue_charges)` итерирует весь QuerySet в памяти. При росте данных — OOM.
**Фикс:**
```python
# Было
total_debt = sum(c.total_due for c in overdue_charges)

# Стало
from django.db.models import Sum
total_debt = AidatCharge.objects.filter(
    status=AidatCharge.Status.OVERDUE,
).aggregate(total=Sum('total_due'))['total'] or Decimal('0')
```

---

### [P0-2] `IyzicoViewSet._get_client_ip` обходит TRUSTED_PROXY_IPS
**Файл:** `crm_backend/apps/billing/views.py:671`
**Проблема:** Собственная наивная реализация `_get_client_ip` не использует whitelist из `TRUSTED_PROXY_IPS`. Исправление S2 из секьюрити-аудита здесь не применяется — IP можно подделать через `X-Forwarded-For`.
**Фикс:** Вынести в `core/utils.py` единую функцию с TRUSTED_PROXY_IPS-логикой, использовать везде.
```python
# core/utils.py
def get_client_ip(request: HttpRequest) -> str:
    trusted = getattr(settings, 'TRUSTED_PROXY_IPS', set())
    remote_addr = request.META.get('REMOTE_ADDR', '')
    if remote_addr in trusted:
        forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
    return remote_addr
```

---

### [P0-3] Отсутствуют составные DB-индексы на горячих путях
**Проблема:** Без индексов — seq scan на больших таблицах.

| Таблица | Поля | Используется в |
|---------|------|----------------|
| `AidatCharge` | `(status, due_date)` | `send_telegram_debt_reminders`, `alert_failed_payments`, `send_reminder_notifications` |
| `Payment` | `(iyzico_token)` | `IyzicoViewSet.callback` |
| `Payment` | `(iyzico_conversation_id)` | `IyzicoViewSet.callback` |

**Фикс:** Миграция с `Index(fields=['status', 'due_date'])` для AidatCharge, `Index(fields=['iyzico_token'])` для Payment.

---

## 🟡 P1 — Важные

### [P1-1] `send_telegram_debt_reminders` — двойная оценка QuerySet
**Файл:** `crm_backend/core/tasks.py:375`
**Проблема:** `overdue_charges.exists()` + последующий `for charge in overdue_charges` = два одинаковых SQL-запроса.
**Фикс:**
```python
overdue_list = list(overdue_charges)
if not overdue_list:
    return TelegramReminderResult(sent=0, failed=0, no_chat_id=0)
# далее итерировать overdue_list
```

---

### [P1-2] `send_meeting_reminders` — N+1 INSERT для Telegram NotificationLog
**Файл:** `crm_backend/core/tasks.py:959-976`
**Проблема:** Каждый `NotificationLog.objects.create(...)` внутри цикла по Telegram-пользователям = отдельный INSERT. Email-блок правильно использует `bulk_create`, Telegram — нет.
**Фикс:** Собирать `telegram_logs_to_create: list[NotificationLog]`, затем `bulk_create` после цикла.

---

### [P1-3] `generate_receipt_pdf` — нет retry при сбое
**Файл:** `crm_backend/core/tasks.py:787`
**Проблема:** `@shared_task` без `bind=True, max_retries`. Сбой при генерации PDF или записи в storage = данные потеряны навсегда.
**Фикс:**
```python
@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def generate_receipt_pdf(self: Any, payment_id: int) -> ReceiptGenerationResult:
    ...
    except Exception as exc:
        raise self.retry(exc=exc)
```

---

### [P1-4] Redis — Celery и Channels делят одну DB
**Файл:** `crm_backend/config/settings/base.py:287-298`
**Проблема:** `CELERY_BROKER_URL` и `CHANNEL_LAYERS.hosts` оба используют `REDIS_URL` (DB 0). При нагрузке — конкуренция за ключи и память.
**Фикс:** Разделить Redis DB по назначению:
```python
CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CHANNEL_LAYERS = {"default": {"CONFIG": {"hosts": [os.getenv("REDIS_CHANNELS_URL", "redis://localhost:6379/2")]}}}
CACHES = {"default": {"LOCATION": os.getenv("REDIS_CACHE_URL", "redis://localhost:6379/1")}}
```
Добавить `REDIS_CHANNELS_URL` в env.

---

## 🟠 P2 — Средние

### [P2-1] Разнести Celery Beat расписание
**Файл:** `crm_backend/config/settings/base.py:304-345`
**Проблема:** `alert_failed_payments` и `send_meeting_reminders` стартуют одновременно в 08:00, создавая пик нагрузки на DB и Redis.
**Фикс:** Разнести по 5 минут:
```python
"alert-failed-payments":   crontab(hour=8, minute=0),
"send-meeting-reminders":  crontab(hour=8, minute=15),
"alert-stuck-tickets":     crontab(hour=8, minute=5),   # уже есть
"alert-deactivated-users": crontab(hour=8, minute=10),  # уже есть
```

---

### [P2-2] `backup_database` — DATABASE_URL в аргументе процесса
**Файл:** `crm_backend/core/tasks.py:582`
**Проблема:** `subprocess.Popen(["pg_dump", db_url], ...)` — URL с паролем виден в `ps aux` и может протечь в системные логи.
**Фикс:** Передавать через `PGPASSWORD` env var и использовать отдельные флаги:
```python
from urllib.parse import urlparse
parsed = urlparse(db_url)
env = {**os.environ, "PGPASSWORD": parsed.password or ""}
dump_proc = subprocess.Popen(
    ["pg_dump", "-h", parsed.hostname, "-U", parsed.username, parsed.path[1:]],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
)
```

---

## 🟢 P3 — Улучшения

### [P3-1] `CacheListRetrieveMixin` — cache key не нормализует query params
**Файл:** `crm_backend/core/mixins.py:92`
**Проблема:** `request.build_absolute_uri()` включает query params в порядке их прихода. `?status=pending&apartment=1` и `?apartment=1&status=pending` = два разных cache key при одинаковых данных.
**Фикс:** Нормализовать params перед построением ключа:
```python
from urllib.parse import urlencode, parse_qs, urlparse
def _cache_key(self, request, action):
    parsed = urlparse(request.build_absolute_uri())
    sorted_params = urlencode(sorted(parse_qs(parsed.query).items()))
    uri = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{sorted_params}"
    ...
```

---

### [P3-2] `generate_monthly_invoices` — неточный счётчик `created`
**Файл:** `crm_backend/core/tasks.py:489-533`
**Проблема:** `after_count - before_count` некорректен если другой процесс создал записи в промежутке между двумя COUNT-запросами.
**Фикс:** Считать `len(charges_to_create)` — это точное число попыток вставки. `ignore_conflicts=True` гарантирует идемпотентность.

---

### [P3-3] Connection pooling в продакшне
**Файл:** `crm_backend/config/settings/production.py`
**Проблема:** `CONN_MAX_AGE=60` без pgBouncer. При масштабировании (Gunicorn workers + Celery workers) каждый процесс держит соединение открытым, что ведёт к исчерпанию `max_connections` PostgreSQL.
**Фикс:** Установить pgBouncer перед PostgreSQL или использовать `django-db-pool`. Добавить `CONN_HEALTH_CHECKS=True` в настройки DB.

---

## Сводная таблица

| ID | Приоритет | Файл | Сложность | Статус |
|----|-----------|------|-----------|--------|
| P0-1 | 🔴 | `core/tasks.py:684` | 5 мин | ✅ |
| P0-2 | 🔴 | `billing/views.py:671` | 30 мин | ✅ |
| P0-3 | 🔴 | Миграция | 20 мин | ✅ |
| P1-1 | 🟡 | `core/tasks.py:375` | 5 мин | ✅ |
| P1-2 | 🟡 | `core/tasks.py:959` | 15 мин | ✅ |
| P1-3 | 🟡 | `core/tasks.py:787` | 5 мин | ✅ |
| P1-4 | 🟡 | `settings/base.py` | 10 мин | ✅ |
| P2-1 | 🟠 | `settings/base.py` | 5 мин | ☐ |
| P2-2 | 🟠 | `core/tasks.py:582` | 20 мин | ☐ |
| P3-1 | 🟢 | `core/mixins.py` | 30 мин | ☐ |
| P3-2 | 🟢 | `core/tasks.py:489` | 10 мин | ☐ |
| P3-3 | 🟢 | Инфра | Инфра | ☐ |

---

## Codebase Scan Findings

- [ ] `requests.post` found in `core/tasks.py:170` — external SMS call without CircuitBreaker | discovered 2026-06-09
- [ ] `requests.post` found in `apps/messenger/telegram_client.py:37` — external Telegram call without CircuitBreaker | discovered 2026-06-09
- [ ] `requests.post` found in `apps/billing/iyzico_client.py:75` — external Iyzico payment call without CircuitBreaker | discovered 2026-06-09
