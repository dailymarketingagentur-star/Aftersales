"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useTenant } from "@/hooks/use-tenant";
import { apiFetch } from "@/lib/api";
import type { EmailProviderConnection, ConnectionTestResult } from "@/types/email";

export default function SendGridPage() {
  const { currentTenantId } = useTenant();
  const [apiKey, setApiKey] = useState("");
  const [fromEmail, setFromEmail] = useState("");
  const [fromName, setFromName] = useState("");
  const [label, setLabel] = useState("SendGrid");

  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [activating, setActivating] = useState(false);
  const [message, setMessage] = useState("");
  const [isError, setIsError] = useState(false);
  const [hasConnection, setHasConnection] = useState(false);
  const [isActive, setIsActive] = useState(false);
  const [lastTestFailed, setLastTestFailed] = useState(false);

  useEffect(() => {
    if (!currentTenantId) return;
    apiFetch<EmailProviderConnection>("/api/v1/emails/providers/sendgrid/", { tenantId: currentTenantId })
      .then((conn) => {
        setFromEmail(conn.from_email);
        setFromName(conn.from_name);
        setLabel(conn.label);
        setHasConnection(true);
        setIsActive(conn.is_active);
        setLastTestFailed(conn.last_test_success === false);
      })
      .catch(() => setHasConnection(false));
  }, [currentTenantId]);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setMessage("");
    try {
      await apiFetch("/api/v1/emails/providers/sendgrid/", {
        method: "PUT",
        body: JSON.stringify({
          label,
          sendgrid_api_key: apiKey,
          from_email: fromEmail,
          from_name: fromName,
        }),
        tenantId: currentTenantId!,
      });
      setMessage("SendGrid-Verbindung gespeichert!");
      setIsError(false);
      setHasConnection(true);
      setApiKey("");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Fehler beim Speichern.");
      setIsError(true);
    } finally {
      setSaving(false);
    }
  }

  async function handleTest() {
    setTesting(true);
    setMessage("");
    try {
      const result = await apiFetch<ConnectionTestResult>("/api/v1/emails/providers/sendgrid/test/", {
        method: "POST",
        tenantId: currentTenantId!,
      });
      setMessage(result.message);
      setIsError(!result.success);
      setLastTestFailed(!result.success);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Verbindungstest fehlgeschlagen.");
      setIsError(true);
    } finally {
      setTesting(false);
    }
  }

  async function handleActivate() {
    setActivating(true);
    setMessage("");
    try {
      await apiFetch("/api/v1/emails/providers/sendgrid/activate/", {
        method: "POST",
        tenantId: currentTenantId!,
      });
      setMessage("SendGrid als aktiven Provider gesetzt.");
      setIsError(false);
      setIsActive(true);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Fehler beim Aktivieren.");
      setIsError(true);
    } finally {
      setActivating(false);
    }
  }

  async function handleDelete() {
    if (!confirm("SendGrid-Konfiguration wirklich löschen?")) return;
    try {
      await apiFetch("/api/v1/emails/providers/sendgrid/", {
        method: "DELETE",
        tenantId: currentTenantId!,
      });
      setApiKey("");
      setFromEmail("");
      setFromName("");
      setLabel("SendGrid");
      setHasConnection(false);
      setIsActive(false);
      setMessage("SendGrid-Konfiguration gelöscht.");
      setIsError(false);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Fehler beim Löschen.");
      setIsError(true);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">SendGrid-Konfiguration</h1>
        <Link href="/integrationen/email">
          <Button variant="outline" size="sm">Zurück</Button>
        </Link>
      </div>

      {isActive && (
        <div className="rounded-lg border border-green-200 bg-green-50 p-4">
          <p className="font-medium text-green-800">SendGrid ist der aktive E-Mail-Provider.</p>
        </div>
      )}

      {lastTestFailed && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <p className="font-medium text-red-800">Letzter Verbindungstest fehlgeschlagen.</p>
          <p className="mt-1 text-sm text-red-700">Bitte überprüfe den API-Key.</p>
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>SendGrid-Zugangsdaten</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSave} className="space-y-4">
            <div>
              <Label htmlFor="label">Bezeichnung</Label>
              <Input id="label" value={label} onChange={(e) => setLabel(e.target.value)} />
            </div>
            <div>
              <Label htmlFor="apiKey">API-Key</Label>
              <Input
                id="apiKey"
                type="password"
                placeholder={hasConnection ? "••••••• (gespeichert, neu eingeben zum Ändern)" : "SG.xxxxxxxx"}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                required={!hasConnection}
              />
              <p className="mt-1 text-xs text-muted-foreground">
                API-Key erstellen unter: SendGrid → Settings → API Keys
              </p>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Label htmlFor="fromEmail">Absender-Email</Label>
                <Input id="fromEmail" type="email" placeholder="noreply@firma.de" value={fromEmail} onChange={(e) => setFromEmail(e.target.value)} required />
              </div>
              <div>
                <Label htmlFor="fromName">Absender-Name</Label>
                <Input id="fromName" placeholder="Firma GmbH" value={fromName} onChange={(e) => setFromName(e.target.value)} />
              </div>
            </div>

            {message && (
              <p className={`text-sm ${isError ? "text-red-600" : "text-green-600"}`}>{message}</p>
            )}

            <div className="flex flex-wrap gap-2">
              <Button type="submit" disabled={saving}>
                {saving ? "Speichern..." : "Speichern"}
              </Button>
              {hasConnection && (
                <>
                  <Button type="button" variant="outline" onClick={handleTest} disabled={testing}>
                    {testing ? "Teste..." : "Verbindung testen"}
                  </Button>
                  {!isActive && (
                    <Button type="button" variant="outline" onClick={handleActivate} disabled={activating}>
                      {activating ? "Aktiviere..." : "Als aktiv setzen"}
                    </Button>
                  )}
                  <Button type="button" variant="destructive" onClick={handleDelete}>
                    Löschen
                  </Button>
                </>
              )}
            </div>
          </form>
        </CardContent>
      </Card>

      <div className="pt-2">
        <Link href="/integrationen/email/vorlagen">
          <Button variant="link" className="px-0">E-Mail-Vorlagen verwalten →</Button>
        </Link>
      </div>
    </div>
  );
}
