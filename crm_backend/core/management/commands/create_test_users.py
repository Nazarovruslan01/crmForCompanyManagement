"""Management command to create test users for development."""

from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()

TEST_USERS = [
    {
        "username": "admin",
        "email": "admin@example.com",
        "password": "admin123!",
        "first_name": "Admin",
        "last_name": "User",
        "role": "admin",
    },
    {
        "username": "manager",
        "email": "manager@example.com",
        "password": "manager123!",
        "first_name": "Manager",
        "last_name": "User",
        "role": "manager",
    },
    {
        "username": "worker",
        "email": "worker@example.com",
        "password": "worker123!",
        "first_name": "Worker",
        "last_name": "User",
        "role": "worker",
    },
    {
        "username": "resident",
        "email": "resident@example.com",
        "password": "resident123!",
        "first_name": "Resident",
        "last_name": "User",
        "role": "resident",
    },
]


class Command(BaseCommand):
    help = "Create test users for development"

    def handle(self, *args: Any, **options: Any) -> None:
        created = 0
        updated = 0

        for user_data in TEST_USERS:
            # Copy to avoid mutating the original
            data = user_data.copy()
            password = data.pop("password")
            role = data.pop("role")

            user, is_new = User.objects.update_or_create(
                username=data["username"],
                defaults=data,
            )
            user.set_password(password)
            user.role = role
            user.save()

            if is_new:
                created += 1
                self.stdout.write(self.style.SUCCESS(f"Created user: {user.username} (role: {role})"))
            else:
                updated += 1
                self.stdout.write(self.style.WARNING(f"Updated user: {user.username} (role: {role})"))

        self.stdout.write(self.style.SUCCESS(f"\nDone: {created} created, {updated} updated"))
        self.stdout.write("\nTest credentials:")
        for user_data in TEST_USERS:
            self.stdout.write(f"  {user_data['username']} / {user_data['password']}")
