"""Generate test data for CRM frontend testing."""
import os
import sys
import random
from decimal import Decimal
from datetime import datetime, timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'crm_backend'))

import django
django.setup()

from django.utils import timezone
from apps.accounts.models import User
from apps.properties.models import Building, Apartment
from apps.residents.models import Resident, Ownership, PersonalAccount
from apps.staff.models import Department, Employee
from apps.tickets.models import Ticket, TicketComment
from apps.billing.models import AidatCharge, Payment
from apps.notifications.models import NotificationLog, NotificationTemplate

random.seed(42)

# ─── Clean existing test data (soft delete) ──────────────────────────────
print("Cleaning existing data...")
TicketComment.objects.all().delete()
Ticket.objects.all().delete()
AidatCharge.objects.all().delete()
Payment.objects.all().delete()
NotificationLog.objects.all().delete()
Ownership.objects.all().delete()
PersonalAccount.objects.all().delete()
Resident.objects.filter(user__username__in=['resident', 'ahmet', 'mehmet', 'ayse', 'fatma']).delete()
Employee.objects.filter(user__username__in=['manager', 'worker']).delete()
Department.objects.filter(name__in=['Yönetim', 'Teknik', 'Muhasebe', 'Temizlik']).delete()
Apartment.objects.filter(building__name__in=['Palmiye Sitesi', 'Cennet Apartmanı', 'Deniz Vadi']).delete()
Building.objects.filter(name__in=['Palmiye Sitesi', 'Cennet Apartmanı', 'Deniz Vadi']).delete()
User.objects.filter(username__in=['ahmet', 'mehmet', 'ayse', 'fatma', 'ali', 'veli']).delete()

# ─── Create Buildings ────────────────────────────────────────────────────
print("Creating buildings...")
buildings_data = [
    {"name": "Palmiye Sitesi", "address": "Saray Mah. Palmiye Cad. No:1", "city": "Alanya", "district": "Kestel", "management_type": "self_managed", "annual_budget": Decimal("500000")},
    {"name": "Cennet Apartmanı", "address": "Mahmutlar Mah. Cennet Sok. No:5", "city": "Alanya", "district": "Mahmutlar", "management_type": "external_company", "annual_budget": Decimal("300000")},
    {"name": "Deniz Vadi", "address": "Oba Mah. Deniz Cad. No:10", "city": "Alanya", "district": "Oba", "management_type": "self_managed", "annual_budget": Decimal("750000")},
]
buildings = []
for data in buildings_data:
    b = Building.objects.create(**data)
    buildings.append(b)
    print(f"  Created: {b.name}")

# ─── Create Apartments ───────────────────────────────────────────────────
print("Creating apartments...")
apartments = []
for building in buildings:
    for floor in range(1, 6):
        for unit in range(1, 5):
            apt = Apartment.objects.create(
                building=building,
                apartment_number=f"{floor}{unit:02d}",
                floor=floor,
                block="A" if building.id % 2 == 0 else "B",
                square_meters=Decimal(str(random.randint(80, 150))),
                share_ratio_num=1,
                share_ratio_denom=20,
                tapu_number=f"{building.id}{floor}{unit:02d}2024",
                status="active",
            )
            apartments.append(apt)
print(f"  Created {len(apartments)} apartments")

# ─── Create Departments ──────────────────────────────────────────────────
print("Creating departments...")
dept_names = [
    ("Yönetim", "Site yönetimi ve idari işler"),
    ("Teknik", "Teknik bakım ve onarım işleri"),
    ("Muhasebe", "Finans ve muhasebe işlemleri"),
    ("Temizlik", "Temizlik ve hijyen hizmetleri"),
]
departments_list = []
for name, desc in dept_names:
    d = Department.objects.create(name=name, description=desc)
    departments_list.append(d)
    print(f"  Created: {d.name}")

# ─── Create Employees ────────────────────────────────────────────────────
print("Creating employees...")
manager_user = User.objects.get(username='manager')
worker_user = User.objects.get(username='worker')

manager_emp, _ = Employee.objects.get_or_create(
    user=manager_user,
    defaults={
        "department": departments_list[0],
        "role": "admin",
        "phone": "+90 555 111 2233",
        "is_active": True,
    }
)

worker_emp, _ = Employee.objects.get_or_create(
    user=worker_user,
    defaults={
        "department": departments_list[1],
        "role": "master",
        "phone": "+90 555 222 3344",
        "is_active": True,
    }
)

