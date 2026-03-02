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

const TEMPLATE_DETAILS: Record<string, {
  summary: string;
  exampleContext: Record<string, string>;
  outputExplanation: string;
}> = {
  "create-jira-project": {
    summary: "Erstellt ein neues Projekt in Jira für einen Mandanten.",
    exampleContext: {
      PROJECT_KEY: "MUSTERGMB",
      PROJECT_NAME: "Muster GmbH",
      LEAD_ACCOUNT_ID: "(Jira-Account-ID des Verantwortlichen)",
    },
    outputExplanation: "Speichert die Jira-Projekt-ID und den Projekt-Key für spätere Referenz.",
  },
  "create-jira-issue": {
    summary: "Erstellt ein neues Ticket (Issue) in einem bestehenden Jira-Projekt.",
    exampleContext: {
      PROJECT_KEY: "MUSTERGMB",
      ISSUE_SUMMARY: "Onboarding: Muster GmbH",
      ISSUE_DESCRIPTION: "Onboarding-Ticket für Muster GmbH",
      ISSUE_TYPE: "Task",
    },
    outputExplanation: "Speichert den Ticket-Key (z.B. MUSTERGMB-1) und die Ticket-ID.",
  },
  "update-jira-issue": {
    summary: "Aktualisiert ein bestehendes Jira-Ticket (z.B. Titel ändern).",
    exampleContext: {
      ISSUE_KEY: "MUSTERGMB-1",
      ISSUE_SUMMARY: "Neuer Titel",
    },
    outputExplanation: "Aktualisiert das Ticket direkt in Jira. Keine neuen Daten werden gespeichert.",
  },
};

export default function VorlageDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { currentTenantId } = useTenant();
  const [template, setTemplate] = useState<ActionTemplate | null>(null);
  const [activeTab, setActiveTab] = useState<"visual" | "json">("visual");

  // Editable fields
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [description, setDescription] = useState("");
  const [method, setMethod] = useState("POST");
  const [endpoint, setEndpoint] = useState("");
  const [bodyJson, setBodyJson] = useState("");
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
        setEndpoint(tpl.endpoint);
        setBodyJson(JSON.stringify(tpl.body_json, null, 2));
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
    try {
      let parsedBody = {};
      let parsedMapping = {};
      try {
        parsedBody = bodyJson.trim() ? JSON.parse(bodyJson) : {};
      } catch {
        setMessage("Body-JSON ist ungültig.");
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

      await apiFetch(`/api/v1/integrations/templates/${id}/`, {
        method: "PATCH",
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
      router.push("/integrationen/jira/vorlagen");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Fehler beim Löschen.");
      setIsError(true);
    }
  }

  if (!template) return <p>Laden...</p>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{template.name}</h1>
        <div className="flex gap-2">
          <Link href="/integrationen/jira/vorlagen">
            <Button variant="outline" size="sm">Zurück</Button>
          </Link>
          {!template.is_system && (
            <Button variant="destructive" size="sm" onClick={handleDelete}>Löschen</Button>
          )}
        </div>
      </div>

      {template.is_system && (
        <p className="text-sm text-muted-foreground">
          System-Vorlagen können nicht bearbeitet werden. Erstellen Sie eine eigene Vorlage als Kopie.
        </p>
      )}

      {/* Was passiert? */}
      {TEMPLATE_DETAILS[template.slug] && (
        <Card>
          <CardHeader>
            <CardTitle>Was passiert?</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm">{TEMPLATE_DETAILS[template.slug].summary}</p>
            <div>
              <p className="mb-2 text-sm font-medium">Beispielwerte:</p>
              <div className="rounded-md bg-muted p-3">
                <dl className="space-y-1 text-sm">
                  {Object.entries(TEMPLATE_DETAILS[template.slug].exampleContext).map(([key, value]) => (
                    <div key={key} className="flex gap-2">
                      <dt className="font-mono font-medium text-muted-foreground">{key}:</dt>
                      <dd className="text-foreground">{value}</dd>
                    </div>
                  ))}
                </dl>
              </div>
            </div>
            <div>
              <p className="mb-1 text-sm font-medium">Ergebnis:</p>
              <p className="text-sm text-muted-foreground">{TEMPLATE_DETAILS[template.slug].outputExplanation}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tab Toggle */}
      <div className="flex gap-2">
        <Button
          variant={activeTab === "visual" ? "default" : "outline"}
          size="sm"
          onClick={() => setActiveTab("visual")}
        >
          Visuell
        </Button>
        <Button
          variant={activeTab === "json" ? "default" : "outline"}
          size="sm"
          onClick={() => setActiveTab("json")}
        >
          JSON
        </Button>
      </div>

      {activeTab === "visual" ? (
        <Card>
          <CardHeader>
            <CardTitle>{template.is_system ? "Technische Details" : "Vorlage bearbeiten"}</CardTitle>
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
                  <Label htmlFor="endpoint">Endpoint</Label>
                  <Input
                    id="endpoint"
                    value={endpoint}
                    onChange={(e) => setEndpoint(e.target.value)}
                    disabled={template.is_system}
                    placeholder="/rest/api/3/..."
                  />
                </div>
              </div>
              <div>
                <Label htmlFor="variables">Variablen (kommagetrennt)</Label>
                <Input
                  id="variables"
                  value={variables}
                  onChange={(e) => setVariables(e.target.value)}
                  disabled={template.is_system}
                  placeholder="PROJECT_KEY, ISSUE_SUMMARY"
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
                  rows={4}
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
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>JSON-Ansicht</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="overflow-auto rounded-md bg-muted p-4 font-mono text-sm">
              {JSON.stringify(template, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
