"""Regression guard: P0-3 added an index on Payment.iyzico_conversation_id.

Two complementary checks:
1. Model field has db_index=True (source of truth for future migrations).
2. A migration file for the index exists and references the field with db_index=True
   (guards against setting the attribute without generating a migration).
"""
import re
from pathlib import Path

from django.test import SimpleTestCase

from apps.billing.models import Payment

MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "migrations"


class TestIyzicoConversationIdIndex(SimpleTestCase):
    """P0-3: Payment.iyzico_conversation_id must remain indexed."""

    def test_field_has_db_index(self):
        field = Payment._meta.get_field("iyzico_conversation_id")
        assert field.db_index is True, (  # type: ignore[union-attr]
            f"Expected db_index=True on Payment.iyzico_conversation_id; "
            f"got db_index={field.db_index!r}"  # type: ignore[union-attr]
        )

    def test_migration_records_db_index(self):
        migration_files = sorted(MIGRATIONS_DIR.glob("*.py"))
        assert migration_files, "No migration files found in billing/migrations"

        found = any(
            re.search(
                r"iyzico_conversation_id[^)]*db_index\s*=\s*True",
                f.read_text(encoding="utf-8"),
                re.DOTALL,
            )
            for f in migration_files
        )
        assert found, (
            "No migration in billing/migrations references "
            "iyzico_conversation_id with db_index=True. "
            "Run makemigrations after setting db_index=True on the field."
        )
