"""Create a development superuser. Idempotent — safe to run multiple times."""
import argparse
import os
import sys


def _setup_django() -> None:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "crm_backend"))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
    import django

    django.setup()


def create_superuser(
    username: str,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    role: str,
) -> None:
    _setup_django()
    from apps.accounts.models import User

    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "is_superuser": True,
            "is_staff": True,
            "role": role,
        },
    )

    if not created:
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.is_superuser = True
        user.is_staff = True
        user.role = role

    user.set_password(password)
    user.save()

    action = "created" if created else "updated"
    print(f"Superuser '{username}' {action} successfully.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or update a development superuser.")
    parser.add_argument("-u", "--username", default="admin", help="Username (default: admin)")
    parser.add_argument("-e", "--email", default="admin@example.com", help="Email (default: admin@example.com)")
    parser.add_argument("-p", "--password", default="admin", help="Password (default: admin)")
    parser.add_argument("--first-name", default="Admin", help="First name (default: Admin)")
    parser.add_argument("--last-name", default="User", help="Last name (default: User)")
    parser.add_argument("--role", default="admin", help="Role (default: admin)")
    args = parser.parse_args()

    create_superuser(
        username=args.username,
        email=args.email,
        password=args.password,
        first_name=args.first_name,
        last_name=args.last_name,
        role=args.role,
    )


if __name__ == "__main__":
    main()
