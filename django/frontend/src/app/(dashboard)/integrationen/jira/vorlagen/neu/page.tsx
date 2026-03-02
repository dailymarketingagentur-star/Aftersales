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

export default function NeueVorlagePage() {
  const router = useRouter();
  const { currentTenantId } = useTenant();

  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [description, setDescription] = useState("");
  const [method, setMethod] = useState("POST");
  const [endpoint, setEndpoint] = useState("");
  const [bodyJson, setBodyJson] = useState("{}");
  const [variables, setVariables] = useState("");
  const [outputMapping, setOutputMapping] = useState("{}");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError("");

    let parsedBody = {};
    let parsedMapping = {};
    try {
      parsedBody = bodyJson.trim() ? JSON.parse(bodyJson) : {};
    } catch {
      setError("Body-JSON ist ungültig.");
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

    try {
      await apiFetch("/api/v1/integrations/templates/", {
        method: "POST",
        body: JSON.stringify({
          name,
          slug,
          description,
          method,
          endpoint,
          body_json: parsedBody,
          variables: variables.split(",").map((v) => v.trim()).filter(Boolean),
          output_mapping: parsedMapping,
        }),
        tenantId: currentTenantId!,
      });
      router.push("/integrationen/jira/vorlagen");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Fehler beim Erstellen.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Neue Vorlage</h1>
        <Link href="/integrationen/jira/vorlagen">
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
                <Input id="slug" value={slug} onChange={(e) => setSlug(e.target.value)} required placeholder="meine-aktion" />
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
                <Label htmlFor="endpoint">Endpoint</Label>
                <Input id="endpoint" value={endpoint} onChange={(e) => setEndpoint(e.target.value)} required placeholder="/rest/api/3/issue" />
              </div>
            </div>
            <div>
              <Label htmlFor="variables">Variablen (kommagetrennt)</Label>
              <Input id="variables" value={variables} onChange={(e) => setVariables(e.target.value)} placeholder="PROJECT_KEY, ISSUE_SUMMARY" />
            </div>
            <div>
              <Label htmlFor="bodyJson">Request-Body (JSON)</Label>
              <textarea
                id="bodyJson"
                value={bodyJson}
                onChange={(e) => setBodyJson(e.target.value)}
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
                rows={4}
                className="w-full rounded-md border border-input bg-background px-3 py-2 font-mono text-sm"
                placeholder='{"id": "ISSUE_ID", "key": "ISSUE_KEY"}'
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
