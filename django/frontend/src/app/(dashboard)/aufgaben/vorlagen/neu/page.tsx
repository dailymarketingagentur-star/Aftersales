"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useTenant } from "@/hooks/use-tenant";
import { apiFetch } from "@/lib/api";
import type { JiraTemplateSummary } from "@/types/task";

const ACTION_TYPE_OPTIONS = [
  { value: "manual", label: "Manuell" },
  { value: "email", label: "E-Mail" },
  { value: "package", label: "Paket" },
  { value: "phone", label: "Telefonat" },
  { value: "meeting", label: "Meeting" },
  { value: "document", label: "Dokument" },
  { value: "jira_project", label: "Jira-Projekt" },
  { value: "jira_ticket", label: "Jira-Ticket" },
];

const PRIORITY_OPTIONS = [
  { value: "low", label: "Niedrig" },
  { value: "medium", label: "Mittel" },
  { value: "high", label: "Hoch" },
  { value: "critical", label: "Kritisch" },
];

export default function NeueVorlagePage() {
  const router = useRouter();
  const { currentTenantId } = useTenant();

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
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

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

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) {
      setError("Name ist erforderlich.");
      return;
    }
    setSaving(true);
    setError("");

    try {
      await apiFetch("/api/v1/tasks/templates/", {
        method: "POST",
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
      router.push("/aufgaben/vorlagen");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Fehler beim Erstellen.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Neue Aufgaben-Vorlage</h1>
        <Link href="/aufgaben/vorlagen">
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
                <Label htmlFor="name">Name *</Label>
                <Input
                  id="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  placeholder="z.B. Follow-up Anruf"
                />
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
                placeholder="Was soll bei dieser Aufgabe getan werden?"
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

            {/* Phase/day_offset collapsed */}
            <details className="rounded border p-3">
              <summary className="cursor-pointer text-sm text-muted-foreground">
                Erweiterte Einstellungen (Phase, Tag-Offset & Jira)
              </summary>
              <div className="mt-3 grid gap-4 md:grid-cols-2">
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
                <div className="mt-4 space-y-3">
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
            </details>

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
