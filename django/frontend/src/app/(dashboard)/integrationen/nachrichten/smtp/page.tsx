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

export default function SmtpPage() {
  const { currentTenantId } = useTenant();
  const [host, setHost] = useState("");
  const [port, setPort] = useState("587");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [useTls, setUseTls] = useState(true);
  const [fromEmail, setFromEmail] = useState("");
  const [fromName, setFromName] = useState("");
  const [label, setLabel] = useState("SMTP");

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
    apiFetch<EmailProviderConnection>("/api/v1/emails/providers/smtp/", { tenantId: currentTenantId })
      .then((conn) => {
        setHost(conn.smtp_host);
        setPort(String(conn.smtp_port));
        setUsername(conn.smtp_username);
        setUseTls(conn.smtp_use_tls);
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
      await apiFetch("/api/v1/emails/providers/smtp/", {
        method: "PUT",
        body: JSON.stringify({
          label,
          smtp_host: host,
          smtp_port: parseInt(port, 10),
          smtp_username: username,
          smtp_password: password,
          smtp_use_tls: useTls,
          from_email: fromEmail,
          from_name: fromName,
        }),
        tenantId: currentTenantId!,
      });
      setMessage("SMTP-Verbindung gespeichert!");
      setIsError(false);
      setHasConnection(true);
      setPassword("");
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
      const result = await apiFetch<ConnectionTestResult>("/api/v1/emails/providers/smtp/test/", {
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
      await apiFetch("/api/v1/emails/providers/smtp/activate/", {
        method: "POST",
        tenantId: currentTenantId!,
      });
      setMessage("SMTP als aktiven Provider gesetzt.");
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
    if (!confirm("SMTP-Konfiguration wirklich löschen?")) return;
    try {
      await apiFetch("/api/v1/emails/providers/smtp/", {
        method: "DELETE",
        tenantId: currentTenantId!,
      });
      setHost("");
      setPort("587");
      setUsername("");
      setPassword("");
      setFromEmail("");
      setFromName("");
      setLabel("SMTP");
      setHasConnection(false);
      setIsActive(false);
      setMessage("SMTP-Konfiguration gelöscht.");
      setIsError(false);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Fehler beim Löschen.");
      setIsError(true);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">SMTP-Konfiguration</h1>
        <Link href="/integrationen/nachrichten">
          <Button variant="outline" size="sm">Zurück</Button>
        </Link>
      </div>

      {isActive && (
        <div className="rounded-lg border border-green-200 bg-green-50 p-4">
          <p className="font-medium text-green-800">SMTP ist der aktive E-Mail-Provider.</p>
        </div>
      )}

      {lastTestFailed && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <p className="font-medium text-red-800">Letzter Verbindungstest fehlgeschlagen.</p>
          <p className="mt-1 text-sm text-red-700">Bitte überprüfe die Zugangsdaten.</p>
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>SMTP-Zugangsdaten</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSave} className="space-y-4">
            <div>
              <Label htmlFor="label">Bezeichnung</Label>
              <Input id="label" value={label} onChange={(e) => setLabel(e.target.value)} />
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Label htmlFor="host">SMTP-Host</Label>
                <Input id="host" placeholder="smtp.example.com" value={host} onChange={(e) => setHost(e.target.value)} required />
              </div>
              <div>
                <Label htmlFor="port">Port</Label>
                <Input id="port" type="number" value={port} onChange={(e) => setPort(e.target.value)} required />
              </div>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Label htmlFor="username">Benutzername</Label>
                <Input id="username" value={username} onChange={(e) => setUsername(e.target.value)} />
              </div>
              <div>
                <Label htmlFor="password">Passwort</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder={hasConnection ? "••••••• (gespeichert, neu eingeben zum Ändern)" : "Passwort eingeben"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <input
                id="tls"
                type="checkbox"
                checked={useTls}
                onChange={(e) => setUseTls(e.target.checked)}
                className="h-4 w-4 rounded border-gray-300"
              />
              <Label htmlFor="tls">STARTTLS verwenden</Label>
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
        <Link href="/integrationen/nachrichten/vorlagen">
          <Button variant="link" className="px-0">E-Mail-Vorlagen verwalten →</Button>
        </Link>
      </div>
    </div>
  );
}
