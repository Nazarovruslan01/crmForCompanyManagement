"""Tests for billing endpoints."""
import pytest
from rest_framework import status

from apps.billing.models import AidatCharge

pytestmark = pytest.mark.django_db


class TestAidatChargeViewSet:
    """Tests for /api/v2/billing/aidat-charges/ endpoints."""

    def test_list_aidat_charges(self, admin_client, aidat_charge):
        """Admin can list aidat charges."""
        response = admin_client.get('/api/v2/billing/aidat-charges/')
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data

    def test_list_aidat_charges_unauthenticated(self, api_client):
        """Unauthenticated request returns 401."""
        response = api_client.get('/api/v2/billing/aidat-charges/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_aidat_charge(self, admin_client, apartment):
        """Admin can create an aidat charge."""
        payload = {
            'apartment': apartment.id,
            'billing_period_start': '2026-02-01',
            'billing_period_end': '2026-02-28',
            'base_amount': 600,
            'late_fee_rate': 0.001,
            'due_date': '2026-03-15',
            'status': 'pending',
        }
        response = admin_client.post('/api/v2/billing/aidat-charges/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert float(response.data['base_amount']) == 600

    def test_retrieve_aidat_charge(self, admin_client, aidat_charge):
        """Admin can retrieve a specific aidat charge."""
        response = admin_client.get(f'/api/v2/billing/aidat-charges/{aidat_charge.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert float(response.data['base_amount']) == 500

    def test_update_aidat_charge(self, admin_client, aidat_charge):
        """Admin can update an aidat charge."""
        payload = {'base_amount': 750}
        response = admin_client.patch(f'/api/v2/billing/aidat-charges/{aidat_charge.id}/', payload, format='json')
        assert response.status_code == status.HTTP_200_OK
        aidat_charge.refresh_from_db()
        assert float(aidat_charge.base_amount) == 750

    def test_delete_aidat_charge(self, admin_client, aidat_charge):
        """Admin can delete an aidat charge."""
        response = admin_client.delete(f'/api/v2/billing/aidat-charges/{aidat_charge.id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_filter_aidat_charges_by_status(self, admin_client, aidat_charge):
        """Admin can filter aidat charges by status."""
        response = admin_client.get('/api/v2/billing/aidat-charges/', {'status': 'pending'})
        assert response.status_code == status.HTTP_200_OK

    def test_filter_aidat_charges_by_apartment(self, admin_client, apartment, aidat_charge):
        """Admin can filter aidat charges by apartment."""
        response = admin_client.get('/api/v2/billing/aidat-charges/', {'apartment': apartment.id})
        assert response.status_code == status.HTTP_200_OK

    def test_overdue_action(self, admin_client, apartment):
        """Admin can get overdue charges via action."""
        from datetime import date, timedelta


        # Create an overdue charge
        start = date(2025, 12, 1)
        end = date(2025, 12, 31)
        AidatCharge.objects.create(
            apartment=apartment,
            billing_period_start=start,
            billing_period_end=end,
            base_amount=500,
            late_fee_rate=0.001,
            due_date=end - timedelta(days=1),
            status=AidatCharge.Status.OVERDUE,
        )
        response = admin_client.get('/api/v2/billing/aidat-charges/overdue/')
        assert response.status_code == status.HTTP_200_OK


class TestExtraordinaryChargeViewSet:
    """Tests for /api/v2/billing/extraordinary-charges/ endpoints."""

    def test_list_extraordinary_charges(self, admin_client, building):
        """Admin can list extraordinary charges."""
        from apps.billing.models import ExtraordinaryCharge
        ExtraordinaryCharge.objects.create(
            building=building,
            description='Test extraordinary charge',
            total_amount=10000,
        )
        response = admin_client.get('/api/v2/billing/extraordinary-charges/')
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data

    def test_list_extraordinary_charges_unauthenticated(self, api_client):
        """Unauthenticated request returns 401."""
        response = api_client.get('/api/v2/billing/extraordinary-charges/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_extraordinary_charge(self, admin_client, building):
        """Admin can create an extraordinary charge."""
        payload = {
            'building': building.id,
            'description': 'New extraordinary charge',
            'total_amount': 15000,
        }
        response = admin_client.post('/api/v2/billing/extraordinary-charges/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED


class TestPaymentViewSet:
    """Tests for /api/v2/billing/payments/ endpoints."""

    def test_list_payments(self, admin_client, payment):
        """Admin can list payments."""
        response = admin_client.get('/api/v2/billing/payments/')
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data

    def test_list_payments_unauthenticated(self, api_client):
        """Unauthenticated request returns 401."""
        response = api_client.get('/api/v2/billing/payments/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_payment(self, admin_client, apartment):
        """Admin can create a payment."""
        payload = {
            'apartment': apartment.id,
            'charge_type': 'aidat',
            'amount': 600,
            'payment_method': 'eft',
        }
        response = admin_client.post('/api/v2/billing/payments/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_filter_payments_by_payment_method(self, admin_client, payment):
        """Admin can filter payments by payment method."""
        response = admin_client.get('/api/v2/billing/payments/', {'payment_method': 'eft'})
        assert response.status_code == status.HTTP_200_OK


class TestReceiptViewSet:
    """Tests for /api/v2/billing/receipts/ endpoints."""

    def test_list_receipts(self, admin_client, payment):
        """Admin can list receipts."""
        from apps.billing.models import Receipt
        Receipt.objects.create(
            payment=payment,
            receipt_number='RCP-001',
            issued_to='Test',
        )
        response = admin_client.get('/api/v2/billing/receipts/')
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data

    def test_list_receipts_unauthenticated(self, api_client):
        """Unauthenticated request returns 401."""
        response = api_client.get('/api/v2/billing/receipts/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_receipt(self, admin_client, payment):
        """Admin can create a receipt."""
        payload = {
            'payment': payment.id,
            'receipt_number': 'RCP-NEW-001',
            'issued_to': 'New Recipient',
        }
        response = admin_client.post('/api/v2/billing/receipts/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
