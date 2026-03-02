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
import type { TaskTemplate } from "@/types/task";

const ACTION_LABELS: Record<string, string> = {
  email: "E-Mail",
  package: "Paket",
  phone: "Telefonat",
  meeting: "Meeting",
  document: "Dokument",
  jira_project: "Jira-Projekt",
  jira_ticket: "Jira-Ticket",
  manual: "Manuell",
};

const PRIORITY_COLORS: Record<string, string> = {
  low: "bg-gray-100 text-gray-700",
  medium: "bg-blue-100 text-blue-700",
  high: "bg-orange-100 text-orange-700",
  critical: "bg-red-100 text-red-700",
};

const PRIORITY_LABELS: Record<string, string> = {
  low: "Niedrig",
  medium: "Mittel",
  high: "Hoch",
  critical: "Kritisch",
};

export default function NeueListePage() {
  const router = useRouter();
  const { currentTenantId } = useTenant();

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [templates, setTemplates] = useState<TaskTemplate[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!currentTenantId) return;
    apiFetch<TaskTemplate[]>("/api/v1/tasks/templates/", { tenantId: currentTenantId })
      .then(setTemplates)
      .catch(() => {});
  }, [currentTenantId]);

  // Gruppiert nach Aktionstyp
  const grouped = templates.reduce<Record<string, TaskTemplate[]>>((acc, t) => {
    const key = t.action_type;
    if (!acc[key]) acc[key] = [];
    acc[key].push(t);
    return acc;
  }, {});
  const actionTypes = Object.keys(grouped).sort((a, b) =>
    (ACTION_LABELS[a] || a).localeCompare(ACTION_LABELS[b] || b)
  );

  function toggleTemplate(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function toggleActionType(actionType: string) {
    const ids = grouped[actionType].map((t) => t.id);
    const allSelected = ids.every((id) => selected.has(id));
    setSelected((prev) => {
      const next = new Set(prev);
      ids.forEach((id) => {
        if (allSelected) next.delete(id);
        else next.add(id);
      });
      return next;
    });
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) {
      setError("Name ist erforderlich.");
      return;
    }
    setSaving(true);
    setError("");

    // Template-IDs in alphabetischer Reihenfolge
    const orderedIds = templates
      .filter((t) => selected.has(t.id))
      .sort((a, b) => a.name.localeCompare(b.name))
      .map((t) => t.id);

    try {
      await apiFetch("/api/v1/tasks/lists/", {
        method: "POST",
        body: JSON.stringify({
          name,
          description,
          template_ids: orderedIds,
        }),
        tenantId: currentTenantId!,
      });
      router.push("/aufgaben/listen");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Fehler beim Erstellen.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Neue Aufgabenliste</h1>
        <Link href="/aufgaben/listen">
          <Button variant="outline" size="sm">Zurück</Button>
        </Link>
      </div>

      <form onSubmit={handleCreate} className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="name">Name *</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                placeholder="z.B. Onboarding Premium"
              />
            </div>
            <div>
              <Label htmlFor="description">Beschreibung</Label>
              <Input
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Optionale Beschreibung des Workflows"
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Vorlagen auswählen ({selected.size})</CardTitle>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelected(new Set(templates.map((t) => t.id)))}
                >
                  Alle
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelected(new Set())}
                >
                  Keine
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <p className="mb-3 text-xs text-muted-foreground">
              Gruppen und Tag-Offsets können nach dem Erstellen auf der Detail-Seite zugewiesen werden.
            </p>
            <div className="space-y-4">
              {actionTypes.map((actionType) => {
                const actionTemplates = grouped[actionType].sort((a, b) => a.name.localeCompare(b.name));
                const ids = actionTemplates.map((t) => t.id);
                const allChecked = ids.every((id) => selected.has(id));
                const someChecked = !allChecked && ids.some((id) => selected.has(id));

                return (
                  <div key={actionType}>
                    <label className="mb-1 flex cursor-pointer items-center gap-2">
                      <input
                        type="checkbox"
                        checked={allChecked}
                        ref={(el) => { if (el) el.indeterminate = someChecked; }}
                        onChange={() => toggleActionType(actionType)}
                        className="h-4 w-4 rounded border-gray-300"
                      />
                      <span className="text-sm font-semibold">
                        {ACTION_LABELS[actionType] || actionType}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        ({actionTemplates.length})
                      </span>
                    </label>
                    <div className="ml-6 space-y-1">
                      {actionTemplates.map((tpl) => (
                        <label
                          key={tpl.id}
                          className="flex cursor-pointer items-start gap-2 rounded px-2 py-1 hover:bg-muted/50"
                        >
                          <input
                            type="checkbox"
                            checked={selected.has(tpl.id)}
                            onChange={() => toggleTemplate(tpl.id)}
                            className="mt-0.5 h-4 w-4 rounded border-gray-300"
                          />
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <span className="text-sm">{tpl.name}</span>
                              {tpl.is_system && (
                                <span className="rounded bg-purple-100 px-1.5 py-0.5 text-xs text-purple-800">System</span>
                              )}
                            </div>
                            <div className="flex gap-2">
                              <span className={`rounded px-1.5 py-0.5 text-xs font-medium ${PRIORITY_COLORS[tpl.priority]}`}>
                                {PRIORITY_LABELS[tpl.priority]}
                              </span>
                            </div>
                          </div>
                        </label>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <Button type="submit" disabled={saving}>
          {saving ? "Erstellen..." : "Liste erstellen"}
        </Button>
      </form>
    </div>
  );
}
