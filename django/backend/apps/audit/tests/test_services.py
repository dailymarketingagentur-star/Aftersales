import pytest
from apps.audit.models import AuditEvent
from apps.audit.services import AuditService


@pytest.mark.django_db
class TestAuditService:
    def test_log_creates_event(self, user_factory, tenant_factory):
        user = user_factory()
        tenant = tenant_factory()
        event = AuditService.log(
            tenant=tenant,
            user=user,
            action="test.action",
            entity_type="test",
            entity_id="123",
            after={"key": "value"},
        )
        assert event.action == "test.action"
        assert event.entity_type == "test"
        assert event.tenant == tenant
        assert event.user == user
        assert AuditEvent.objects.count() == 1
