"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useTenant } from "@/hooks/use-tenant";
import { apiFetch } from "@/lib/api";
import type { WhatsAppConnection, ConnectionTestResult } from "@/types/integration";

export default function WhatsAppPage() {
  const { currentTenantId } = useTenant();
  const [phoneNumberId, setPhoneNumberId] = useState("");
  const [businessAccountId, setBusinessAccountId] = useState("");
  const [accessToken, setAccessToken] = useState("");
  const [webhookVerifyToken, setWebhookVerifyToken] = useState("");
  const [displayPhoneNumber, setDisplayPhoneNumber] = useState("");
  const [label, setLabel] = useState("WhatsApp Business");

  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [message, setMessage] = useState("");
  const [isError, setIsError] = useState(false);
  const [hasConnection, setHasConnection] = useState(false);
  const [lastTestFailed, setLastTestFailed] = useState(false);

  useEffect(() => {
    if (!currentTenantId) return;
    apiFetch<WhatsAppConnection>("/api/v1/integrations/whatsapp/connection/", { tenantId: currentTenantId })
      .then((conn) => {
        setPhoneNumberId(conn.phone_number_id);
        setBusinessAccountId(conn.business_account_id);
        setWebhookVerifyToken(conn.webhook_verify_token);
        setDisplayPhoneNumber(conn.display_phone_number);
        setLabel(conn.label);
        setHasConnection(true);
        setLastTestFailed(conn.last_test_success === false);
      })
      .catch(() => setHasConnection(false));
  }, [currentTenantId]);

  const webhookUrl = typeof window !== "undefined"
    ? `${window.location.origin}/api/v1/integrations/whatsapp/webhook/`
    : "";

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setMessage("");
    try {
      await apiFetch("/api/v1/integrations/whatsapp/connection/", {
        method: "PUT",
        body: JSON.stringify({
          label,
          phone_number_id: phoneNumberId,
          business_account_id: businessAccountId,
          access_token: accessToken,
          webhook_verify_token: webhookVerifyToken,
          display_phone_number: displayPhoneNumber,
        }),
        tenantId: currentTenantId!,
      });
      setMessage("WhatsApp-Verbindung gespeichert!");
      setIsError(false);
      setHasConnection(true);
      setAccessToken("");
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
      const result = await apiFetch<ConnectionTestResult>("/api/v1/integrations/whatsapp/connection/test/", {
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

  async function handleDelete() {
    if (!confirm("WhatsApp-Konfiguration wirklich löschen?")) return;
    try {
      await apiFetch("/api/v1/integrations/whatsapp/connection/", {
        method: "DELETE",
        tenantId: currentTenantId!,
      });
      setPhoneNumberId("");
      setBusinessAccountId("");
      setAccessToken("");
      setWebhookVerifyToken("");
      setDisplayPhoneNumber("");
      setLabel("WhatsApp Business");
      setHasConnection(false);
      setMessage("WhatsApp-Konfiguration gelöscht.");
      setIsError(false);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Fehler beim Löschen.");
      setIsError(true);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">WhatsApp Business</h1>
        <Link href="/integrationen/nachrichten">
          <Button variant="outline" size="sm">Zurück</Button>
        </Link>
      </div>

      {hasConnection && !lastTestFailed && (
        <div className="rounded-lg border border-green-200 bg-green-50 p-4">
          <p className="font-medium text-green-800">WhatsApp Business ist konfiguriert.</p>
        </div>
      )}

      {lastTestFailed && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <p className="font-medium text-red-800">Letzter Verbindungstest fehlgeschlagen.</p>
          <p className="mt-1 text-sm text-red-700">Bitte überprüfe den Access Token.</p>
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Meta Cloud API Zugangsdaten</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSave} className="space-y-4">
            <div>
              <Label htmlFor="label">Bezeichnung</Label>
              <Input id="label" value={label} onChange={(e) => setLabel(e.target.value)} />
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Label htmlFor="phoneNumberId">Phone Number ID</Label>
                <Input id="phoneNumberId" placeholder="123456789012345" value={phoneNumberId} onChange={(e) => setPhoneNumberId(e.target.value)} required />
                <p className="mt-1 text-xs text-muted-foreground">Aus dem WhatsApp Business Dashboard</p>
              </div>
              <div>
                <Label htmlFor="businessAccountId">Business Account ID (WABA)</Label>
                <Input id="businessAccountId" placeholder="123456789012345" value={businessAccountId} onChange={(e) => setBusinessAccountId(e.target.value)} required />
              </div>
            </div>
            <div>
              <Label htmlFor="accessToken">Access Token</Label>
              <Input
                id="accessToken"
                type="password"
                placeholder={hasConnection ? "••••••• (gespeichert, neu eingeben zum Ändern)" : "EAAxxxxxxxx..."}
                value={accessToken}
                onChange={(e) => setAccessToken(e.target.value)}
                required={!hasConnection}
              />
              <p className="mt-1 text-xs text-muted-foreground">
                Permanenten System-User-Token verwenden (nicht den temporären Test-Token)
              </p>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Label htmlFor="displayPhoneNumber">Anzeige-Nummer (E.164)</Label>
                <Input id="displayPhoneNumber" placeholder="+4915112345678" value={displayPhoneNumber} onChange={(e) => setDisplayPhoneNumber(e.target.value)} required />
              </div>
              <div>
                <Label htmlFor="webhookVerifyToken">Webhook Verify Token</Label>
                <Input id="webhookVerifyToken" placeholder="mein_geheimer_token" value={webhookVerifyToken} onChange={(e) => setWebhookVerifyToken(e.target.value)} required />
                <p className="mt-1 text-xs text-muted-foreground">Frei wählbar, muss in Meta konfiguriert werden</p>
              </div>
            </div>

            {webhookUrl && (
              <div>
                <Label className="text-sm text-muted-foreground">Webhook-URL (in Meta konfigurieren)</Label>
                <code className="mt-1 block rounded bg-muted px-3 py-2 text-xs break-all">
                  {webhookUrl}
                </code>
              </div>
            )}

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
                  <Button type="button" variant="destructive" onClick={handleDelete}>
                    Löschen
                  </Button>
                </>
              )}
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
