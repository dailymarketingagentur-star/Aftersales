"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useTenant } from "@/hooks/use-tenant";
import { apiFetch } from "@/lib/api";
import type { ConnectionTestResult, TwilioConnection } from "@/types/integration";

export default function TwilioVerbindungPage() {
  const { currentTenantId } = useTenant();
  const [accountSid, setAccountSid] = useState("");
  const [authToken, setAuthToken] = useState("");
  const [twimlAppSid, setTwimlAppSid] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [label, setLabel] = useState("Twilio Telefonie");
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [message, setMessage] = useState("");
  const [isError, setIsError] = useState(false);
  const [hasConnection, setHasConnection] = useState(false);

  useEffect(() => {
    if (!currentTenantId) return;
    apiFetch<TwilioConnection>("/api/v1/integrations/twilio/connection/", {
      tenantId: currentTenantId,
    })
      .then((conn) => {
        setAccountSid(conn.account_sid);
        setTwimlAppSid(conn.twiml_app_sid);
        setPhoneNumber(conn.phone_number);
        setLabel(conn.label);
        setHasConnection(true);
      })
      .catch(() => setHasConnection(false));
  }, [currentTenantId]);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setMessage("");
    try {
      await apiFetch("/api/v1/integrations/twilio/connection/", {
        method: "PUT",
        body: JSON.stringify({
          label,
          account_sid: accountSid,
          auth_token: authToken,
          twiml_app_sid: twimlAppSid,
          phone_number: phoneNumber,
        }),
        tenantId: currentTenantId!,
      });
      setMessage("Verbindung gespeichert!");
      setIsError(false);
      setHasConnection(true);
      setAuthToken("");
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
      const result = await apiFetch<ConnectionTestResult>(
        "/api/v1/integrations/twilio/connection/test/",
        { method: "POST", tenantId: currentTenantId! }
      );
      setMessage(result.message);
      setIsError(!result.success);
    } catch (err) {
      setMessage(
        err instanceof Error ? err.message : "Verbindungstest fehlgeschlagen."
      );
      setIsError(true);
    } finally {
      setTesting(false);
    }
  }

  async function handleDelete() {
    if (!confirm("Twilio-Verbindung wirklich löschen?")) return;
    try {
      await apiFetch("/api/v1/integrations/twilio/connection/", {
        method: "DELETE",
        tenantId: currentTenantId!,
      });
      setAccountSid("");
      setAuthToken("");
      setTwimlAppSid("");
      setPhoneNumber("");
      setLabel("Twilio Telefonie");
      setHasConnection(false);
      setMessage("Verbindung gelöscht.");
      setIsError(false);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Fehler beim Löschen.");
      setIsError(true);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Twilio-Verbindung</h1>
        <Link href="/integrationen/twilio">
          <Button variant="outline" size="sm">
            Zurück
          </Button>
        </Link>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Zugangsdaten</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSave} className="space-y-4">
            <div>
              <Label htmlFor="label">Bezeichnung</Label>
              <Input
                id="label"
                value={label}
                onChange={(e) => setLabel(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="accountSid">Account SID</Label>
              <Input
                id="accountSid"
                placeholder="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                value={accountSid}
                onChange={(e) => setAccountSid(e.target.value)}
                required
              />
              <p className="mt-1 text-xs text-muted-foreground">
                Beginnt mit &quot;AC&quot;, 34 Zeichen lang
              </p>
            </div>
            <div>
              <Label htmlFor="authToken">Auth Token</Label>
              <Input
                id="authToken"
                type="password"
                placeholder={
                  hasConnection
                    ? "••••••• (gespeichert, neu eingeben zum Ändern)"
                    : "Auth Token eingeben"
                }
                value={authToken}
                onChange={(e) => setAuthToken(e.target.value)}
                required={!hasConnection}
              />
              <p className="mt-1 text-xs text-muted-foreground">
                Findest du in der Twilio-Console unter Account &gt; API Keys
              </p>
            </div>
            <div>
              <Label htmlFor="twimlAppSid">TwiML App SID</Label>
              <Input
                id="twimlAppSid"
                placeholder="APxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                value={twimlAppSid}
                onChange={(e) => setTwimlAppSid(e.target.value)}
                required
              />
              <p className="mt-1 text-xs text-muted-foreground">
                Beginnt mit &quot;AP&quot; — erstelle eine TwiML App in der
                Twilio-Console
              </p>
            </div>
            <div>
              <Label htmlFor="phoneNumber">Telefonnummer</Label>
              <Input
                id="phoneNumber"
                placeholder="+4930123456"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                required
              />
              <p className="mt-1 text-xs text-muted-foreground">
                E.164-Format, z.B. +4930123456
              </p>
            </div>

            {message && (
              <p
                className={`text-sm ${isError ? "text-red-600" : "text-green-600"}`}
              >
                {message}
              </p>
            )}

            <div className="flex gap-2">
              <Button type="submit" disabled={saving}>
                {saving ? "Speichern..." : "Speichern"}
              </Button>
              {hasConnection && (
                <>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleTest}
                    disabled={testing}
                  >
                    {testing ? "Teste..." : "Verbindung testen"}
                  </Button>
                  <Button
                    type="button"
                    variant="destructive"
                    onClick={handleDelete}
                  >
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
