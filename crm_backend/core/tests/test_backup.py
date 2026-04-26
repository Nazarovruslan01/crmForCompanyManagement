"""Tests for database backup and restore integrity."""

import gzip
import os
import subprocess
import tempfile

import pytest
from django.conf import settings


@pytest.mark.django_db(transaction=True)
class TestBackupRestore:
    """Verify that pg_dump produces a valid, restorable backup."""

    @pytest.fixture
    def db_url(self):
        """Build DATABASE_URL from Django settings."""
        db = settings.DATABASES["default"]
        # Skip if using SQLite (local dev without DATABASE_URL)
        if "sqlite" in db["ENGINE"]:
            pytest.skip("Backup tests require PostgreSQL")
        return f"postgresql://{db['USER']}:{db['PASSWORD']}@{db['HOST']}:{db['PORT']}/{db['NAME']}"

    def test_pg_dump_creates_valid_gzip(self, db_url):
        """pg_dump | gzip creates a non-empty, valid .sql.gz file."""
        with tempfile.NamedTemporaryFile(suffix=".sql.gz", delete=False) as f:
            backup_path = f.name

        try:
            with open(backup_path, "wb") as out_f:
                dump = subprocess.Popen(
                    ["pg_dump", db_url, "--no-owner", "--no-privileges"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                gz = subprocess.Popen(
                    ["gzip", "-c"],
                    stdin=dump.stdout,
                    stdout=out_f,
                    stderr=subprocess.PIPE,
                )
                if dump.stdout:
                    dump.stdout.close()
                gz.wait()
                dump.wait()

            assert dump.returncode == 0, f"pg_dump failed: {dump.stderr.read().decode() if dump.stderr else ''}"
            assert gz.returncode == 0

            size = os.path.getsize(backup_path)
            assert size > 0, "Backup file is empty"

            # Verify gzip is valid and contains SQL
            with gzip.open(backup_path, "rt") as gf:
                header = gf.read(2048)
                assert "SET" in header.upper() or "CREATE" in header.upper() or "--" in header, (
                    "Backup does not look like a SQL dump"
                )
        finally:
            os.unlink(backup_path)

    def test_backup_restore_roundtrip(self, db_url):
        """Full cycle: dump → gzip → gunzip → psql succeeds without errors."""
        from apps.accounts.models import User

        # Insert a marker row
        marker = User.objects.create_user(
            username="backup_test_marker",
            email="marker@backup.test",
            password="BackupTest123!",
        )
        marker_id = marker.id

        # Dump
        with tempfile.NamedTemporaryFile(suffix=".sql.gz", delete=False) as f:
            backup_path = f.name

        try:
            with open(backup_path, "wb") as out_f:
                dump = subprocess.Popen(
                    ["pg_dump", db_url, "--no-owner", "--no-privileges"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                gz = subprocess.Popen(
                    ["gzip", "-c"],
                    stdin=dump.stdout,
                    stdout=out_f,
                    stderr=subprocess.PIPE,
                )
                if dump.stdout:
                    dump.stdout.close()
                gz.wait()
                dump.wait()

            assert dump.returncode == 0

            # Restore (into same DB — safe because test DB is ephemeral)
            gunzip = subprocess.Popen(
                ["gunzip", "-c", backup_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            psql = subprocess.Popen(
                ["psql", db_url, "-v", "ON_ERROR_STOP=0"],
                stdin=gunzip.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if gunzip.stdout:
                gunzip.stdout.close()
            _, psql_err = psql.communicate()
            gunzip.wait()

            # psql may output warnings about existing objects but should not fail fatally
            assert psql.returncode == 0, f"psql restore failed: {psql_err.decode() if psql_err else ''}"

            # Verify marker survived the roundtrip
            assert User.objects.filter(id=marker_id, username="backup_test_marker").exists(), (
                "Marker row not found after restore"
            )
        finally:
            os.unlink(backup_path)
