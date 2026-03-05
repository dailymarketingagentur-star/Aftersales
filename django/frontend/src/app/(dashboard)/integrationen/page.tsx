"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { useTenant } from "@/hooks/use-tenant";
import { apiFetch } from "@/lib/api";
import type { IntegrationType } from "@/types/integration";
import type { EmailProviderConnection } from "@/types/email";
import { CopyConfigButton } from "./copy-config-dialog";

export default function IntegrationenPage() {
  const { currentTenantId } = useTenant();
  const [types, setTypes] = useState<IntegrationType[]>([]);
  const [toggling, setToggling] = useState<string | null>(null);
  const [smtpStatus, setSmtpStatus] = useState<"connected" | "active" | "none">("none");
  const [sendgridStatus, setSendgridStatus] = useState<"connected" | "active" | "none">("none");

  useEffect(() => {
    if (!currentTenantId) return;

    apiFetch<IntegrationType[]>("/api/v1/integrations/types/", { tenantId: currentTenantId })
      .then(setTypes)
      .catch(() => {});

    apiFetch<EmailProviderConnection[]>("/api/v1/emails/providers/", { tenantId: currentTenantId })
      .then((providers) => {
        for (const p of providers) {
          if (p.provider_type === "smtp") {
            setSmtpStatus(p.is_active ? "active" : "connected");
          }
          if (p.provider_type === "sendgrid") {
            setSendgridStatus(p.is_active ? "active" : "connected");
          }
        }
      })
      .catch(() => {
        setSmtpStatus("none");
        setSendgridStatus("none");
      });
  }, [currentTenantId]);

  async function handleToggle(key: string, newValue: boolean) {
    if (!currentTenantId) return;
    setToggling(key);
    try {
      await apiFetch("/api/v1/integrations/toggle/", {
        method: "POST",
        body: JSON.stringify({ integration_type: key, is_enabled: newValue }),
        tenantId: currentTenantId,
      });
      setTypes((prev) =>
        prev.map((t) => (t.key === key ? { ...t, is_enabled: newValue } : t))
      );
    } catch {
      /* Fehler ignorieren — State bleibt unveraendert */
    } finally {
      setToggling(null);
    }
  }

  function emailStatusDot(s: "connected" | "active" | "none") {
    if (s === "active") return "bg-green-500";
    if (s === "connected") return "bg-yellow-400";
    return "bg-gray-300";
  }

  function emailStatusText(s: "connected" | "active" | "none") {
    if (s === "active") return "Aktiv";
    if (s === "connected") return "Konfiguriert (inaktiv)";
    return "Nicht konfiguriert";
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Integrationen</h1>
        <CopyConfigButton />
      </div>

      {/* Dynamische Integrations-Karten */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {types.map((type) => {
          const content = (
            <Card className="transition-shadow hover:shadow-md">
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    {type.label}
                    <span
                      className={`inline-block h-3 w-3 rounded-full ${
                        type.is_enabled ? "bg-green-500" : "bg-gray-300"
                      }`}
                    />
                  </span>
                  <Switch
                    checked={type.is_enabled}
                    disabled={toggling === type.key}
                    onCheckedChange={(checked) => handleToggle(type.key, checked)}
                    onClick={(e) => e.stopPropagation()}
                  />
                </CardTitle>
                <CardDescription>{type.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  {type.is_enabled ? "Aktiviert" : "Deaktiviert"}
                  {type.fields.length > 0 && ` · ${type.fields.length} Felder`}
                </p>
              </CardContent>
            </Card>
          );

          // Jira hat eine Detail-Seite fuer die API-Verbindung
          if (type.key === "jira") {
            return (
              <Link key={type.key} href="/integrationen/jira" className="block">
                {content}
              </Link>
            );
          }

          // Twilio hat eine eigene Detail-Seite fuer Telefonie
          if (type.key === "twilio") {
            return (
              <Link key={type.key} href="/integrationen/twilio" className="block">
                {content}
              </Link>
            );
          }

          // WhatsApp hat eine eigene Detail-Seite unter Nachrichten
          if (type.key === "whatsapp") {
            return (
              <Link key={type.key} href="/integrationen/nachrichten/whatsapp" className="block">
                {content}
              </Link>
            );
          }

          // Confluence: Hinweis auf geteilte Atlassian-Verbindung
          if (type.key === "confluence") {
            return (
              <div key={type.key}>
                {content}
                <p className="mt-1 px-1 text-xs text-muted-foreground">
                  Nutzt die gleiche Atlassian-Verbindung wie Jira
                </p>
              </div>
            );
          }

          return <div key={type.key}>{content}</div>;
        })}
      </div>

      {/* E-Mail-Provider — separate Sektion */}
      <h2 className="text-lg font-semibold">Nachrichten-Provider</h2>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {/* SMTP */}
        <Link href="/integrationen/nachrichten/smtp">
          <Card className="cursor-pointer transition-shadow hover:shadow-md">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                SMTP
                <span className={`inline-block h-3 w-3 rounded-full ${emailStatusDot(smtpStatus)}`} />
              </CardTitle>
              <CardDescription>
                E-Mails über eigenen SMTP-Server versenden
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                {emailStatusText(smtpStatus)}
              </p>
            </CardContent>
          </Card>
        </Link>

        {/* SendGrid */}
        <Link href="/integrationen/nachrichten/sendgrid">
          <Card className="cursor-pointer transition-shadow hover:shadow-md">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                SendGrid
                <span className={`inline-block h-3 w-3 rounded-full ${emailStatusDot(sendgridStatus)}`} />
              </CardTitle>
              <CardDescription>
                E-Mails über SendGrid versenden
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                {emailStatusText(sendgridStatus)}
              </p>
            </CardContent>
          </Card>
        </Link>
      </div>
    </div>
  );
}
