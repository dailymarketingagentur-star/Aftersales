"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useTenant } from "@/hooks/use-tenant";
import { apiFetch } from "@/lib/api";
import type { ConnectionTestResult, JiraConnection } from "@/types/integration";

const CONFIG_FIELDS = [
  { section: "Projekt-Einstellungen", fields: [
    { key: "SEARCH_EMAIL", label: "Lead-Email (User-Suche)" },
    { key: "PROJECT_TEMPLATE_KEY", label: "Projekt-Template-Key" },
    { key: "PROJECT_DESCRIPTION", label: "Projekt-Beschreibung" },
  ]},
  { section: "Schema-IDs", fields: [
    { key: "WORKFLOW_SCHEME_ID", label: "Workflow-Schema-ID" },
    { key: "ISSUE_TYPE_SCREEN_SCHEME_ID", label: "Issue-Type-Screen-Schema-ID" },
    { key: "FIELD_CONFIG_SCHEME_ID", label: "Feldkonfigurations-Schema-ID" },
    { key: "ISSUE_TYPE_SCHEME_ID", label: "Issue-Type-Schema-ID" },
  ]},
  { section: "Issue-Einstellungen", fields: [
    { key: "ISSUE_TYPE_ID", label: "Standard Issue-Type-ID" },
  ]},
  { section: "Custom-Field-Zuordnung", fields: [
    { key: "CUSTOM_FIELD_EMAIL", label: "E-Mail-Feld-ID" },
    { key: "CUSTOM_FIELD_COMPANY", label: "Firmenname-Feld-ID" },
    { key: "CUSTOM_FIELD_PHONE", label: "Telefon-Feld-ID" },
    { key: "CUSTOM_FIELD_WEBSITE", label: "Website-Feld-ID" },
  ]},
] as const;

