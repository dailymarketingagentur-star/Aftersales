"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useTenant } from "@/hooks/use-tenant";
import { apiFetch } from "@/lib/api";
import type { ActionTemplate } from "@/types/integration";

const AUTH_LABELS: Record<string, string> = {
  none: "Keine",
  bearer: "Bearer Token",
  basic: "Basic Auth",
  api_key: "API Key",
};

export default function WebhookVorlageDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { currentTenantId } = useTenant();
  const [template, setTemplate] = useState<ActionTemplate | null>(null);

  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [description, setDescription] = useState("");
  const [method, setMethod] = useState("POST");
  const [webhookUrl, setWebhookUrl] = useState("");
  const [authType, setAuthType] = useState("none");
  const [authCredentials, setAuthCredentials] = useState("");
  const [bodyJson, setBodyJson] = useState("");
  const [headersJson, setHeadersJson] = useState("");
  const [variables, setVariables] = useState("");
  const [outputMapping, setOutputMapping] = useState("");

  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [isError, setIsError] = useState(false);

  useEffect(() => {
    if (!currentTenantId || !id) return;
    apiFetch<ActionTemplate>(`/api/v1/integrations/templates/${id}/`, { tenantId: currentTenantId })
      .then((tpl) => {
        setTemplate(tpl);
        setName(tpl.name);
        setSlug(tpl.slug);
        setDescription(tpl.description);
        setMethod(tpl.method);
        setWebhookUrl(tpl.webhook_url);
        setAuthType(tpl.auth_type);
        setBodyJson(JSON.stringify(tpl.body_json, null, 2));
        setHeadersJson(JSON.stringify(tpl.headers_json, null, 2));
        setVariables(tpl.variables.join(", "));
        setOutputMapping(JSON.stringify(tpl.output_mapping, null, 2));
      })
      .catch(() => {});
  }, [currentTenantId, id]);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (!template || template.is_system) return;

    setSaving(true);
    setMessage("");

    let parsedBody = {};
    let parsedHeaders = {};
    let parsedMapping = {};
    let parsedCreds = undefined;

    try {
      parsedBody = bodyJson.trim() ? JSON.parse(bodyJson) : {};
    } catch {
      setMessage("Body-JSON ist ungültig.");
      setIsError(true);
      setSaving(false);
      return;
    }
    try {
      parsedHeaders = headersJson.trim() ? JSON.parse(headersJson) : {};
    } catch {
      setMessage("Headers-JSON ist ungültig.");
      setIsError(true);
      setSaving(false);
      return;
    }
    try {
      parsedMapping = outputMapping.trim() ? JSON.parse(outputMapping) : {};
    } catch {
      setMessage("Output-Mapping-JSON ist ungültig.");
      setIsError(true);
      setSaving(false);
      return;
    }
    if (authCredentials.trim()) {
      try {
        parsedCreds = JSON.parse(authCredentials);
      } catch {
        setMessage("Auth-Credentials-JSON ist ungültig.");
        setIsError(true);
        setSaving(false);
        return;
      }
    }

    try {
      await apiFetch(`/api/v1/integrations/templates/${id}/`, {
        method: "PATCH",
        body: JSON.stringify({
          name,
          slug,
          description,
          method,
          webhook_url: webhookUrl,
          auth_type: authType,
          ...(parsedCreds ? { auth_credentials: parsedCreds } : {}),
          body_json: parsedBody,
          headers_json: parsedHeaders,
          variables: variables.split(",").map((v) => v.trim()).filter(Boolean),
          output_mapping: parsedMapping,
        }),
        tenantId: currentTenantId!,
      });
      setMessage("Gespeichert!");
      setIsError(false);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Fehler beim Speichern.");
      setIsError(true);
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!confirm("Vorlage wirklich löschen?")) return;
    try {
      await apiFetch(`/api/v1/integrations/templates/${id}/`, {
        method: "DELETE",
        tenantId: currentTenantId!,
      });
      router.push("/integrationen/webhooks/vorlagen");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Fehler beim Löschen.");
      setIsError(true);
    }
  }

  if (!template) return <p>Laden...</p>;

  const authHint: Record<string, string> = {
    none: "",
    bearer: '{"token": "..."}',
    basic: '{"username": "...", "password": "..."}',
    api_key: '{"header_name": "X-API-Key", "header_value": "..."}',
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{template.name}</h1>
        <div className="flex gap-2">
          <Link href="/integrationen/webhooks/vorlagen">
            <Button variant="outline" size="sm">Zurück</Button>
          </Link>
          {!template.is_system && (
            <Button variant="destructive" size="sm" onClick={handleDelete}>Löschen</Button>
          )}
        </div>
      </div>

      {template.is_system && (
        <p className="text-sm text-muted-foreground">
          System-Vorlagen können nicht bearbeitet werden.
        </p>
      )}

      <Card>
        <CardHeader>
          <CardTitle>{template.is_system ? "Details" : "Vorlage bearbeiten"}</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSave} className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Label htmlFor="name">Name</Label>
                <Input id="name" value={name} onChange={(e) => setName(e.target.value)} disabled={template.is_system} />
              </div>
              <div>
                <Label htmlFor="slug">Slug</Label>
                <Input id="slug" value={slug} onChange={(e) => setSlug(e.target.value)} disabled={template.is_system} />
              </div>
            </div>
            <div>
              <Label htmlFor="description">Beschreibung</Label>
              <Input id="description" value={description} onChange={(e) => setDescription(e.target.value)} disabled={template.is_system} />
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Label htmlFor="method">HTTP-Methode</Label>
                <select
                  id="method"
                  value={method}
                  onChange={(e) => setMethod(e.target.value)}
                  disabled={template.is_system}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  <option value="GET">GET</option>
                  <option value="POST">POST</option>
                  <option value="PUT">PUT</option>
                  <option value="DELETE">DELETE</option>
                </select>
              </div>
              <div>
                <Label htmlFor="webhookUrl">Webhook-URL</Label>
                <Input
                  id="webhookUrl"
                  value={webhookUrl}
                  onChange={(e) => setWebhookUrl(e.target.value)}
                  disabled={template.is_system}
                  placeholder="https://api.example.com/webhook"
                />
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Label htmlFor="authType">Authentifizierung</Label>
                <select
                  id="authType"
                  value={authType}
                  onChange={(e) => setAuthType(e.target.value)}
                  disabled={template.is_system}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  <option value="none">Keine</option>
                  <option value="bearer">Bearer Token</option>
                  <option value="basic">Basic Auth</option>
                  <option value="api_key">API Key</option>
                </select>
              </div>
              {authType !== "none" && !template.is_system && (
                <div>
                  <Label htmlFor="authCredentials">Neue Credentials (JSON, optional)</Label>
                  <Input
                    id="authCredentials"
                    value={authCredentials}
                    onChange={(e) => setAuthCredentials(e.target.value)}
                    placeholder={authHint[authType]}
                  />
                  <p className="mt-1 text-xs text-muted-foreground">
                    Nur ausfüllen um Credentials zu ändern. Aktuell: {AUTH_LABELS[authType]}
                  </p>
                </div>
              )}
            </div>

            <div>
              <Label htmlFor="variables">Variablen (kommagetrennt)</Label>
              <Input id="variables" value={variables} onChange={(e) => setVariables(e.target.value)} disabled={template.is_system} />
            </div>
            <div>
              <Label htmlFor="headersJson">Extra-Headers (JSON)</Label>
              <textarea
                id="headersJson"
                value={headersJson}
                onChange={(e) => setHeadersJson(e.target.value)}
                disabled={template.is_system}
                rows={3}
                className="w-full rounded-md border border-input bg-background px-3 py-2 font-mono text-sm"
              />
            </div>
            <div>
              <Label htmlFor="bodyJson">Request-Body (JSON)</Label>
              <textarea
                id="bodyJson"
                value={bodyJson}
                onChange={(e) => setBodyJson(e.target.value)}
                disabled={template.is_system}
                rows={8}
                className="w-full rounded-md border border-input bg-background px-3 py-2 font-mono text-sm"
              />
            </div>
            <div>
              <Label htmlFor="outputMapping">Output-Mapping (JSON)</Label>
              <textarea
                id="outputMapping"
                value={outputMapping}
                onChange={(e) => setOutputMapping(e.target.value)}
                disabled={template.is_system}
                rows={3}
                className="w-full rounded-md border border-input bg-background px-3 py-2 font-mono text-sm"
              />
            </div>

            {message && (
              <p className={`text-sm ${isError ? "text-red-600" : "text-green-600"}`}>{message}</p>
            )}

            {!template.is_system && (
              <Button type="submit" disabled={saving}>
                {saving ? "Speichern..." : "Speichern"}
              </Button>
            )}
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
