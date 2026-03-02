from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("billing", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tenantsubscription",
            name="status",
            field=models.CharField(
                choices=[
                    ("active", "Active"),
                    ("trialing", "Trialing"),
                    ("free", "Free"),
                    ("past_due", "Past Due"),
                    ("canceled", "Canceled"),
                    ("incomplete", "Incomplete"),
                    ("none", "No Subscription"),
                ],
                default="none",
                max_length=20,
            ),
        ),
    ]
