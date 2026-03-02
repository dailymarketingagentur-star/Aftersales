"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useTenant } from "@/hooks/use-tenant";
import { apiFetch } from "@/lib/api";

export default function NeueWebhookVorlagePage() {
  const router = useRouter();
  const { currentTenantId } = useTenant();

  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [description, setDescription] = useState("");
  const [method, setMethod] = useState("POST");
  const [webhookUrl, setWebhookUrl] = useState("");
  const [authType, setAuthType] = useState("none");
  const [authCredentials, setAuthCredentials] = useState("{}");
  const [bodyJson, setBodyJson] = useState("{}");
  const [headersJson, setHeadersJson] = useState("{}");
  const [variables, setVariables] = useState("");
  const [outputMapping, setOutputMapping] = useState("{}");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError("");

    let parsedBody = {};
    let parsedHeaders = {};
    let parsedMapping = {};
    let parsedCreds = undefined;

    try {
      parsedBody = bodyJson.trim() ? JSON.parse(bodyJson) : {};
    } catch {
      setError("Body-JSON ist ungültig.");
      setSaving(false);
      return;
    }
    try {
      parsedHeaders = headersJson.trim() ? JSON.parse(headersJson) : {};
    } catch {
      setError("Headers-JSON ist ungültig.");
      setSaving(false);
      return;
    }
    try {
      parsedMapping = outputMapping.trim() ? JSON.parse(outputMapping) : {};
    } catch {
      setError("Output-Mapping-JSON ist ungültig.");
      setSaving(false);
      return;
    }
    if (authType !== "none" && authCredentials.trim() !== "{}") {
      try {
        parsedCreds = JSON.parse(authCredentials);
      } catch {
        setError("Auth-Credentials-JSON ist ungültig.");
        setSaving(false);
        return;
      }
    }

    try {
      await apiFetch("/api/v1/integrations/templates/", {
        method: "POST",
        body: JSON.stringify({
          name,
          slug,
          description,
          target_type: "webhook",
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
      router.push("/integrationen/webhooks/vorlagen");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Fehler beim Erstellen.");
    } finally {
      setSaving(false);
    }
  }

  const authHint: Record<string, string> = {
    none: "",
    bearer: '{"token": "dein-token"}',
    basic: '{"username": "user", "password": "pass"}',
    api_key: '{"header_name": "X-API-Key", "header_value": "dein-key"}',
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Neue Webhook-Vorlage</h1>
        <Link href="/integrationen/webhooks/vorlagen">
          <Button variant="outline" size="sm">Zurück</Button>
        </Link>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Vorlage erstellen</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleCreate} className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Label htmlFor="name">Name</Label>
                <Input id="name" value={name} onChange={(e) => setName(e.target.value)} required />
              </div>
              <div>
                <Label htmlFor="slug">Slug</Label>
                <Input id="slug" value={slug} onChange={(e) => setSlug(e.target.value)} required placeholder="mein-webhook" />
              </div>
            </div>
            <div>
              <Label htmlFor="description">Beschreibung</Label>
              <Input id="description" value={description} onChange={(e) => setDescription(e.target.value)} />
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Label htmlFor="method">HTTP-Methode</Label>
                <select
                  id="method"
                  value={method}
                  onChange={(e) => setMethod(e.target.value)}
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
                  required
                  placeholder="https://api.example.com/webhook"
                />
              </div>
            </div>

            {/* Auth */}
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Label htmlFor="authType">Authentifizierung</Label>
                <select
                  id="authType"
                  value={authType}
                  onChange={(e) => setAuthType(e.target.value)}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  <option value="none">Keine</option>
                  <option value="bearer">Bearer Token</option>
                  <option value="basic">Basic Auth</option>
                  <option value="api_key">API Key (Custom Header)</option>
                </select>
              </div>
              {authType !== "none" && (
                <div>
                  <Label htmlFor="authCredentials">Credentials (JSON)</Label>
                  <Input
                    id="authCredentials"
                    value={authCredentials}
                    onChange={(e) => setAuthCredentials(e.target.value)}
                    placeholder={authHint[authType]}
                  />
                  <p className="mt-1 text-xs text-muted-foreground">
                    Format: {authHint[authType]}
                  </p>
                </div>
              )}
            </div>

            <div>
              <Label htmlFor="variables">Variablen (kommagetrennt)</Label>
              <Input id="variables" value={variables} onChange={(e) => setVariables(e.target.value)} placeholder="CLIENT_NAME, CLIENT_EMAIL" />
            </div>
            <div>
              <Label htmlFor="headersJson">Extra-Headers (JSON)</Label>
              <textarea
                id="headersJson"
                value={headersJson}
                onChange={(e) => setHeadersJson(e.target.value)}
                rows={3}
                className="w-full rounded-md border border-input bg-background px-3 py-2 font-mono text-sm"
                placeholder='{"X-Custom-Header": "value"}'
              />
            </div>
            <div>
              <Label htmlFor="bodyJson">Request-Body (JSON)</Label>
              <textarea
                id="bodyJson"
                value={bodyJson}
                onChange={(e) => setBodyJson(e.target.value)}
                rows={8}
                className="w-full rounded-md border border-input bg-background px-3 py-2 font-mono text-sm"
                placeholder='{"name": "{{CLIENT_NAME}}", "email": "{{CLIENT_EMAIL}}"}'
              />
            </div>
            <div>
              <Label htmlFor="outputMapping">Output-Mapping (JSON)</Label>
              <textarea
                id="outputMapping"
                value={outputMapping}
                onChange={(e) => setOutputMapping(e.target.value)}
                rows={3}
                className="w-full rounded-md border border-input bg-background px-3 py-2 font-mono text-sm"
                placeholder='{"id": "RESULT_ID"}'
              />
            </div>

            {error && <p className="text-sm text-red-600">{error}</p>}

            <Button type="submit" disabled={saving}>
              {saving ? "Erstellen..." : "Vorlage erstellen"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
