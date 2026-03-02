from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.clients.models import Service


@receiver(post_save, sender=Service)
def recalculate_client_volume_on_save(sender, instance, **kwargs):
    """Recalculate client monthly_volume when a service is saved."""
    instance.client.recalculate_volume()


@receiver(post_delete, sender=Service)
def recalculate_client_volume_on_delete(sender, instance, **kwargs):
    """Recalculate client monthly_volume when a service is deleted."""
    instance.client.recalculate_volume()
