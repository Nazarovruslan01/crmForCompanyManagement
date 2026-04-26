"""Management command to restore PostgreSQL database from a backup file."""

import subprocess

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Restore PostgreSQL database from a pg_dump .sql.gz backup file."

    def add_arguments(self, parser):  # type: ignore[override]
        parser.add_argument("backup_file", type=str, help="Path to the .sql.gz backup file")
        parser.add_argument("--dry-run", action="store_true", help="Validate file without restoring")

    def handle(self, *args, **options):  # type: ignore[override]
        backup_file: str = options["backup_file"]
        dry_run: bool = options["dry_run"]

        if not backup_file.endswith(".sql.gz"):
            raise CommandError("Backup file must be a .sql.gz file")

        import gzip
        import os

        if not os.path.exists(backup_file):
            raise CommandError(f"Backup file not found: {backup_file}")

        size_mb = os.path.getsize(backup_file) / (1024 * 1024)
        self.stdout.write(f"Backup file: {backup_file} ({size_mb:.1f} MB)")

        # Validate gzip integrity
        try:
            with gzip.open(backup_file, "rb") as f:
                # Read first 1KB to verify it's a valid SQL dump
                header = f.read(1024).decode("utf-8", errors="replace")
                if "--" not in header and "CREATE" not in header.upper() and "SET" not in header.upper():
                    raise CommandError("File does not appear to be a valid pg_dump output")
        except gzip.BadGzipFile as exc:
            raise CommandError(f"Invalid gzip file: {exc}") from exc

        self.stdout.write(self.style.SUCCESS("Backup file is valid"))

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run — skipping restore"))
            return

        db_url = getattr(settings, "DATABASE_URL", None) or os.getenv("DATABASE_URL", "")
        if not db_url:
            raise CommandError("DATABASE_URL not configured")

        self.stdout.write(self.style.WARNING("Restoring database — this will overwrite existing data!"))

        try:
            gunzip = subprocess.Popen(["gunzip", "-c", backup_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            psql = subprocess.Popen(
                ["psql", db_url],
                stdin=gunzip.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if gunzip.stdout:
                gunzip.stdout.close()

            _, psql_err = psql.communicate()
            gunzip.wait()

            if psql.returncode != 0:
                err_msg = psql_err.decode("utf-8", errors="replace") if psql_err else "Unknown error"
                raise CommandError(f"psql restore failed: {err_msg}")

            self.stdout.write(self.style.SUCCESS("Database restored successfully"))
        except FileNotFoundError:
            raise CommandError("psql or gunzip not found — ensure PostgreSQL client tools are installed")
