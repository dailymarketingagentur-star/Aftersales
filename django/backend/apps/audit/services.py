import structlog

logger = structlog.get_logger()


class AuditService:
    @staticmethod
    def log(tenant, user, action, entity_type, entity_id="", before=None, after=None, request=None):
        """Create an audit log entry."""
        from apps.audit.models import AuditEvent

        ip_address = None
        user_agent = ""

        if request:
            ip_address = getattr(request, "client_ip", None)
            user_agent = getattr(request, "user_agent", "")

        event = AuditEvent.objects.create(
            tenant=tenant,
            user=user,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            before=before,
            after=after,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        logger.info(
            "audit_event",
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            tenant_id=str(tenant.id),
        )
        return event