# Extra employees
extra_users = [
    {"username": "teknikci", "first_name": "Ali", "last_name": "Yılmaz", "role": "worker"},
    {"username": "muhasebe", "first_name": "Ayşe", "last_name": "Kaya", "role": "worker"},
    {"username": "temizlikci", "first_name": "Mehmet", "last_name": "Şahin", "role": "worker"},
]
for u_data in extra_users:
    u, _ = User.objects.get_or_create(
        username=u_data["username"],
        defaults={
            "email": f"{u_data['username']}@test.com",
            "first_name": u_data["first_name"],
            "last_name": u_data["last_name"],
            "role": u_data["role"],
            "is_active": True,
        }
    )
    u.set_password("test123456")
    u.save()
    role_map = {"admin": "admin", "manager": "admin", "worker": "master"}
    Employee.objects.create(
        user=u,
        department=departments_list[random.randint(0, len(departments_list)-1)],
        role=role_map.get(u_data["role"], "master"),
        phone=f"+90 555 {random.randint(100,999)} {random.randint(1000,9999)}",
        is_active=True,
    )
    print(f"  Created employee: {u.username}")

print(f"  Total employees: {Employee.objects.count()}")

# ─── Create Residents ────────────────────────────────────────────────────
print("Creating residents...")
resident_users_data = [
    {"username": "resident", "name": "Fatma", "surname": "Demir", "tc": "12345678901"},
    {"username": "ahmet", "name": "Ahmet", "surname": "Kaya", "tc": "23456789012"},
    {"username": "mehmet", "name": "Mehmet", "surname": "Yılmaz", "tc": "34567890123"},
    {"username": "ayse", "name": "Ayşe", "surname": "Şahin", "tc": "45678901234"},
    {"username": "fatma2", "name": "Fatma", "surname": "Özdemir", "tc": "56789012345"},
    {"username": "ali", "name": "Ali", "surname": "Can", "tc": "67890123456"},
    {"username": "veli", "name": "Veli", "surname": "Korkmaz", "tc": "78901234567"},
]
residents = []
for i, r_data in enumerate(resident_users_data):
    if r_data["username"] == "resident":
        u = User.objects.get(username="resident")
    else:
        u, _ = User.objects.get_or_create(
            username=r_data["username"],
            defaults={
                "email": f"{r_data['username']}@test.com",
                "first_name": r_data["name"],
                "last_name": r_data["surname"],
                "role": "resident",
                "is_active": True,
            }
        )
        u.set_password("resident123")
        u.save()

    r = Resident.objects.create(
        user=u if r_data["username"] == "resident" else u,
        tc_kimlik_no=r_data["tc"],
        name=r_data["name"],
        surname=r_data["surname"],
        phone=f"+90 555 {random.randint(100,999)} {random.randint(1000,9999)}",
        email=f"{r_data['username']}@test.com",
        owner_type="owner" if i < 5 else "tenant",
        is_active=True,
    )
    residents.append(r)
    print(f"  Created resident: {r.full_name}")

# ─── Create Ownerships ───────────────────────────────────────────────────
print("Creating ownerships...")
for i, resident in enumerate(residents):
    apt = apartments[i % len(apartments)]
    Ownership.objects.create(
        resident=resident,
        apartment=apt,
        role="owner" if resident.owner_type == "owner" else "tenant",
        is_primary=True,
        share_ratio_num=1,
        share_ratio_denom=20,
    )
print(f"  Created {Ownership.objects.count()} ownerships")

# ─── Create Personal Accounts ────────────────────────────────────────────
print("Creating personal accounts...")
for apt in apartments[:10]:
    if not hasattr(apt, 'personal_account'):
        PersonalAccount.objects.create(
            apartment=apt,
            account_number=f"ACC-{apt.building.id}-{apt.apartment_number}",
            balance=Decimal(str(random.randint(-5000, 10000))),
            is_active=True,
        )
print(f"  Created {PersonalAccount.objects.count()} personal accounts")

# ─── Create Tickets ──────────────────────────────────────────────────────
print("Creating tickets...")
categories = ["plumbing", "electrical", "cleaning", "security", "noise", "general"]
priorities = ["low", "medium", "high", "urgent"]
statuses = ["new", "assigned", "in_progress", "resolved", "closed"]
titles = [
    ("Su kaçağı var", "plumbing"),
    ("Elektrik kesintisi", "electrical"),
    ("Asansör arızalı", "general"),
    ("Gürültü şikayeti", "noise"),
    ("Temizlik yapılmamış", "cleaning"),
    ("Kapı kilidi bozuk", "security"),
    ("Sıcak su yok", "plumbing"),
    ("Internet bağlantısı yok", "electrical"),
]

