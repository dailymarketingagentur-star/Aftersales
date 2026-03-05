"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useTenant } from "@/hooks/use-tenant";
import { apiFetch } from "@/lib/api";
import type { EmailProviderConnection } from "@/types/email";
import type { WhatsAppConnection } from "@/types/integration";

export default function NachrichtenUebersichtPage() {
  const { currentTenantId } = useTenant();
  const [providers, setProviders] = useState<EmailProviderConnection[]>([]);
  const [waStatus, setWaStatus] = useState<"connected" | "none">("none");

  useEffect(() => {
    if (!currentTenantId) return;
    apiFetch<EmailProviderConnection[]>("/api/v1/emails/providers/", { tenantId: currentTenantId })
      .then(setProviders)
      .catch(() => setProviders([]));
    apiFetch<WhatsAppConnection>("/api/v1/integrations/whatsapp/connection/", { tenantId: currentTenantId })
      .then(() => setWaStatus("connected"))
      .catch(() => setWaStatus("none"));
  }, [currentTenantId]);

  const smtp = providers.find((p) => p.provider_type === "smtp");
  const sendgrid = providers.find((p) => p.provider_type === "sendgrid");
  const activeProvider = providers.find((p) => p.is_active);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Nachrichten</h1>
        <Link href="/integrationen">
          <Button variant="outline" size="sm">Zurück</Button>
        </Link>
      </div>

      {activeProvider ? (
        <div className="rounded-lg border border-green-200 bg-green-50 p-4">
          <p className="font-medium text-green-800">
            Aktiver E-Mail-Provider: {activeProvider.label} ({activeProvider.provider_type.toUpperCase()})
          </p>
          <p className="mt-1 text-sm text-green-700">
            Absender: {activeProvider.from_name ? `${activeProvider.from_name} <${activeProvider.from_email}>` : activeProvider.from_email}
          </p>
        </div>
      ) : (
        <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4">
          <p className="font-medium text-yellow-800">Kein E-Mail-Provider aktiv</p>
          <p className="mt-1 text-sm text-yellow-700">
            E-Mails können nicht versendet werden. Konfiguriere einen Provider:
          </p>
          <ol className="mt-2 list-inside list-decimal space-y-1 text-sm text-yellow-700">
            <li>Wähle unten SMTP oder SendGrid</li>
            <li>Gib deine Zugangsdaten ein</li>
            <li>Teste die Verbindung</li>
            <li>Aktiviere den Provider</li>
          </ol>
        </div>
      )}

      <h2 className="text-lg font-semibold">E-Mail-Provider</h2>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Link href="/integrationen/nachrichten/smtp">
          <Card className="cursor-pointer transition-shadow hover:shadow-md">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                SMTP
                <span className={`inline-block h-3 w-3 rounded-full ${smtp?.is_active ? "bg-green-500" : smtp ? "bg-yellow-400" : "bg-gray-300"}`} />
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                {smtp?.is_active ? "Aktiv" : smtp ? `Konfiguriert — ${smtp.smtp_host}` : "Nicht konfiguriert"}
              </p>
            </CardContent>
          </Card>
        </Link>

        <Link href="/integrationen/nachrichten/sendgrid">
          <Card className="cursor-pointer transition-shadow hover:shadow-md">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                SendGrid
                <span className={`inline-block h-3 w-3 rounded-full ${sendgrid?.is_active ? "bg-green-500" : sendgrid ? "bg-yellow-400" : "bg-gray-300"}`} />
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                {sendgrid?.is_active ? "Aktiv" : sendgrid ? "Konfiguriert (inaktiv)" : "Nicht konfiguriert"}
              </p>
            </CardContent>
          </Card>
        </Link>

        <Link href="/integrationen/nachrichten/whatsapp">
          <Card className="cursor-pointer transition-shadow hover:shadow-md">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                WhatsApp Business
                <span className={`inline-block h-3 w-3 rounded-full ${waStatus === "connected" ? "bg-green-500" : "bg-gray-300"}`} />
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                {waStatus === "connected" ? "Konfiguriert" : "Nicht konfiguriert"}
              </p>
            </CardContent>
          </Card>
        </Link>
      </div>

      <h2 className="text-lg font-semibold">Posteingang & Vorlagen</h2>
      <div className="grid gap-4 md:grid-cols-2">
        <Link href="/integrationen/nachrichten/posteingang">
          <Card className="cursor-pointer transition-shadow hover:shadow-md">
            <CardHeader>
              <CardTitle>Posteingang</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Eingehende E-Mails und WhatsApp-Nachrichten anzeigen
              </p>
            </CardContent>
          </Card>
        </Link>
        <Link href="/integrationen/nachrichten/vorlagen">
          <Card className="cursor-pointer transition-shadow hover:shadow-md">
            <CardHeader>
              <CardTitle>E-Mail-Vorlagen</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                E-Mail-Vorlagen verwalten
              </p>
            </CardContent>
          </Card>
        </Link>
      </div>
    </div>
  );
}
