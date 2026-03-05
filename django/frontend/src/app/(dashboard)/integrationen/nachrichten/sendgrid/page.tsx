"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useTenant } from "@/hooks/use-tenant";
import { apiFetch } from "@/lib/api";
import type { EmailProviderConnection, ConnectionTestResult } from "@/types/email";

export default function SendGridPage() {
  const { currentTenantId } = useTenant();
  const [apiKey, setApiKey] = useState("");
  const [fromEmail, setFromEmail] = useState("");
  const [fromName, setFromName] = useState("");
  const [label, setLabel] = useState("SendGrid");

  // Inbound Parse state
  const [inboundEnabled, setInboundEnabled] = useState(false);
  const [inboundDomain, setInboundDomain] = useState("");

  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [activating, setActivating] = useState(false);
  const [message, setMessage] = useState("");
  const [isError, setIsError] = useState(false);
  const [hasConnection, setHasConnection] = useState(false);
  const [isActive, setIsActive] = useState(false);
  const [lastTestFailed, setLastTestFailed] = useState(false);
  const [guideOpen, setGuideOpen] = useState(false);
  const [copied, setCopied] = useState(false);

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
        setInboundEnabled(conn.inbound_parse_enabled);
        setInboundDomain(conn.inbound_parse_domain);
      })
      .catch(() => setHasConnection(false));
  }, [currentTenantId]);

  const webhookUrl = currentTenantId
    ? `${window.location.origin}/api/v1/emails/inbound-webhook/${currentTenantId}/`
    : "";

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
          inbound_parse_enabled: inboundEnabled,
          inbound_parse_domain: inboundDomain,
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
      setInboundEnabled(false);
      setInboundDomain("");
      setHasConnection(false);
      setIsActive(false);
      setMessage("SendGrid-Konfiguration gelöscht.");
      setIsError(false);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Fehler beim Löschen.");
      setIsError(true);
    }
  }

  function handleCopyWebhookUrl() {
    navigator.clipboard.writeText(webhookUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">SendGrid-Konfiguration</h1>
        <Link href="/integrationen/nachrichten">
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

      {/* Inbound Parse Section */}
      <Card>
        <CardHeader>
          <CardTitle>Inbound Parse — E-Mail-Empfang</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {inboundEnabled && (
            <Alert className="border-amber-200 bg-amber-50 text-amber-900">
              <AlertTitle>Wichtiger Hinweis zu Inbound Parse</AlertTitle>
              <AlertDescription>
                <p className="mt-1">
                  Wenn Inbound Parse aktiviert ist, werden E-Mail-Antworten an eine technische
                  Subdomain-Adresse zugestellt (z.B. antwort@{inboundDomain || "parse.ihredomain.de"}),
                  NICHT an die persönliche E-Mail-Adresse des Beraters.
                </p>
                <p className="mt-2">
                  Kunden müssen explizit darauf hingewiesen werden, an welche Adresse
                  sie antworten sollen, oder die Absender-Adresse muss entsprechend konfiguriert werden.
                </p>
              </AlertDescription>
            </Alert>
          )}

          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="inboundEnabled"
              checked={inboundEnabled}
              onChange={(e) => setInboundEnabled(e.target.checked)}
              className="h-4 w-4 rounded border-gray-300"
            />
            <Label htmlFor="inboundEnabled" className="cursor-pointer">
              Inbound Parse aktivieren
            </Label>
          </div>

          {inboundEnabled && (
            <div className="space-y-4">
              <div>
                <Label htmlFor="inboundDomain">Empfangs-Subdomain</Label>
                <Input
                  id="inboundDomain"
                  placeholder="parse.aftersales.daily-marketing.de"
                  value={inboundDomain}
                  onChange={(e) => setInboundDomain(e.target.value)}
                />
                <p className="mt-1 text-xs text-muted-foreground">
                  Die Subdomain, auf der eingehende E-Mails empfangen werden sollen.
                </p>
              </div>

              {inboundDomain && (
                <>
                  <div>
                    <Label className="text-sm text-muted-foreground">Antwort-Adresse</Label>
                    <p className="mt-1 font-mono text-sm">antwort@{inboundDomain}</p>
                  </div>

                  <div>
                    <Label className="text-sm text-muted-foreground">Webhook-URL</Label>
                    <div className="mt-1 flex items-center gap-2">
                      <code className="flex-1 rounded bg-muted px-3 py-2 text-xs break-all">
                        {webhookUrl}
                      </code>
                      <Button type="button" variant="outline" size="sm" onClick={handleCopyWebhookUrl}>
                        {copied ? "Kopiert!" : "Kopieren"}
                      </Button>
                    </div>
                  </div>
                </>
              )}

              <p className="text-xs text-muted-foreground">
                Klicke oben auf &quot;Speichern&quot; um die Inbound-Parse-Konfiguration zu übernehmen.
              </p>

              {/* Setup Guide */}
              <div className="rounded-lg border">
                <button
                  type="button"
                  onClick={() => setGuideOpen(!guideOpen)}
                  className="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-medium hover:bg-muted/50"
                >
                  Einrichtungsanleitung
                  <span className="text-muted-foreground">{guideOpen ? "−" : "+"}</span>
                </button>
                {guideOpen && (
                  <div className="space-y-4 border-t px-4 py-3 text-sm">
                    <div>
                      <p className="font-medium">Schritt 1: SendGrid-Konto vorbereiten</p>
                      <ul className="mt-1 list-inside list-disc text-muted-foreground">
                        <li>Öffne SendGrid → Settings → Inbound Parse</li>
                        <li>Stelle sicher, dass dein SendGrid-Plan Inbound Parse unterstützt</li>
                      </ul>
                    </div>
                    <div>
                      <p className="font-medium">Schritt 2: DNS-Konfiguration (MX-Record)</p>
                      <ul className="mt-1 list-inside list-disc text-muted-foreground">
                        <li>Erstelle bei deinem Domain-Hoster einen MX-Record:</li>
                        <li>Typ: <strong>MX</strong></li>
                        <li>Host/Name: <strong>{inboundDomain || "[deine Subdomain]"}</strong></li>
                        <li>Wert/Points to: <strong>mx.sendgrid.net</strong></li>
                        <li>Priorität: <strong>10</strong></li>
                      </ul>
                      <p className="mt-1 text-xs text-muted-foreground">DNS-Änderungen können bis zu 48 Stunden dauern.</p>
                    </div>
                    <div>
                      <p className="font-medium">Schritt 3: SendGrid Inbound Parse konfigurieren</p>
                      <ul className="mt-1 list-inside list-disc text-muted-foreground">
                        <li>Gehe zu SendGrid → Settings → Inbound Parse</li>
                        <li>Klicke &quot;Add Host & URL&quot;</li>
                        <li>Hostname: <strong>{inboundDomain || "[deine Subdomain]"}</strong></li>
                        <li>URL: <strong>{webhookUrl || "[Webhook-URL von oben]"}</strong></li>
                        <li>&quot;Check incoming emails for spam&quot;: Optional</li>
                        <li>&quot;POST the raw, full MIME message&quot;: <strong>NICHT aktivieren</strong></li>
                        <li>Speichern</li>
                      </ul>
                    </div>
                    <div>
                      <p className="font-medium">Schritt 4: Testen</p>
                      <ul className="mt-1 list-inside list-disc text-muted-foreground">
                        <li>Sende eine Test-E-Mail an test@{inboundDomain || "[deine Subdomain]"}</li>
                        <li>Die E-Mail sollte innerhalb weniger Sekunden im Posteingang erscheinen</li>
                      </ul>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="pt-2">
        <Link href="/integrationen/nachrichten/vorlagen">
          <Button variant="link" className="px-0">E-Mail-Vorlagen verwalten →</Button>
        </Link>
      </div>
    </div>
  );
}