for i in range(15):
    title, cat = titles[i % len(titles)]
    status = statuses[i % len(statuses)]
    apt = apartments[i % len(apartments)]
    t = Ticket.objects.create(
        apartment=apt,
        category=cat,
        priority=priorities[i % len(priorities)],
        status=status,
        title=title,
        description=f"{title} - lütfen acil müdahale edin. Apartman: {apt.building.name} Daire: {apt.apartment_number}",
        assigned_worker=worker_emp if status in ["assigned", "in_progress", "resolved", "closed"] else None,
        created_by=manager_user,
        resolved_at=timezone.now() - timedelta(days=random.randint(1, 10)) if status == "resolved" else None,
    )

    # Add comments
    if i % 3 == 0:
        TicketComment.objects.create(
            ticket=t,
            author=manager_user,
            content="Konu inceleniyor, en kısa sürede çözülecek.",
        )
    if i % 5 == 0:
        TicketComment.objects.create(
            ticket=t,
            author=worker_user,
            content="Tamir tamamlandı, kontrol edebilirsiniz.",
        )

print(f"  Created {Ticket.objects.count()} tickets")

# ─── Create Aidat Charges ────────────────────────────────────────────────
print("Creating aidat charges...")
for apt in apartments[:15]:
    for month in range(1, 4):
        start = datetime(2026, month, 1).date()
        end = datetime(2026, month, 28).date()
        due = datetime(2026, month, 15).date()
        AidatCharge.objects.create(
            apartment=apt,
            billing_period_start=start,
            billing_period_end=end,
            base_amount=Decimal(str(random.choice([500, 750, 1000]))),
            due_date=due,
            status=random.choice(["pending", "paid", "overdue"]),
        )
print(f"  Created {AidatCharge.objects.count()} aidat charges")

# ─── Create Payments ───────────────────────────────────────────────────────
print("Creating payments...")
payment_methods = ["eft", "credit_card", "cash", "online"]
for i in range(10):
    apt = apartments[i % len(apartments)]
    Payment.objects.create(
        apartment=apt,
        charge_type="aidat",
        amount=Decimal(str(random.choice([500, 750, 1000]))),
        payment_method=random.choice(payment_methods),
        currency="TRY",
        receipt_number=f"RCP-{2026}{i+1:04d}",
        paid_at=timezone.now() - timedelta(days=random.randint(1, 30)),
        bank_reference=f"REF-{i+1:06d}",
    )
print(f"  Created {Payment.objects.count()} payments")

# ─── Create Notification Logs ────────────────────────────────────────────
print("Creating notification logs...")
channels = ["email", "sms", "telegram", "whatsapp"]
notification_statuses = ["pending", "sent", "delivered", "failed"]

# Create template first
template, _ = NotificationTemplate.objects.get_or_create(
    name="Aidat Hatırlatma",
    defaults={
        "channel": "email",
        "notification_type": "aidat_reminder",
        "subject": "Aidat Ödeme Hatırlatması",
        "body_template": "Sayın {name}, aidat ödemeniz hatırlatılır.",
        "is_active": True,
    }
)

for i in range(20):
    resident = residents[i % len(residents)]
    status = random.choice(notification_statuses)
    nl = NotificationLog.objects.create(
        recipient=resident,
        template=template,
        channel=random.choice(channels),
        subject="Aidat Hatırlatma" if i % 2 == 0 else "Genel Duyuru",
        status=status,
        sent_at=timezone.now() - timedelta(hours=random.randint(1, 48)) if status in ["sent", "delivered", "failed"] else None,
        delivered_at=timezone.now() - timedelta(hours=random.randint(1, 24)) if status == "delivered" else None,
        error_message="SMTP timeout" if status == "failed" and i % 3 == 0 else None,
    )
print(f"  Created {NotificationLog.objects.count()} notification logs")

print("\n✅ Test data generation complete!")
print(f"   Buildings: {Building.objects.count()}")
print(f"   Apartments: {Apartment.objects.count()}")
print(f"   Employees: {Employee.objects.count()}")
print(f"   Residents: {Resident.objects.count()}")
print(f"   Tickets: {Ticket.objects.count()}")
print(f"   Aidat Charges: {AidatCharge.objects.count()}")
print(f"   Payments: {Payment.objects.count()}")
print(f"   Notifications: {NotificationLog.objects.count()}")
