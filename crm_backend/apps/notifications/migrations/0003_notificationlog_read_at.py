# Generated migration for adding read_at field to NotificationLog.
# Enables tracking when notifications were read by recipients for unread badge feature.

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("notifications", "0002_add_model_ordering"),
    ]

    operations = [
        migrations.AddField(
            model_name="notificationlog",
            name="read_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text="Timestamp when the notification was read by the recipient",
                db_index=True,
            ),
        ),
    ]
