"""Tests for automatic audit logging via AuditLogMixin."""

import pytest

from apps.accounts.audit import AuditLogMixin
from apps.accounts.models import AuditAction, AuditLog
from apps.properties.models import Building

pytestmark = pytest.mark.django_db


class TestAuditLogMixin:
    """Tests that AuditLogMixin automatically logs DRF mutations."""

    def test_create_logs_audit_entry(self, admin_client, admin_user):
        """POST to a ModelViewSet should create an AuditLog with action='create'."""
        response = admin_client.post(
            "/api/v2/properties/buildings/",
            {
                "name": "Audit Tower",
                "address": "123 Test St",
                "city": "Istanbul",
                "district": "Kadikoy",
                "management_type": "self_managed",
            },
            format="json",
        )
        assert response.status_code == 201

        log = AuditLog.objects.filter(action=AuditAction.CREATE).last()
        assert log is not None
        assert log.user == admin_user
        assert log.content_object is not None
        assert log.content_object.name == "Audit Tower"
        assert log.ip_address is not None

    def test_update_logs_audit_entry_with_changes(self, admin_client, admin_user, building):
        """PATCH should create an AuditLog with action='update' and diff."""
        old_name = building.name
        response = admin_client.patch(
            f"/api/v2/properties/buildings/{building.id}/",
            {"name": "Renamed Building"},
            format="json",
        )
        assert response.status_code == 200

        log = AuditLog.objects.filter(action=AuditAction.UPDATE).last()
        assert log is not None
        assert log.user == admin_user
        assert log.content_object == building
        assert "name" in log.changes
        assert log.changes["name"]["old"] == old_name
        assert log.changes["name"]["new"] == "Renamed Building"

    def test_delete_logs_audit_entry(self, admin_client, admin_user, building):
        """DELETE should create an AuditLog with action='delete'."""
        building_id = building.id
        response = admin_client.delete(f"/api/v2/properties/buildings/{building.id}/")
        assert response.status_code == 204

        log = AuditLog.objects.filter(action=AuditAction.DELETE).last()
        assert log is not None
        assert log.user == admin_user
        assert log.object_id == building_id

    def test_list_does_not_create_audit_log(self, admin_client, building):
        """GET list should not create any audit entries."""
        before = AuditLog.objects.count()
        response = admin_client.get("/api/v2/properties/buildings/")
        assert response.status_code == 200
        assert AuditLog.objects.count() == before

    def test_retrieve_does_not_create_audit_log(self, admin_client, building):
        """GET retrieve should not create any audit entries."""
        before = AuditLog.objects.count()
        response = admin_client.get(f"/api/v2/properties/buildings/{building.id}/")
        assert response.status_code == 200
        assert AuditLog.objects.count() == before


class TestAuditLogMixinSensitiveFields:
    """Tests that sensitive fields are masked in audit logs."""

    def test_safe_changes_masks_sensitive_fields(self):
        """Fields in SENSITIVE_FIELDS should be replaced with '***'."""
        data = {
            "name": "Test Building",
            "address": "123 St",
            "tc_kimlik_no": "12345678901",
            "password": "secret123",
        }
        result = AuditLogMixin._safe_changes(data)
        assert result["name"] == "Test Building"
        assert result["address"] == "123 St"
        assert result["tc_kimlik_no"] == "***"
        assert result["password"] == "***"


class TestAuditLogMixinOptOut:
    """Tests that a ViewSet can disable audit logging."""

    def test_audit_enabled_false_skips_logging(self, admin_client, admin_user):
        """A ViewSet with audit_enabled=False should not log mutations."""

        # We don't have an existing opt-out ViewSet, so we test the mixin directly.
        class DummySerializer:
            validated_data = {"name": "X"}

            def save(self, **kwargs):
                return Building.objects.create(name="X", address="Y")

        class DummyViewSet(AuditLogMixin):
            audit_enabled = False
            request = type("R", (), {"user": admin_user, "META": {}})()

        viewset = DummyViewSet()
        before = AuditLog.objects.count()
        viewset.perform_create(DummySerializer())
        assert AuditLog.objects.count() == before
