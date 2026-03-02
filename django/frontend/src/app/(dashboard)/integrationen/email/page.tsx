"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useTenant } from "@/hooks/use-tenant";
import { apiFetch } from "@/lib/api";
import type { EmailProviderConnection } from "@/types/email";

export default function EmailUebersichtPage() {
  const { currentTenantId } = useTenant();
  const [providers, setProviders] = useState<EmailProviderConnection[]>([]);

  useEffect(() => {
    if (!currentTenantId) return;
    apiFetch<EmailProviderConnection[]>("/api/v1/emails/providers/", { tenantId: currentTenantId })
      .then(setProviders)
      .catch(() => setProviders([]));
  }, [currentTenantId]);

  const smtp = providers.find((p) => p.provider_type === "smtp");
  const sendgrid = providers.find((p) => p.provider_type === "sendgrid");
  const activeProvider = providers.find((p) => p.is_active);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">E-Mail-Konfiguration</h1>
        <Link href="/integrationen">
          <Button variant="outline" size="sm">Zurück</Button>
        </Link>
      </div>

      {activeProvider ? (
        <div className="rounded-lg border border-green-200 bg-green-50 p-4">
          <p className="font-medium text-green-800">
            Aktiver Provider: {activeProvider.label} ({activeProvider.provider_type.toUpperCase()})
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

      <p className="text-sm text-muted-foreground">
        Nur ein Provider kann gleichzeitig aktiv sein. Konfiguriere SMTP oder SendGrid und aktiviere den gewünschten Provider.
      </p>

      <div className="grid gap-4 md:grid-cols-2">
        <Link href="/integrationen/email/smtp">
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

        <Link href="/integrationen/email/sendgrid">
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
      </div>

      <div className="pt-4">
        <Link href="/integrationen/email/vorlagen">
          <Button variant="outline">E-Mail-Vorlagen verwalten</Button>
        </Link>
      </div>
    </div>
  );
}
