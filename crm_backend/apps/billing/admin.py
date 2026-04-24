"""Admin configuration for billing app."""
from django.contrib import admin
from django.utils import timezone

from .models import AidatCharge, ExtraordinaryCharge, Payment, Receipt


@admin.action(description='Mark selected charges as paid')
def mark_paid(modeladmin, request, queryset):
    queryset.update(status=AidatCharge.Status.PAID, paid_at=timezone.now())


@admin.action(description='Mark selected charges as overdue')
def mark_overdue(modeladmin, request, queryset):
    queryset.update(status=AidatCharge.Status.OVERDUE)


@admin.register(AidatCharge)
class AidatChargeAdmin(admin.ModelAdmin):
    list_display = ['apartment', 'billing_period_start', 'billing_period_end', 'base_amount', 'status', 'due_date']
    list_filter = ['status', 'billing_period_start']
    search_fields = ['apartment__apartment_number', 'apartment__building__name']
    date_hierarchy = 'billing_period_start'
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['apartment']
    actions = [mark_paid, mark_overdue]


@admin.register(ExtraordinaryCharge)
class ExtraordinaryChargeAdmin(admin.ModelAdmin):
    list_display = ['description', 'building', 'total_amount', 'status', 'due_date', 'approval_date']
    list_filter = ['status', 'building']
    search_fields = ['description', 'building__name']
    date_hierarchy = 'approval_date'
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['building']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['receipt_number', 'apartment', 'amount', 'payment_method', 'paid_at']
    list_filter = ['payment_method', 'paid_at']
    search_fields = ['receipt_number', 'bank_reference', 'apartment__apartment_number']
    date_hierarchy = 'paid_at'
    readonly_fields = ['created_at']
    raw_id_fields = ['apartment']


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ['payment', 'pdf_url', 'generated_at']
    search_fields = ['payment__receipt_number']
    readonly_fields = ['generated_at']
