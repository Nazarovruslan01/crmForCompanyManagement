"""Regression guard: P0-3 added an index on Payment.iyzico_conversation_id.

pytest runs with --no-migrations, so runtime DB introspection is unavailable.
We parse the latest migration's AST/source directly to confirm the
db_index=True is preserved — catches accidental reverts or renames of
the field that would silently drop the index on next deploy.
"""
import re
from pathlib import Path

from django.test import SimpleTestCase

MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "migrations"


class TestIyzicoConversationIdIndex(SimpleTestCase):
    """P0-3: latest migration must reference iyzico_conversation_id with db_index=True."""

    def test_latest_migration_adds_db_index(self):
        migration_files = sorted(MIGRATIONS_DIR.glob("0019_*.py"))
        assert migration_files, "Expected migration 0019_* to exist for P0-3 index"
        latest = migration_files[-1]
        source = latest.read_text(encoding="utf-8")
        assert "iyzico_conversation_id" in source, (
            f"Expected iyzico_conversation_id in {latest.name}, not found"
        )
        match = re.search(
            r"iyzico_conversation_id[^)]*db_index\s*=\s*True",
            source,
            re.DOTALL,
        )
        assert match, (
            f"Expected db_index=True on iyzico_conversation_id in {latest.name}"
        )
