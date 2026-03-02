"""Service for copying integration configurations between tenants."""

from __future__ import annotations

import structlog
from django.db import transaction

from apps.audit.services import AuditService
from apps.emails.models import EmailProviderConnection
from apps.integrations.models import ActionTemplate, JiraConnection
from apps.users.models import Membership

logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# Copy functions — one per integration type
# ---------------------------------------------------------------------------


def _copy_email_provider(source_tenant, target_tenant, overwrite: bool) -> tuple[list[str], list[str], list[str]]:
    """Copy EmailProviderConnections (SMTP / SendGrid) from source to target.

    Copied providers are always is_active=False — the user must activate manually
    because the sender address may differ between tenants.
    """
    copied: list[str] = []
    skipped: list[str] = []
    errors: list[str] = []

    source_providers = EmailProviderConnection.objects.filter(tenant=source_tenant)
    if not source_providers.exists():
        skipped.append("email_provider: Keine Provider im Quell-Mandanten")
        return copied, skipped, errors

    for provider in source_providers:
        existing = EmailProviderConnection.objects.filter(
            tenant=target_tenant, provider_type=provider.provider_type
        ).first()

        if existing and not overwrite:
            skipped.append(f"email_provider ({provider.provider_type}): Existiert bereits")
            continue

        if existing and overwrite:
            existing.delete()

        new_provider = EmailProviderConnection(
            tenant=target_tenant,
            provider_type=provider.provider_type,
            label=provider.label,
            is_active=False,
            smtp_host=provider.smtp_host,
            smtp_port=provider.smtp_port,
            smtp_username=provider.smtp_username,
            smtp_use_tls=provider.smtp_use_tls,
            from_email=provider.from_email,
            from_name=provider.from_name,
        )

        # Copy encrypted secrets via decrypt → re-encrypt
        if provider.provider_type == "smtp" and provider.smtp_password_encrypted:
            new_provider.set_smtp_password(provider.get_smtp_password())
        if provider.provider_type == "sendgrid" and provider.sendgrid_api_key_encrypted:
            new_provider.set_sendgrid_api_key(provider.get_sendgrid_api_key())

        new_provider.save()
        copied.append(f"email_provider ({provider.provider_type})")

    return copied, skipped, errors


def _copy_jira_connection(source_tenant, target_tenant, overwrite: bool) -> tuple[list[str], list[str], list[str]]:
    """Copy JiraConnection from source to target.

    New connection is is_active=True. With overwrite=True, existing active
    connections are deactivated first (due to unique constraint).
    """
    copied: list[str] = []
    skipped: list[str] = []
    errors: list[str] = []

    source_conn = JiraConnection.objects.filter(tenant=source_tenant, is_active=True).first()
    if not source_conn:
        skipped.append("jira_connection: Keine aktive Verbindung im Quell-Mandanten")
        return copied, skipped, errors

    existing = JiraConnection.objects.filter(tenant=target_tenant, is_active=True).first()
    if existing and not overwrite:
        skipped.append("jira_connection: Existiert bereits")
        return copied, skipped, errors

    if existing and overwrite:
        existing.is_active = False
        existing.save(update_fields=["is_active"])

    new_conn = JiraConnection(
        tenant=target_tenant,
        label=source_conn.label,
        jira_url=source_conn.jira_url,
        jira_email=source_conn.jira_email,
        config=source_conn.config,
        is_active=True,
    )
    new_conn.set_token(source_conn.get_token())
    new_conn.save()
    copied.append("jira_connection")

    return copied, skipped, errors


