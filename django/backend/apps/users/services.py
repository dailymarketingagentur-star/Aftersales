import structlog
from django.db import transaction

logger = structlog.get_logger()


class UserService:
    @staticmethod
    @transaction.atomic
    def invite_member(tenant, email, role, invited_by):
        """Invite a user to a tenant. Creates user if needed."""
        from apps.users.models import Membership, User
        from apps.audit.services import AuditService

        user, created = User.objects.get_or_create(
            email=email,
            defaults={"first_name": "", "last_name": ""},
        )

        if created:
            user.set_unusable_password()
            user.save()

        membership, mem_created = Membership.objects.get_or_create(
            user=user,
            tenant=tenant,
            defaults={"role": role, "invited_by": invited_by},
        )

        if not mem_created:
            if not membership.is_active:
                membership.is_active = True
                membership.role = role
                membership.save()
            else:
                return None  # Already active member

        AuditService.log(
            tenant=tenant,
            user=invited_by,
            action="member.invited",
            entity_type="membership",
            entity_id=str(membership.id),
            after={"email": email, "role": role},
        )

        # Send invite email via central email service
        from apps.emails.services import EmailService
        from django.conf import settings

        EmailService.send(
            tenant=tenant,
            template_slug="team-invite",
            recipient_email=email,
            context={
                "INVITED_BY": invited_by.full_name or invited_by.email,
                "TENANT_NAME": tenant.name,
                "INVITE_URL": f"{settings.FRONTEND_URL}/login",
            },
            idempotency_key=f"invite-{tenant.id}-{email}",
        )

        logger.info("member_invited", tenant_id=str(tenant.id), email=email, role=role)
        return membership

    @staticmethod
    @transaction.atomic
    def change_role(membership, new_role, changed_by):
        """Change a member's role."""
        from apps.audit.services import AuditService

        old_role = membership.role
        membership.role = new_role
        membership.save()

        AuditService.log(
            tenant=membership.tenant,
            user=changed_by,
            action="member.role_changed",
            entity_type="membership",
            entity_id=str(membership.id),
            before={"role": old_role},
            after={"role": new_role},
        )

        return membership

    @staticmethod
    @transaction.atomic
    def remove_member(membership, removed_by):
        """Deactivate a membership."""
        from apps.audit.services import AuditService

        membership.is_active = False
        membership.save()

        AuditService.log(
            tenant=membership.tenant,
            user=removed_by,
            action="member.removed",
            entity_type="membership",
            entity_id=str(membership.id),
            after={"email": membership.user.email},
        )

        return membership
