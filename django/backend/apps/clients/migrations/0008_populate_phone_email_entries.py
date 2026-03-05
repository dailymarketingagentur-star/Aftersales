"""Data migration: Copy existing contact_phone/contact_email into the new related models."""

from django.db import migrations


def forwards(apps, schema_editor):
    Client = apps.get_model("clients", "Client")
    ClientPhoneNumber = apps.get_model("clients", "ClientPhoneNumber")
    ClientEmailAddress = apps.get_model("clients", "ClientEmailAddress")

    for client in Client.objects.all():
        if client.contact_phone:
            ClientPhoneNumber.objects.create(
                tenant=client.tenant,
                client=client,
                label="Hauptnummer",
                number=client.contact_phone,
                position=0,
            )
        if client.contact_email:
            ClientEmailAddress.objects.create(
                tenant=client.tenant,
                client=client,
                label="Hauptadresse",
                email=client.contact_email,
                position=0,
            )


def backwards(apps, schema_editor):
    Client = apps.get_model("clients", "Client")
    ClientPhoneNumber = apps.get_model("clients", "ClientPhoneNumber")
    ClientEmailAddress = apps.get_model("clients", "ClientEmailAddress")

    for client in Client.objects.all():
        first_phone = ClientPhoneNumber.objects.filter(client=client).order_by("position", "created_at").first()
        if first_phone:
            client.contact_phone = first_phone.number
        first_email = ClientEmailAddress.objects.filter(client=client).order_by("position", "created_at").first()
        if first_email:
            client.contact_email = first_email.email
        client.save(update_fields=["contact_phone", "contact_email"])

    ClientPhoneNumber.objects.all().delete()
    ClientEmailAddress.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("clients", "0007_clientemailaddress_clientphonenumber"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