export default function VerbindungPage() {
  const { currentTenantId } = useTenant();
  const [jiraUrl, setJiraUrl] = useState("");
  const [jiraEmail, setJiraEmail] = useState("");
  const [jiraToken, setJiraToken] = useState("");
  const [label, setLabel] = useState("Jira Cloud");
  const [config, setConfig] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [savingConfig, setSavingConfig] = useState(false);
  const [testing, setTesting] = useState(false);
  const [message, setMessage] = useState("");
  const [isError, setIsError] = useState(false);
  const [configMessage, setConfigMessage] = useState("");
  const [configIsError, setConfigIsError] = useState(false);
  const [hasConnection, setHasConnection] = useState(false);
  const [connectionFailed, setConnectionFailed] = useState(false);

  useEffect(() => {
    if (!currentTenantId) return;
    apiFetch<JiraConnection>("/api/v1/integrations/connection/", { tenantId: currentTenantId })
      .then((conn) => {
        setJiraUrl(conn.jira_url);
        setJiraEmail(conn.jira_email);
        setLabel(conn.label);
        setConfig(conn.config || {});
        setHasConnection(true);
        setConnectionFailed(conn.last_test_success === false);
      })
      .catch(() => setHasConnection(false));
  }, [currentTenantId]);

  function updateConfig(key: string, value: string) {
    setConfig((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setMessage("");
    try {
      await apiFetch("/api/v1/integrations/connection/", {
        method: "PUT",
        body: JSON.stringify({
          label,
          jira_url: jiraUrl,
          jira_email: jiraEmail,
          jira_api_token: jiraToken,
        }),
        tenantId: currentTenantId!,
      });
      setMessage("Verbindung gespeichert!");
      setIsError(false);
      setHasConnection(true);
      setJiraToken("");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Fehler beim Speichern.");
      setIsError(true);
    } finally {
      setSaving(false);
    }
  }

  async function handleSaveConfig(e: React.FormEvent) {
    e.preventDefault();
    setSavingConfig(true);
    setConfigMessage("");
    try {
      // Leere Werte rausfiltern, damit nur gesetzte Keys gespeichert werden
      const cleanConfig: Record<string, string> = {};
      for (const [k, v] of Object.entries(config)) {
        if (v.trim()) cleanConfig[k] = v.trim();
      }
      await apiFetch("/api/v1/integrations/connection/", {
        method: "PUT",
        body: JSON.stringify({
          label,
          jira_url: jiraUrl,
          jira_email: jiraEmail,
          jira_api_token: jiraToken || "UNCHANGED",
          config: cleanConfig,
        }),
        tenantId: currentTenantId!,
      });
      setConfig(cleanConfig);
      setConfigMessage("Konfiguration gespeichert!");
      setConfigIsError(false);
    } catch (err) {
      setConfigMessage(err instanceof Error ? err.message : "Fehler beim Speichern.");
      setConfigIsError(true);
    } finally {
      setSavingConfig(false);
    }
  }

  async function handleTest() {
    setTesting(true);
    setMessage("");
    try {
      const result = await apiFetch<ConnectionTestResult>("/api/v1/integrations/connection/test/", {
        method: "POST",
        tenantId: currentTenantId!,
      });
      setMessage(result.message);
      setIsError(!result.success);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Verbindungstest fehlgeschlagen.");
      setIsError(true);
    } finally {
      setTesting(false);
    }
  }

  async function handleDelete() {
    if (!confirm("Verbindung wirklich löschen?")) return;
    try {
      await apiFetch("/api/v1/integrations/connection/", {
        method: "DELETE",
        tenantId: currentTenantId!,
      });
      setJiraUrl("");
      setJiraEmail("");
      setJiraToken("");
      setLabel("Jira Cloud");
      setConfig({});
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
        <h1 className="text-2xl font-bold">Jira-Verbindung</h1>
        <Link href="/integrationen/jira">
          <Button variant="outline" size="sm">Zurück</Button>
        </Link>
      </div>

      {connectionFailed && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <div className="flex items-start gap-3">
            <span className="mt-0.5 text-red-600 text-lg">&#9888;</span>
            <div>
              <p className="font-medium text-red-800">
                API-Token ist ungültig oder abgelaufen
              </p>
              <p className="mt-1 text-sm text-red-700">
                Erstelle einen neuen Token unter{" "}
                <a
                  href="https://id.atlassian.com/manage-profile/security/api-tokens"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="underline font-medium"
                >
                  Atlassian → API Tokens
                </a>
                , gib ihn unten ein und klicke &quot;Speichern&quot;.
              </p>
            </div>
          </div>
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Zugangsdaten</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSave} className="space-y-4">
            <div>
              <Label htmlFor="label">Bezeichnung</Label>
              <Input id="label" value={label} onChange={(e) => setLabel(e.target.value)} />
            </div>
            <div>
              <Label htmlFor="jiraUrl">Jira-URL</Label>
              <Input
                id="jiraUrl"
                type="url"
                placeholder="https://firma.atlassian.net"
                value={jiraUrl}
                onChange={(e) => setJiraUrl(e.target.value)}
                required
              />
            </div>
            <div>
              <Label htmlFor="jiraEmail">Jira-Email</Label>
              <Input
                id="jiraEmail"
                type="email"
                placeholder="user@firma.de"
                value={jiraEmail}
                onChange={(e) => setJiraEmail(e.target.value)}
                required
              />
            </div>
            <div>
              <Label htmlFor="jiraToken">API-Token</Label>
              <Input
                id="jiraToken"
                type="password"
                placeholder={hasConnection ? "••••••• (gespeichert, neu eingeben zum Ändern)" : "API-Token eingeben"}
                value={jiraToken}
                onChange={(e) => setJiraToken(e.target.value)}
                required={!hasConnection}
              />
              <p className="mt-1 text-xs text-muted-foreground">
                Token erstellen unter: Atlassian Account → Security → API Tokens
              </p>
            </div>

            {message && (
              <p className={`text-sm ${isError ? "text-red-600" : "text-green-600"}`}>
                {message}
              </p>
            )}

            <div className="flex gap-2">
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

      {hasConnection && (
        <Card>
          <CardHeader>
            <CardTitle>Jira-Konfiguration</CardTitle>
            <CardDescription>
              Instanzspezifische Werte für die Automatisierung. Diese IDs findest du in deiner Jira-Administration.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSaveConfig} className="space-y-6">
              {CONFIG_FIELDS.map((group) => (
                <div key={group.section}>
                  <h3 className="text-sm font-semibold text-muted-foreground mb-3">
                    {group.section}
                  </h3>
                  <div className="grid gap-3 sm:grid-cols-2">
                    {group.fields.map((field) => (
                      <div key={field.key}>
                        <Label htmlFor={`cfg-${field.key}`} className="text-xs">
                          {field.label}
                        </Label>
                        <Input
                          id={`cfg-${field.key}`}
                          value={config[field.key] || ""}
                          onChange={(e) => updateConfig(field.key, e.target.value)}
                          className="mt-1"
                        />
                        <p className="mt-0.5 text-[10px] text-muted-foreground font-mono">
                          {field.key}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              ))}

              {configMessage && (
                <p className={`text-sm ${configIsError ? "text-red-600" : "text-green-600"}`}>
                  {configMessage}
                </p>
              )}

              <Button type="submit" disabled={savingConfig}>
                {savingConfig ? "Speichern..." : "Konfiguration speichern"}
              </Button>
            </form>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
