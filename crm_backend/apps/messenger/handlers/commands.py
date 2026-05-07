"""Simple command handlers: /start, /help, /balance, unknown commands."""

from decimal import Decimal

from apps.messenger.handlers._send import send_telegram_message
from apps.messenger.models import MessengerUser


def _get_resident_debt_lines(messenger_user: MessengerUser) -> tuple[str, Decimal, int]:
    """Calculate pending/overdue charges for a resident and return message lines.

    Returns (message_text, total_due, months_count).
    """
    from apps.billing.models import AidatCharge
    from apps.residents.models import Ownership

    assert messenger_user.resident is not None
    apartments = Ownership.objects.filter(resident=messenger_user.resident).values_list("apartment_id", flat=True)

    charges = (
        AidatCharge.objects.filter(
            apartment_id__in=apartments,
            status__in=[AidatCharge.Status.PENDING, AidatCharge.Status.OVERDUE],
        )
        .select_related("apartment", "apartment__building")
        .order_by("billing_period_start")
    )

    if not charges.exists():
        return (
            "✅ You have no outstanding payments.\n\nThank you for staying up to date!",
            Decimal("0"),
            0,
        )

    lines: list[str] = ["💳 Your Balance Summary\n"]
    total_due = Decimal("0")
    months_count = charges.count()

    for charge in charges:
        total = charge.total_due
        total_due += total
        status_icon = "🔴" if charge.status == AidatCharge.Status.OVERDUE else "🟡"
        lines.append(
            f"\n🏢 {charge.apartment.building.name} - Apt {charge.apartment.apartment_number}\n"
            f"{status_icon} {charge.billing_period_start.strftime('%B %Y')}: {total:.2f} TRY\n"
            f"   Due: {charge.due_date.strftime('%d.%m.%Y')}"
        )

    lines.append(f"\n{'─' * 28}")
    lines.append(f"💰 Total Due: {total_due:.2f} TRY")
    lines.append(f"📅 Unpaid months: {months_count}")
    lines.append("\nPlease make your payment as soon as possible.")

    return "\n".join(lines), total_due, months_count


def send_balance(messenger_user: MessengerUser) -> None:
    """Send current balance/debt summary to a resident."""
    if not messenger_user.resident:
        send_telegram_message(
            messenger_user.telegram_chat_id,
            "Please complete registration first with /register to view your balance.",
        )
        return

    message_text, _, _ = _get_resident_debt_lines(messenger_user)
    send_telegram_message(messenger_user.telegram_chat_id, message_text)


def send_welcome(messenger_user: MessengerUser) -> None:
    welcome_text = (
        "Welcome to the Building Management CRM bot! 🏢\n\n"
        "I can help you with:\n"
        "• Register as a resident (/register)\n"
        "• Create maintenance tickets\n"
        "• Check your balance\n"
        "• Chat with the management\n\n"
        "Use /help to see all available commands."
    )
    send_telegram_message(messenger_user.telegram_chat_id, welcome_text)


def send_help(messenger_user: MessengerUser) -> None:
    help_text = (
        "Available commands:\n\n"
        "/start - Welcome message\n"
        "/register - Register as a resident\n"
        "/ticket - Create a maintenance ticket\n"
        "/balance - Check your outstanding payments\n"
        "/cancel - Cancel current registration\n"
        "/help - This help message"
    )
    send_telegram_message(messenger_user.telegram_chat_id, help_text)


def send_unknown_command(messenger_user: MessengerUser) -> None:
    send_telegram_message(
        messenger_user.telegram_chat_id,
        "Unknown command. Use /help to see available commands.",
    )