def _copy_action_templates(source_tenant, target_tenant, overwrite: bool) -> tuple[list[str], list[str], list[str]]:
    """Copy tenant-specific ActionTemplates (not system) from source to target.

    Conflict detection via slug (unique_together(tenant, slug)).
    Copied templates are always is_system=False.
    """
    copied: list[str] = []
    skipped: list[str] = []
    errors: list[str] = []

    source_templates = ActionTemplate.objects.filter(tenant=source_tenant, is_system=False)
    if not source_templates.exists():
        skipped.append("action_templates: Keine Vorlagen im Quell-Mandanten")
        return copied, skipped, errors

    for tmpl in source_templates:
        existing = ActionTemplate.objects.filter(tenant=target_tenant, slug=tmpl.slug).first()

        if existing and not overwrite:
            skipped.append(f"action_templates ({tmpl.slug}): Existiert bereits")
            continue

        if existing and overwrite:
            existing.delete()

        ActionTemplate.objects.create(
            tenant=target_tenant,
            slug=tmpl.slug,
            name=tmpl.name,
            description=tmpl.description,
            method=tmpl.method,
            endpoint=tmpl.endpoint,
            body_json=tmpl.body_json,
            headers_json=tmpl.headers_json,
            variables=tmpl.variables,
            output_mapping=tmpl.output_mapping,
            is_active=tmpl.is_active,
            is_system=False,
        )
        copied.append(f"action_templates ({tmpl.slug})")

    return copied, skipped, errors


# ---------------------------------------------------------------------------
# Registry — maps type names to copy functions
# ---------------------------------------------------------------------------

COPY_REGISTRY: dict[str, callable] = {
    "email_provider": _copy_email_provider,
    "jira_connection": _copy_jira_connection,
    "action_templates": _copy_action_templates,
}

COPYABLE_TYPES = list(COPY_REGISTRY.keys())


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


class ConfigCopyService:
    """Service for copying integration configurations between tenants."""

    @staticmethod
    def get_copyable_sources(user, exclude_tenant) -> list[dict]:
        """Return tenants where user is owner (excluding current) that have configs.

        Returns: [{tenant_id, tenant_name, available_types}, ...]
        """
        owned_memberships = Membership.objects.filter(
            user=user, role="owner", is_active=True
        ).exclude(tenant=exclude_tenant).select_related("tenant")

        sources = []
        for membership in owned_memberships:
            tenant = membership.tenant
            if not tenant.is_active:
                continue

            available = []
            if EmailProviderConnection.objects.filter(tenant=tenant).exists():
                available.append("email_provider")
            if JiraConnection.objects.filter(tenant=tenant, is_active=True).exists():
                available.append("jira_connection")
            if ActionTemplate.objects.filter(tenant=tenant, is_system=False).exists():
                available.append("action_templates")

            if available:
                sources.append({
                    "tenant_id": str(tenant.id),
                    "tenant_name": tenant.name,
                    "available_types": available,
                })

        return sources

    @staticmethod
    @transaction.atomic
    def copy_config(source_tenant, target_tenant, types: list[str], overwrite: bool, user, request=None) -> dict:
        """Copy selected integration configs from source to target tenant.

        Returns: {copied: [...], skipped: [...], errors: [...]}
        """
        all_copied: list[str] = []
        all_skipped: list[str] = []
        all_errors: list[str] = []

        for type_key in types:
            copy_fn = COPY_REGISTRY.get(type_key)
            if not copy_fn:
                all_errors.append(f"{type_key}: Unbekannter Typ")
                continue

            try:
                copied, skipped, errors = copy_fn(source_tenant, target_tenant, overwrite)
                all_copied.extend(copied)
                all_skipped.extend(skipped)
                all_errors.extend(errors)
            except Exception as e:
                logger.error("config_copy_error", type=type_key, error=str(e))
                all_errors.append(f"{type_key}: {str(e)}")

        # Audit log
        AuditService.log(
            tenant=target_tenant,
            user=user,
            action="config_copy",
            entity_type="integration_config",
            entity_id=str(source_tenant.id),
            before={"source_tenant": source_tenant.name, "types": types, "overwrite": overwrite},
            after={"copied": all_copied, "skipped": all_skipped, "errors": all_errors},
            request=request,
        )

        return {
            "copied": all_copied,
            "skipped": all_skipped,
            "errors": all_errors,
        }
