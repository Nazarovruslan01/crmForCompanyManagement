# ACCESS EXCLUSIVE Migrations — Runbook

This runbook is the authoritative reference for safe deployment of schema
migrations on hot Postgres tables in this project. Read it before merging
any migration that touches `billing_payment`, `tickets_ticket`,
`documents_*`, `notifications_*`, or any other table expected to grow
beyond a few hundred thousand rows.

## 1. What ACCESS EXCLUSIVE means

`ACCESS EXCLUSIVE` is PostgreSQL's strongest table-level lock. It
conflicts with **every** other lock mode, including the implicit
`ACCESS SHARE` lock taken by a plain `SELECT`. Result: while the lock
is held, **no other session can read or write the table**.

Django's migration framework wraps schema operations in a transaction
by default, so the lock is held until the migration transaction commits.
Held-duration cost is roughly `O(rows)` for full-table rewrites, but it
is **non-trivial even for "metadata-only" changes** because Django
issues `CREATE INDEX` inside the same transaction when the `db_index`
flag on a field flips from `False` to `True` (or when a new
`models.Index(...)` is added in `Meta.indexes`).

The first symptom of an ACCESS EXCLUSIVE outage is request-path
latency, followed by 5xx errors and DB connection-pool exhaustion as
queued requests pile up waiting for the lock to release.

## 2. Default Django behavior (and why it's a footgun here)

`python manage.py makemigrations` produces `migrations.AlterField`
for any field-option change, including a `db_index=True` toggle. Django
runs the operation inside `transaction.atomic()` by default.

There was no concurrent-index support until **Django 5.1**, which
added `AddIndexConcurrently` and `RemoveIndexConcurrently`. The project
runs Django 5.2, so these are available.

## 3. Pattern A — Django 5.1+ concurrent indexes

```python
from django.db import migrations, models


class Migration(migrations.Migration):
    # REQUIRED for CONCURRENTLY; cannot run inside a transaction.
    atomic = False

    dependencies = [
        ("billing", "0018_payment_amount_positive"),
    ]

    operations = [
        migrations.AddIndexConcurrently(
            model_name="payment",
            index=models.Index(fields=["iyzico_conversation_id"], name="billing_pay_iyzico__idx"),
        ),
    ]
```

Properties:

- Index build takes `SHARE UPDATE EXCLUSIVE` → reads and writes proceed
  normally. The user-facing request path is **not** blocked.
- `CREATE INDEX CONCURRENTLY` can fail (e.g. duplicate values for a
  `UNIQUE` index, or pre-existing rows that violate the constraint).
  The migration must be idempotent, or you must run a follow-up
  `DROP INDEX CONCURRENTLY` and retry. The failure leaves an `INVALID`
  index behind; check `pg_index` before retrying.
- The migration class **must** set `atomic = False`. Inside a
  transaction, `CONCURRENTLY` is rejected by Postgres.

## 4. Pattern B — pre-deploy manual `CREATE INDEX CONCURRENTLY`

Works on all Django versions, including the legacy `0019` migration
that is already deployed.

1. **Edit the model field** to add the desired option
   (`db_index=True`, a new `models.Index(...)`, `unique=True`, etc.).
2. **Run `makemigrations`**, then **delete the auto-generated
   `AlterField` line from the migration** (or, equivalently, mark the
   migration as a no-op for the database while keeping the
   state-only change via `SeparateDatabaseAndState`).
3. **Document the manual step** in the migration file's docstring
   AND in the release notes for the deploy.
4. **In a maintenance window** (or pre-deploy, behind a feature flag
   for read paths), an operator runs:
   ```sql
   CREATE INDEX CONCURRENTLY billing_pay_iyzico__idx
       ON billing_payment (iyzico_conversation_id);
   ```
5. **Confirm** the new index exists (`\d billing_payment` in psql).
6. **Deploy the migration.** Because the field is already indexed in
   the database, Django's `AlterField` becomes a no-op on the index
   (still metadata-only, still ACCESS EXCLUSIVE on the table — but
   instantaneous because there's no work to do).
7. **Optional cleanup:** `DROP INDEX CONCURRENTLY` any superseded
   index from a prior attempt.

## 5. Decision tree

| Scenario | Pattern |
|---|---|
| New index, table < 100k rows, no strict uptime SLO | Default `AddIndex` is fine |
| New index, table ≥ 100k rows OR a hot table (payments, audit, tickets) | **Pattern A** (Django 5.1+) **or** Pattern B |
| Dropping an index that is still serving live queries | **Pattern A** with `RemoveIndexConcurrently` — never plain `RemoveIndex` |
| Altering a column type or nullability | Manual DDL in a maintenance window, not Django. There is no safe in-transaction option. |
| Adding `db_index=True` to an existing field via `AlterField` | **Pattern B** — this is the 0019 case. Never ship the auto-generated `AlterField` for an indexed field on a busy table. |

## 6. Migration checklist

Before approving a PR that contains a schema migration:

- [ ] `python manage.py makemigrations --dry-run --check` is clean.
- [ ] If adding or removing an index on a hot table, the migration uses
      `atomic = False` + `AddIndexConcurrently` / `RemoveIndexConcurrently`
      **or** the manual DDL runbook entry is in the release notes.
- [ ] For manual DDL: the index DDL was reviewed by a second engineer;
      rollback DDL (`DROP INDEX CONCURRENTLY`) is prepared; the deploy
      window is noted in the release notes.
- [ ] For Pattern A: the Postgres version is ≥ 9.6 (CONCURRENTLY has
      been supported since 9.2, but no-op rebuilds in 11+ make
      migrations more robust).
- [ ] Staging migration runs in < 5 minutes on a copy of prod-size
      data. Anything longer is a red flag.
- [ ] `pg_locks` and `pg_stat_activity` are watched during the staging
      deploy to confirm the lock is not held longer than expected.
- [ ] The migration file has a header comment that explains the lock
      risk and points back to this runbook.

## 7. How to detect this issue in PR review

- `git diff` shows a `models.AlterField` whose only change is
  `db_index=...` or a field's `unique=...` flag.
- A new `models.Index(...)` is added in `Meta.indexes` of a model that
  already has > 100k rows in production.
- A migration file is missing a header comment explaining the lock
  risk for any operation on a hot table.

When any of the above is true, the reviewer should request Pattern A
or Pattern B before approving the PR.
