"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";
import type { ClientIntegrationData, IntegrationType } from "@/types/integration";

interface IntegrationSectionProps {
  slug: string;
  tenantId: string;
  clientName: string;
}

export function IntegrationSection({ slug, tenantId, clientName }: IntegrationSectionProps) {
  const [types, setTypes] = useState<IntegrationType[]>([]);
  const [dataMap, setDataMap] = useState<Record<string, ClientIntegrationData>>({});
  const [editingType, setEditingType] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [showJiraModal, setShowJiraModal] = useState(false);
  const [showConfluenceModal, setShowConfluenceModal] = useState(false);

  useEffect(() => {
    if (!tenantId) return;

    apiFetch<IntegrationType[]>("/api/v1/integrations/types/", { tenantId })
      .then(setTypes)
      .catch(() => {});

    apiFetch<ClientIntegrationData[]>(`/api/v1/clients/${slug}/integrations/`, { tenantId })
      .then((items) => {
        const map: Record<string, ClientIntegrationData> = {};
        for (const item of items) {
          map[item.integration_type] = item;
        }
        setDataMap(map);
      })
      .catch(() => {});
  }, [tenantId, slug]);

  const enabledTypes = types.filter((t) => t.is_enabled && t.fields.length > 0);

  if (enabledTypes.length === 0) return null;

  function startEditing(type: IntegrationType) {
    const existing = dataMap[type.key]?.data || {};
    const form: Record<string, string> = {};
    for (const f of type.fields) {
      form[f.key] = existing[f.key] || "";
    }
    setEditForm(form);
    setEditingType(type.key);
    setError("");
  }

  async function handleSave(type: IntegrationType) {
    setSaving(true);
    setError("");
    try {
      const result = await apiFetch<ClientIntegrationData>(
        `/api/v1/clients/${slug}/integrations/`,
        {
          method: "PUT",
          body: JSON.stringify({
            integration_type: type.key,
            data: editForm,
          }),
          tenantId,
        }
      );
      setDataMap((prev) => ({ ...prev, [type.key]: result }));
      setEditingType(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Fehler beim Speichern.");
    } finally {
      setSaving(false);
    }
  }

  /** Check if Jira fields are empty (no project linked yet). */
  function isJiraUnlinked(type: IntegrationType): boolean {
    if (type.key !== "jira") return false;
    const data = dataMap[type.key]?.data || {};
    return !data.project_key && !data.project_id;
  }

  /** Check if Confluence page is not yet synced. */
  function isConfluenceUnsynced(type: IntegrationType): boolean {
    if (type.key !== "confluence") return false;
    const data = dataMap[type.key]?.data || {};
    return !data.page_id;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Integrationen</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {enabledTypes.map((type) => {
          const isEditing = editingType === type.key;
          const data = dataMap[type.key]?.data || {};

          return (
            <div key={type.key}>
              <div className="mb-2 flex items-center justify-between">
                <h4 className="text-sm font-semibold">{type.label}</h4>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => (isEditing ? setEditingType(null) : startEditing(type))}
                >
                  {isEditing ? "Abbrechen" : "Bearbeiten"}
                </Button>
              </div>

              {isEditing ? (
                <div className="space-y-3">
                  {type.fields.map((f) => (
                    <div key={f.key} className="space-y-1">
                      <Label htmlFor={`${type.key}-${f.key}`}>{f.label}</Label>
                      <Input
                        id={`${type.key}-${f.key}`}
                        type={f.field_type === "url" ? "url" : "text"}
                        placeholder={f.field_type === "url" ? "https://..." : ""}
                        value={editForm[f.key] || ""}
                        onChange={(e) =>
                          setEditForm((prev) => ({ ...prev, [f.key]: e.target.value }))
                        }
                      />
                    </div>
                  ))}
                  {error && <p className="text-sm text-destructive">{error}</p>}
                  <Button size="sm" disabled={saving} onClick={() => handleSave(type)}>
                    {saving ? "..." : "Speichern"}
                  </Button>
                </div>
              ) : (
                <>
                  <dl className="grid grid-cols-2 gap-3 text-sm">
                    {type.fields.map((f) => {
                      const value = data[f.key];
                      return (
                        <div key={f.key}>
                          <dt className="text-muted-foreground">{f.label}</dt>
                          <dd>
                            {value ? (
                              f.field_type === "url" ? (
                                <a
                                  href={value}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-primary underline underline-offset-4 hover:text-primary/80"
                                >
                                  {value}
                                </a>
                              ) : (
                                value
                              )
                            ) : (
                              "\u2014"
                            )}
                          </dd>
                        </div>
                      );
                    })}
                  </dl>

                  {isJiraUnlinked(type) && (
                    <div className="mt-3">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setShowJiraModal(true)}
                      >
                        Jira-Projekt anlegen
                      </Button>
                    </div>
                  )}

                  {type.key === "confluence" && isConfluenceUnsynced(type) && (
                    <div className="mt-3">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setShowConfluenceModal(true)}
                      >
                        Confluence-Seite erstellen
                      </Button>
                    </div>
                  )}

                  {type.key === "confluence" && !isConfluenceUnsynced(type) && (
                    <div className="mt-3 flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setShowConfluenceModal(true)}
                      >
                        Key-Facts synchronisieren
                      </Button>
                      {data.page_url && (
                        <a
                          href={data.page_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm text-primary underline underline-offset-4 hover:text-primary/80"
                        >
                          In Confluence öffnen
                        </a>
                      )}
                    </div>
                  )}
                </>
              )}

              {enabledTypes.indexOf(type) < enabledTypes.length - 1 && (
                <hr className="mt-4" />
              )}
            </div>
          );
        })}
      </CardContent>

      {showJiraModal && (
        <CreateJiraProjectModal
          slug={slug}
          tenantId={tenantId}
          clientName={clientName}
          onClose={() => setShowJiraModal(false)}
          onCreated={(result) => {
            setDataMap((prev) => ({ ...prev, jira: result }));
            setShowJiraModal(false);
          }}
        />
      )}

      {showConfluenceModal && (
        <SyncConfluenceModal
          slug={slug}
          tenantId={tenantId}
          defaultSpaceKey={dataMap["jira"]?.data?.project_key || ""}
          existingPageId={dataMap["confluence"]?.data?.page_id || ""}
          onClose={() => setShowConfluenceModal(false)}
          onSynced={(result) => {
            setDataMap((prev) => ({ ...prev, confluence: result }));
            setShowConfluenceModal(false);
          }}
        />
      )}
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Modal: Jira-Projekt anlegen
// ---------------------------------------------------------------------------

function generateProjectKey(name: string): string {
  const words = name.trim().split(/\s+/);
  if (words.length >= 2) {
    return words
      .map((w) => w[0])
      .join("")
      .toUpperCase()
      .replace(/[^A-Z]/g, "")
      .slice(0, 10);
  }
  // Single word: take first 4 uppercase chars
  return name
    .toUpperCase()
    .replace(/[^A-Z]/g, "")
    .slice(0, 4);
}

function CreateJiraProjectModal({
  slug,
  tenantId,
  clientName,
  onClose,
  onCreated,
}: {
  slug: string;
  tenantId: string;
  clientName: string;
  onClose: () => void;
  onCreated: (data: ClientIntegrationData) => void;
}) {
  const [projectName, setProjectName] = useState(clientName);
  const [projectKey, setProjectKey] = useState(() => generateProjectKey(clientName));
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit() {
    if (!projectName.trim() || !projectKey.trim()) return;
    setSubmitting(true);
    setError("");
    try {
      const result = await apiFetch<ClientIntegrationData>(
        `/api/v1/clients/${slug}/integrations/jira/create-project/`,
        {
          method: "POST",
          body: JSON.stringify({
            project_name: projectName.trim(),
            project_key: projectKey.trim().toUpperCase(),
          }),
          tenantId,
        }
      );
      onCreated(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Fehler beim Erstellen des Jira-Projekts.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="mx-4 w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Jira-Projekt anlegen</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            ✕
          </button>
        </div>

        <div className="space-y-4">
          <div className="space-y-1">
            <label className="block text-sm font-medium text-gray-700">Projektname</label>
            <input
              type="text"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            />
          </div>

          <div className="space-y-1">
            <label className="block text-sm font-medium text-gray-700">
              Projekt-Key <span className="text-xs text-gray-400">(2-10 Zeichen, Großbuchstaben + Ziffern)</span>
            </label>
            <input
              type="text"
              value={projectKey}
              onChange={(e) => setProjectKey(e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 10))}
              maxLength={10}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm font-mono uppercase"
            />
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <div className="flex justify-end gap-2">
            <button
              onClick={onClose}
              className="rounded-md border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
            >
              Abbrechen
            </button>
            <button
              onClick={handleSubmit}
              disabled={submitting || !projectName.trim() || projectKey.trim().length < 2}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {submitting ? "Erstelle…" : "Projekt erstellen"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}


// ---------------------------------------------------------------------------
// Modal: Confluence-Seite synchronisieren
// ---------------------------------------------------------------------------

function SyncConfluenceModal({
  slug,
  tenantId,
  defaultSpaceKey,
  existingPageId,
  onClose,
  onSynced,
}: {
  slug: string;
  tenantId: string;
  defaultSpaceKey: string;
  existingPageId: string;
  onClose: () => void;
  onSynced: (data: ClientIntegrationData) => void;
}) {
  const [spaceKey, setSpaceKey] = useState(defaultSpaceKey);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const isUpdate = !!existingPageId;

  async function handleSubmit() {
    if (!spaceKey.trim()) return;
    setSubmitting(true);
    setError("");
    setSuccess("");
    try {
      const result = await apiFetch<ClientIntegrationData>(
        `/api/v1/clients/${slug}/integrations/confluence/sync/`,
        {
          method: "POST",
          body: JSON.stringify({ space_key: spaceKey.trim() }),
          tenantId,
        }
      );
      setSuccess(isUpdate ? "Key-Facts erfolgreich synchronisiert!" : "Confluence-Seite erstellt!");
      setTimeout(() => onSynced(result), 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Fehler bei der Confluence-Synchronisation.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="mx-4 w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">
            {isUpdate ? "Key-Facts synchronisieren" : "Confluence-Seite erstellen"}
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            ✕
          </button>
        </div>

        <div className="space-y-4">
          <div className="space-y-1">
            <label className="block text-sm font-medium text-gray-700">
              Space-Key{" "}
              <span className="text-xs text-gray-400">
                (Confluence-Space, in dem die Seite erstellt wird)
              </span>
            </label>
            <input
              type="text"
              value={spaceKey}
              onChange={(e) => setSpaceKey(e.target.value.toUpperCase().replace(/[^A-Z0-9_]/g, ""))}
              placeholder="z.B. PROJ"
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm font-mono uppercase"
            />
          </div>

          <p className="text-xs text-gray-500">
            {isUpdate
              ? "Die bestehende Confluence-Seite wird mit den aktuellen Key-Facts aktualisiert."
              : "Es wird eine neue Seite mit Mandanten-Infos und Key-Facts im angegebenen Space erstellt."}
          </p>

          {error && <p className="text-sm text-red-600">{error}</p>}
          {success && <p className="text-sm text-green-600">{success}</p>}

          <div className="flex justify-end gap-2">
            <button
              onClick={onClose}
              className="rounded-md border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
            >
              Abbrechen
            </button>
            <button
              onClick={handleSubmit}
              disabled={submitting || !spaceKey.trim() || !!success}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {submitting ? "Synchronisiere…" : isUpdate ? "Synchronisieren" : "Seite erstellen"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
