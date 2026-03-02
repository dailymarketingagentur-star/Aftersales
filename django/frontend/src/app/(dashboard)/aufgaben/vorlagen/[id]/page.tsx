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
import type { JiraTemplateSummary, TaskTemplate } from "@/types/task";

const ACTION_TYPE_OPTIONS = [
  { value: "email", label: "E-Mail" },
  { value: "package", label: "Paket" },
  { value: "phone", label: "Telefonat" },
  { value: "meeting", label: "Meeting" },
  { value: "document", label: "Dokument" },
  { value: "jira_project", label: "Jira-Projekt" },
  { value: "jira_ticket", label: "Jira-Ticket" },
  { value: "manual", label: "Manuell" },
];

const PRIORITY_OPTIONS = [
  { value: "low", label: "Niedrig" },
  { value: "medium", label: "Mittel" },
  { value: "high", label: "Hoch" },
  { value: "critical", label: "Kritisch" },
];

export default function VorlageDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { currentTenantId } = useTenant();
  const [template, setTemplate] = useState<TaskTemplate | null>(null);

  // Editable fields
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [actionType, setActionType] = useState("manual");
  const [phase, setPhase] = useState(0);
  const [dayOffset, setDayOffset] = useState(0);
  const [priority, setPriority] = useState("medium");
  const [subtasks, setSubtasks] = useState("");
  const [actionTemplate, setActionTemplate] = useState<string | null>(null);
  const [actionSequence, setActionSequence] = useState<string | null>(null);
  const [jiraTemplates, setJiraTemplates] = useState<JiraTemplateSummary[]>([]);
  const [jiraSequences, setJiraSequences] = useState<JiraTemplateSummary[]>([]);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [isError, setIsError] = useState(false);


  useEffect(() => {
    if (!currentTenantId || !id) return;
    apiFetch<TaskTemplate>(`/api/v1/tasks/templates/${id}/`, { tenantId: currentTenantId })
      .then((tpl) => {
        setTemplate(tpl);
        setName(tpl.name);
        setDescription(tpl.description);
        setActionType(tpl.action_type);
        setPhase(tpl.phase);
        setDayOffset(tpl.day_offset);
        setPriority(tpl.priority);
        setSubtasks(tpl.default_subtasks.join("\n"));
        setActionTemplate(tpl.action_template_id || null);
        setActionSequence(tpl.action_sequence_id || null);
      })
      .catch(() => {});
  }, [currentTenantId, id]);

  const isJiraType = actionType === "jira_project" || actionType === "jira_ticket";

  useEffect(() => {
    if (!currentTenantId || !isJiraType) return;
    apiFetch<JiraTemplateSummary[]>("/api/v1/integrations/templates/", { tenantId: currentTenantId })
      .then(setJiraTemplates)
      .catch(() => {});
    apiFetch<JiraTemplateSummary[]>("/api/v1/integrations/sequences/", { tenantId: currentTenantId })
      .then(setJiraSequences)
      .catch(() => {});
  }, [currentTenantId, isJiraType]);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setMessage("");
    try {
      const updated = await apiFetch<TaskTemplate>(`/api/v1/tasks/templates/${id}/`, {
        method: "PATCH",
        body: JSON.stringify({
          name,
          description,
          action_type: actionType,
          phase,
          day_offset: dayOffset,
          priority,
          default_subtasks: subtasks.split("\n").map((s) => s.trim()).filter(Boolean),
          action_template: actionTemplate || null,
          action_sequence: actionSequence || null,
        }),
        tenantId: currentTenantId!,
      });
      setTemplate(updated);
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
      await apiFetch(`/api/v1/tasks/templates/${id}/`, {
        method: "DELETE",
        tenantId: currentTenantId!,
      });
      router.push("/aufgaben/vorlagen");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Fehler beim Löschen.");
      setIsError(true);
    }
  }

  async function handleDuplicate() {
    if (!template) return;
    setSaving(true);
    setMessage("");
    try {
      const copy = await apiFetch<TaskTemplate>("/api/v1/tasks/templates/", {
        method: "POST",
        body: JSON.stringify({
          name: `${template.name} (Kopie)`,
          description: template.description,
          action_type: template.action_type,
          phase: template.phase,
          day_offset: template.day_offset,
          priority: template.priority,
          default_subtasks: template.default_subtasks,
          action_template: template.action_template_id || null,
          action_sequence: template.action_sequence_id || null,
        }),
        tenantId: currentTenantId!,
      });
      router.push(`/aufgaben/vorlagen/${copy.id}`);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Fehler beim Duplizieren.");
      setIsError(true);
    } finally {
      setSaving(false);
    }
  }

  if (!template) return <p className="text-sm text-muted-foreground">Laden...</p>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{template.name}</h1>
        <div className="flex gap-2">
          <Link href="/aufgaben/vorlagen">
            <Button variant="outline" size="sm">Zurück</Button>
          </Link>
          <Button variant="outline" size="sm" onClick={handleDuplicate} disabled={saving}>
            Duplizieren
          </Button>
          <Button variant="destructive" size="sm" onClick={handleDelete}>Löschen</Button>
        </div>
      </div>

      {/* Info-Card */}
      <Card>
        <CardHeader>
          <CardTitle>Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <p className="text-xs font-medium text-muted-foreground">Aktionstyp</p>
              <p className="text-sm">
                {ACTION_TYPE_OPTIONS.find((o) => o.value === template.action_type)?.label || template.action_type}
              </p>
            </div>
            <div>
              <p className="text-xs font-medium text-muted-foreground">Slug</p>
              <p className="font-mono text-sm">{template.slug}</p>
            </div>
          </div>
          {template.default_subtasks.length > 0 && (
            <div>
              <p className="mb-1 text-xs font-medium text-muted-foreground">Standard-Checkliste</p>
              <ul className="list-inside list-disc text-sm text-muted-foreground">
                {template.default_subtasks.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Verknüpfungen */}
          {(template.email_templates_detail?.length > 0 || template.action_template_slug || template.action_sequence_slug) && (
            <div>
              <p className="mb-1 text-xs font-medium text-muted-foreground">Verknüpfungen</p>
              <div className="flex flex-wrap gap-2">
                {template.email_templates_detail?.map((et) => (
                  <Link key={et.id} href={`/integrationen/email/vorlagen/${et.id}`} className="rounded bg-green-100 px-2 py-0.5 text-xs text-green-800 transition-colors hover:bg-green-200">
                    E-Mail: {et.name}
                  </Link>
                ))}
                {template.action_template_slug && (
                  template.action_template_id ? (
                    <Link href={`/integrationen/jira/vorlagen/${template.action_template_id}`} className="rounded bg-indigo-100 px-2 py-0.5 text-xs text-indigo-800 transition-colors hover:bg-indigo-200">
                      Jira-Aktion: {template.action_template_slug}
                    </Link>
                  ) : (
                    <span className="rounded bg-indigo-100 px-2 py-0.5 text-xs text-indigo-800">
                      Jira-Aktion: {template.action_template_slug}
                    </span>
                  )
                )}
                {template.action_sequence_slug && (
                  template.action_sequence_id ? (
                    <Link href={`/integrationen/jira/sequenzen/${template.action_sequence_id}`} className="rounded bg-indigo-100 px-2 py-0.5 text-xs text-indigo-800 transition-colors hover:bg-indigo-200">
                      Jira-Sequenz: {template.action_sequence_slug}
                    </Link>
                  ) : (
                    <span className="rounded bg-indigo-100 px-2 py-0.5 text-xs text-indigo-800">
                      Jira-Sequenz: {template.action_sequence_slug}
                    </span>
                  )
                )}
              </div>
            </div>
          )}

          {/* Erweiterte Einstellungen (Phase/day_offset) — collapsed */}
          <div>
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
            >
              <span className={`transition-transform ${showAdvanced ? "rotate-90" : ""}`}>&#9654;</span>
              Erweiterte Einstellungen (Phase & Tag-Offset)
            </button>
            {showAdvanced && (
              <div className="mt-2 grid gap-4 rounded border p-3 sm:grid-cols-2">
                <div>
                  <p className="text-xs font-medium text-muted-foreground">Phase</p>
                  <p className="text-sm">Phase {template.phase}</p>
                </div>
                <div>
                  <p className="text-xs font-medium text-muted-foreground">Tag-Offset</p>
                  <p className="text-sm">{template.day_offset > 0 ? "+" : ""}{template.day_offset}</p>
                </div>
                <p className="col-span-full text-xs text-muted-foreground">
                  Diese Werte werden als Vorschlag verwendet, wenn die Vorlage ohne Liste geladen wird.
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Bearbeiten-Formular */}
      <Card>
          <CardHeader>
            <CardTitle>Bearbeiten</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSave} className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <Label htmlFor="name">Name</Label>
                  <Input id="name" value={name} onChange={(e) => setName(e.target.value)} />
                </div>
                <div>
                  <Label htmlFor="actionType">Aktionstyp</Label>
                  <select
                    id="actionType"
                    value={actionType}
                    onChange={(e) => setActionType(e.target.value)}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    {ACTION_TYPE_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div>
                <Label htmlFor="description">Beschreibung</Label>
                <textarea
                  id="description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={3}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                />
              </div>
              <div>
                <Label htmlFor="priority">Priorität</Label>
                <select
                  id="priority"
                  value={priority}
                  onChange={(e) => setPriority(e.target.value)}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  {PRIORITY_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <Label htmlFor="subtasks">Standard-Checkliste (eine pro Zeile)</Label>
                <textarea
                  id="subtasks"
                  value={subtasks}
                  onChange={(e) => setSubtasks(e.target.value)}
                  rows={4}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  placeholder="Schritt 1&#10;Schritt 2&#10;Schritt 3"
                />
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <Label htmlFor="phase">Phase (0–10)</Label>
                  <Input
                    id="phase"
                    type="number"
                    min={0}
                    max={10}
                    value={phase}
                    onChange={(e) => setPhase(Number(e.target.value))}
                  />
                </div>
                <div>
                  <Label htmlFor="dayOffset">Tag-Offset</Label>
                  <Input
                    id="dayOffset"
                    type="number"
                    value={dayOffset}
                    onChange={(e) => setDayOffset(Number(e.target.value))}
                  />
                  <p className="mt-1 text-xs text-muted-foreground">
                    Wird als Vorschlag für Listen ohne eigenen Tag-Offset verwendet.
                  </p>
                </div>
              </div>
              {isJiraType && (
                <div className="space-y-3">
                  <div className="grid gap-4 md:grid-cols-2">
                    <div>
                      <Label htmlFor="actionTemplate">Jira-Aktionsvorlage</Label>
                      <select
                        id="actionTemplate"
                        value={actionTemplate || ""}
                        onChange={(e) => setActionTemplate(e.target.value || null)}
                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      >
                        <option value="">— Keine —</option>
                        {jiraTemplates.map((t) => (
                          <option key={t.id} value={t.id}>{t.name}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <Label htmlFor="actionSequence">Jira-Sequenz</Label>
                      <select
                        id="actionSequence"
                        value={actionSequence || ""}
                        onChange={(e) => setActionSequence(e.target.value || null)}
                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      >
                        <option value="">— Keine —</option>
                        {jiraSequences.map((s) => (
                          <option key={s.id} value={s.id}>{s.name}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <Link
                    href="/integrationen/jira/vorlagen/neu"
                    className="inline-flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-800 hover:underline"
                  >
                    Neue Jira-Vorlage erstellen &rarr;
                  </Link>
                </div>
              )}

              {message && (
                <p className={`text-sm ${isError ? "text-red-600" : "text-green-600"}`}>{message}</p>
              )}

              <Button type="submit" disabled={saving}>
                {saving ? "Speichern..." : "Speichern"}
              </Button>
            </form>
          </CardContent>
        </Card>
    </div>
  );
}
