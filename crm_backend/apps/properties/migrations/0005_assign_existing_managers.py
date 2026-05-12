"""Assign existing manager-role users to all buildings.

Preserves current behavior where managers see everything.
Without this, all managers would lose access to all buildings
after adding the M2M field.
"""

from django.db import migrations


def assign_existing_managers_to_all_buildings(apps, schema_editor):
    Building = apps.get_model("properties", "Building")
    User = apps.get_model("accounts", "User")
    managers = User.objects.filter(role="manager")
    if not managers.exists() or not Building.objects.exists():
        return
    for building in Building.objects.iterator():
        building.managers.set(managers)


class Migration(migrations.Migration):
    dependencies = [
        ("properties", "0004_add_building_managers"),
    ]

    operations = [
        migrations.RunPython(
            assign_existing_managers_to_all_buildings,
            migrations.RunPython.noop,
        ),
    ]
