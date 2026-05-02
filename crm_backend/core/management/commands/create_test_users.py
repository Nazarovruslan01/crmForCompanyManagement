"""Management command to create test users and seed data for E2E tests."""

from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.properties.models import Apartment, Building
from apps.residents.models import Ownership, PersonalAccount, Resident
from apps.staff.models import Department, Employee
from apps.tickets.models import Ticket

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


def _create_or_update_user(data: dict[str, Any]) -> Any:
    user_data = data.copy()
    password = user_data.pop("password")
    role = user_data.pop("role")

    user, _ = User.objects.update_or_create(
        username=user_data["username"],
        defaults=user_data,
    )
    user.set_password(password)
    user.role = role
    user.save()
    return user


class Command(BaseCommand):
    help = "Create test users and seed data for E2E tests"

    def handle(self, *args: Any, **options: Any) -> None:
        for user_data in TEST_USERS:
            _create_or_update_user(user_data)

        self.stdout.write(self.style.SUCCESS("Ensured 4 test users exist"))
        self.stdout.write("\nTest credentials:")
        for user_data in TEST_USERS:
            self.stdout.write(f"  {user_data['username']} / {user_data['password']}")

        # ─── Seed related data ────────────────────────────────────────────────
        self._seed_departments()
        self._seed_buildings_and_apartments()
        self._seed_residents()
        self._seed_employees()
        self._seed_tickets()

    def _seed_departments(self) -> None:
        dept, _ = Department.objects.get_or_create(
            name="Teknik",
            defaults={"description": "Teknik servis departmanı"},
        )
        self.stdout.write(self.style.SUCCESS(f"Ensured department: {dept.name}"))

    def _seed_buildings_and_apartments(self) -> None:
        building, _ = Building.objects.get_or_create(
            name="E2E Test Sitesi",
            defaults={
                "address": "Test Caddesi 1",
                "city": "Antalya",
                "district": "Alanya",
                "management_type": "self_managed",
                "annual_budget": 500000,
            },
        )

        apt, _ = Apartment.objects.get_or_create(
            building=building,
            apartment_number="101",
            defaults={
                "floor": 1,
                "block": "A",
                "status": "active",
                "square_meters": 120.00,
                "tapu_number": "TAPU-101",
            },
        )

        self.stdout.write(self.style.SUCCESS(f"Ensured building: {building.name}"))
        self.stdout.write(self.style.SUCCESS(f"Ensured apartment: {apt}"))

    def _seed_residents(self) -> None:
        try:
            apartment = Apartment.objects.get(building__name="E2E Test Sitesi", apartment_number="101")
        except Apartment.DoesNotExist:
            self.stdout.write(self.style.WARNING("Apartment not found, skipping resident seed"))
            return

        resident, _ = Resident.objects.get_or_create(
            tc_kimlik_no="10000000146",
            defaults={
                "name": "Ahmet",
                "surname": "Yılmaz",
                "phone": "+90 555 000 00 01",
                "email": "ahmet@example.com",
                "owner_type": "owner",
                "is_active": True,
            },
        )

        Ownership.objects.get_or_create(
            resident=resident,
            apartment=apartment,
            role="owner",
            defaults={"is_primary": True},
        )

        PersonalAccount.objects.get_or_create(
            apartment=apartment,
            defaults={"account_number": "PA-001", "balance": 0},
        )

        self.stdout.write(self.style.SUCCESS(f"Ensured resident: {resident}"))

    def _seed_employees(self) -> None:
        try:
            worker_user = User.objects.get(username="worker")
            dept = Department.objects.get(name="Teknik")
        except (User.DoesNotExist, Department.DoesNotExist):
            self.stdout.write(self.style.WARNING("Worker user or department not found, skipping employee seed"))
            return

        employee, _ = Employee.objects.get_or_create(
            user=worker_user,
            defaults={
                "department": dept,
                "role": "master",
                "phone": "+90 555 000 00 02",
                "is_active": True,
            },
        )

        self.stdout.write(self.style.SUCCESS(f"Ensured employee: {employee}"))

    def _seed_tickets(self) -> None:
        try:
            apartment = Apartment.objects.get(building__name="E2E Test Sitesi", apartment_number="101")
            admin_user = User.objects.get(username="admin")
            employee = Employee.objects.get(  # type: ignore[misc]
                user__username="worker"
            )
        except (Apartment.DoesNotExist, User.DoesNotExist, Employee.DoesNotExist):
            self.stdout.write(self.style.WARNING("Required data missing, skipping ticket seed"))
            return

        ticket, _ = Ticket.objects.get_or_create(
            apartment=apartment,
            title="E2E Test Ticket",
            defaults={
                "description": "Created by E2E seed script",
                "category": "general",
                "priority": "medium",
                "status": "new",
                "created_by": admin_user,
                "assigned_worker": employee,
            },
        )

        self.stdout.write(self.style.SUCCESS(f"Ensured ticket: {ticket}"))
