"""Pytest configuration and shared fixtures for CRM backend tests."""
from datetime import date, timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.billing.models import AidatCharge, Payment
from apps.notifications.models import NotificationTemplate
from apps.properties.models import Apartment, Building
from apps.residents.models import Ownership, PersonalAccount, Resident
from apps.staff.models import Department, Employee

# =============================================================================
# API Client Fixtures
# =============================================================================


@pytest.fixture
def api_client():
    """Return unauthenticated API client."""
    return APIClient()


@pytest.fixture
def authenticated_client(db):
    """Return API client authenticated as a regular resident user."""
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        role=User.Role.RESIDENT
    )
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def admin_client(db):
    """Return API client authenticated as an admin user."""
    user = User.objects.create_user(
        username='adminuser',
        email='admin@example.com',
        password='testpass123',
        role=User.Role.ADMIN,
        first_name='Admin',
        last_name='User'
    )
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def staff_client(db):
    """Return API client authenticated as a staff (worker) user."""
    user = User.objects.create_user(
        username='staffuser',
        email='staff@example.com',
        password='testpass123',
        role=User.Role.WORKER,
        first_name='Staff',
        last_name='User'
    )
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def manager_client(db):
    """Return API client authenticated as a manager user."""
    user = User.objects.create_user(
        username='manageruser',
        email='manager@example.com',
        password='testpass123',
        role=User.Role.MANAGER,
        first_name='Manager',
        last_name='User'
    )
    client = APIClient()
    client.force_authenticate(user=user)
    return client


# =============================================================================
# User Fixtures
# =============================================================================


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        role=User.Role.RESIDENT
    )


@pytest.fixture
def admin_user(db):
    """Create an admin user."""
    return User.objects.create_user(
        username='adminuser',
        email='admin@example.com',
        password='testpass123',
        role=User.Role.ADMIN,
        first_name='Admin',
        last_name='User'
    )


@pytest.fixture
def staff_user(db):
    """Create a staff user for employee tests."""
    return User.objects.create_user(
        username='staffuser',
        email='staff@example.com',
        password='testpass123',
        role=User.Role.WORKER,
        first_name='Staff',
        last_name='User'
    )


@pytest.fixture
def building(db):
    """Create a test building."""
    return Building.objects.create(
        name='Test Building',
        address='123 Test Street',
        city='Istanbul',
        district='Kadikoy',
        management_type=Building.ManagementType.SELF_MANAGED,
        annual_budget=100000
    )


@pytest.fixture
def apartment(db, building):
    """Create a test apartment."""
    return Apartment.objects.create(
        building=building,
        apartment_number='101',
        floor=1,
        block='A',
        square_meters=120.50,
        share_ratio_num=1,
        share_ratio_denom=100,
        tapu_number='1234567890',
        status=Apartment.Status.ACTIVE
    )


@pytest.fixture
def second_apartment(db, building):
    """Create a second test apartment."""
    return Apartment.objects.create(
        building=building,
        apartment_number='102',
        floor=1,
        block='A',
        square_meters=95.00,
        share_ratio_num=95,
        share_ratio_denom=10000,
        status=Apartment.Status.ACTIVE
    )


@pytest.fixture
def resident(db):
    """Create a test resident."""
    return Resident.objects.create(
        name='Test',
        surname='Resident',
        phone='+905551234567',
        email='resident@example.com',
        tc_kimlik_no='12345678901',
        owner_type=Resident.OwnerType.OWNER
    )


@pytest.fixture
def tenant_resident(db):
    """Create a tenant resident."""
    return Resident.objects.create(
        name='Test',
        surname='Tenant',
        phone='+905551234568',
        email='tenant@example.com',
        tc_kimlik_no='12345678902',
        owner_type=Resident.OwnerType.TENANT
    )


@pytest.fixture
def personal_account(db, apartment):
    """Create a personal account for an apartment."""
    return PersonalAccount.objects.create(
        apartment=apartment,
        account_number='ACC-001',
        balance=0
    )


@pytest.fixture
def ownership(db, resident, apartment):
    """Create an ownership record."""
    return Ownership.objects.create(
        resident=resident,
        apartment=apartment,
        role=Ownership.Role.OWNER,
        share_ratio_num=1,
        share_ratio_denom=1,
        is_primary=True
    )


@pytest.fixture
def department(db):
    """Create a test department."""
    return Department.objects.create(
        name='Maintenance',
        description='Building maintenance department'
    )


@pytest.fixture
def employee(db, staff_user, department):
    """Create a test employee."""
    return Employee.objects.create(
        user=staff_user,
        department=department,
        role=Employee.Role.MASTER,
        phone='+905551234569'
    )


@pytest.fixture
def notification_template(db):
    """Create a test notification template."""
    return NotificationTemplate.objects.create(
        name='Aidat Reminder',
        notification_type=NotificationTemplate.NotificationType.AIDAT_REMINDER,
        channel=NotificationTemplate.Channel.EMAIL,
        subject='Aidat Payment Reminder',
        body_template='Dear {name}, your aidat of {amount} is due.',
        is_active=True
    )


@pytest.fixture
def aidat_charge(db, apartment):
    """Create a test aidat charge."""
    start = date(2026, 1, 1)
    end = date(2026, 1, 31)
    return AidatCharge.objects.create(
        apartment=apartment,
        billing_period_start=start,
        billing_period_end=end,
        base_amount=500,
        late_fee_rate=0.001,
        due_date=end + timedelta(days=15),
        status=AidatCharge.Status.PENDING
    )


@pytest.fixture
def paid_aidat_charge(db, apartment):
    """Create a paid aidat charge."""
    start = date(2025, 12, 1)
    end = date(2025, 12, 31)
    paid_dt = timezone.now()
    return AidatCharge.objects.create(
        apartment=apartment,
        billing_period_start=start,
        billing_period_end=end,
        base_amount=500,
        late_fee_rate=0.001,
        due_date=end + timedelta(days=15),
        status=AidatCharge.Status.PAID,
        paid_at=paid_dt,
        paid_amount=500
    )


@pytest.fixture
def payment(db, apartment):
    """Create a test payment."""
    return Payment.objects.create(
        apartment=apartment,
        charge_type='aidat',
        amount=500,
        payment_method=Payment.PaymentMethod.EFT
    )
