"""Data migration: Convert health_score from 0-100 scale to 7-35 scale."""

from django.db import migrations


def convert_scores_forward(apps, schema_editor):
    Client = apps.get_model("clients", "Client")
    for client in Client.objects.all():
        old = client.health_score
        if old > 35:
            client.health_score = max(7, min(35, round(old * 35 / 100)))
            client.save(update_fields=["health_score"])


def convert_scores_backward(apps, schema_editor):
    Client = apps.get_model("clients", "Client")
    for client in Client.objects.all():
        old = client.health_score
        if old <= 35:
            client.health_score = max(0, min(100, round(old * 100 / 35)))
            client.save(update_fields=["health_score"])


class Migration(migrations.Migration):

    dependencies = [
        ("clients", "0009_client_churn_warning_count_and_more"),
    ]

    operations = [
        migrations.RunPython(convert_scores_forward, convert_scores_backward),
    ]
