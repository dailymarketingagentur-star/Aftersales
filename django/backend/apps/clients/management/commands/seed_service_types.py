from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Seed default service types for all tenants that don't have them yet."

    def handle(self, *args, **options):
        from apps.clients.services import ServiceTypeService
        from apps.tenants.models import Tenant

        tenants = Tenant.objects.filter(is_active=True)
        total_created = 0

        for tenant in tenants:
            created = ServiceTypeService.seed_defaults(tenant)
            total_created += created
            if created:
                self.stdout.write(f"  {tenant.name}: {created} Service-Typen erstellt")

        self.stdout.write(self.style.SUCCESS(f"Fertig: {total_created} Service-Typen insgesamt erstellt."))
