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
import type { TaskList, TaskListItem, TaskTemplate, TaskListUsageClient } from "@/types/task";

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

const PRIORITY_LABELS: Record<string, string> = {
  low: "Niedrig",
  medium: "Mittel",
  high: "Hoch",
  critical: "Kritisch",
};

const PRIORITY_COLORS: Record<string, string> = {
  low: "bg-gray-100 text-gray-700",
  medium: "bg-blue-100 text-blue-700",
  high: "bg-orange-100 text-orange-700",
  critical: "bg-red-100 text-red-700",
};

interface ServiceType {
  id: string;
  name: string;
  slug: string;
}

export default function ListeDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { currentTenantId } = useTenant();

  const [list, setList] = useState<TaskList | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [isError, setIsError] = useState(false);

  // Template-Picker
  const [allTemplates, setAllTemplates] = useState<TaskTemplate[]>([]);
  const [showPicker, setShowPicker] = useState(false);

  // Service-Typen
  const [serviceTypes, setServiceTypes] = useState<ServiceType[]>([]);
  const [selectedServiceType, setSelectedServiceType] = useState<string>("");

  // Verwendet-bei
  const [usageClients, setUsageClients] = useState<TaskListUsageClient[]>([]);

  useEffect(() => {
    if (!currentTenantId || !id) return;
    apiFetch<TaskList>(`/api/v1/tasks/lists/${id}/`, { tenantId: currentTenantId })
      .then((data) => {
        setList(data);
        setName(data.name);
        setDescription(data.description);
        setSelectedServiceType(data.default_for_service_type || "");
      })
      .catch(() => {});
  }, [currentTenantId, id]);

  useEffect(() => {
    if (!currentTenantId) return;
    apiFetch<TaskTemplate[]>("/api/v1/tasks/templates/", { tenantId: currentTenantId })
      .then(setAllTemplates)
      .catch(() => {});
    apiFetch<ServiceType[]>("/api/v1/service-types/", { tenantId: currentTenantId })
      .then(setServiceTypes)
      .catch(() => {});
    apiFetch<TaskListUsageClient[]>(`/api/v1/tasks/lists/${id}/usage/`, { tenantId: currentTenantId })
      .then(setUsageClients)
      .catch(() => {});
  }, [currentTenantId, id]);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (!list || list.is_system) return;
    setSaving(true);
    setMessage("");
    try {
      const body: Record<string, unknown> = { name, description };
      if (selectedServiceType !== (list.default_for_service_type || "")) {
        body.default_for_service_type = selectedServiceType || null;
      }
      const updated = await apiFetch<TaskList>(`/api/v1/tasks/lists/${id}/`, {
        method: "PATCH",
        body: JSON.stringify(body),
        tenantId: currentTenantId!,
      });
      setList(updated);
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
    if (!confirm("Aufgabenliste wirklich löschen?")) return;
    try {
      await apiFetch(`/api/v1/tasks/lists/${id}/`, {
        method: "DELETE",
        tenantId: currentTenantId!,
      });
      router.push("/aufgaben/listen");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Fehler beim Löschen.");
      setIsError(true);
    }
  }

  async function handleDuplicate() {
    try {
      const newList = await apiFetch<TaskList>(`/api/v1/tasks/lists/${id}/duplicate/`, {
        method: "POST",
        body: JSON.stringify({}),
        tenantId: currentTenantId!,
      });
      router.push(`/aufgaben/listen/${newList.id}`);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Fehler beim Duplizieren.");
      setIsError(true);
    }
  }

  async function handleAddTemplate(templateId: string) {
    if (!list) return;
    const currentIds = list.items.map((i) => i.task_template);
    if (currentIds.includes(templateId)) return;
    const newIds = [...currentIds, templateId];
    try {
      const updated = await apiFetch<TaskList>(`/api/v1/tasks/lists/${id}/`, {
        method: "PATCH",
        body: JSON.stringify({ template_ids: newIds }),
        tenantId: currentTenantId!,
      });
      setList(updated);
      setShowPicker(false);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Fehler beim Hinzufügen.");
      setIsError(true);
    }
  }

  async function handleRemoveTemplate(templateId: string) {
    if (!list) return;
    const newIds = list.items
      .filter((i) => i.task_template !== templateId)
      .map((i) => i.task_template);
    try {
      const updated = await apiFetch<TaskList>(`/api/v1/tasks/lists/${id}/`, {
        method: "PATCH",
        body: JSON.stringify({ template_ids: newIds }),
        tenantId: currentTenantId!,
      });
      setList(updated);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Fehler beim Entfernen.");
      setIsError(true);
    }
  }

  // Reorder: Move item up or down
  async function handleMoveItem(index: number, direction: "up" | "down") {
    if (!list) return;
    const items = [...list.items];
    const swapIndex = direction === "up" ? index - 1 : index + 1;
    if (swapIndex < 0 || swapIndex >= items.length) return;

    [items[index], items[swapIndex]] = [items[swapIndex], items[index]];
    const itemIds = items.map((i) => i.id);

    try {
      const updated = await apiFetch<TaskList>(`/api/v1/tasks/lists/${id}/reorder/`, {
        method: "PATCH",
        body: JSON.stringify({ item_ids: itemIds }),
        tenantId: currentTenantId!,
      });
      setList(updated);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Fehler beim Umsortieren.");
      setIsError(true);
    }
  }

  // Inline-Edit: group_label oder day_offset eines Items
  async function handleItemUpdate(item: TaskListItem, field: "group_label" | "day_offset", value: string) {
    const updateValue = field === "day_offset"
      ? (value === "" ? null : Number(value))
      : value;
    try {
      const updated = await apiFetch<TaskList>(`/api/v1/tasks/lists/${id}/`, {
        method: "PATCH",
        body: JSON.stringify({
          item_updates: [{ id: item.id, [field]: updateValue }],
        }),
        tenantId: currentTenantId!,
      });
      setList(updated);
    } catch {
      // silent
    }
  }

  if (!list) return <p className="text-sm text-muted-foreground">Laden...</p>;

  const existingIds = new Set(list.items.map((i) => i.task_template));
  const availableTemplates = allTemplates.filter((t) => !existingIds.has(t.id));

  // Gruppen für Datalist-Suggestions
  const existingGroups = [...new Set(list.items.map((i) => i.group_label).filter(Boolean))];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{list.name}</h1>
        <div className="flex gap-2">
          <Link href="/aufgaben/listen">
            <Button variant="outline" size="sm">Zurück</Button>
          </Link>
          <Button variant="outline" size="sm" onClick={handleDuplicate}>Duplizieren</Button>
          {!list.is_system && (
            <Button variant="destructive" size="sm" onClick={handleDelete}>Löschen</Button>
          )}
        </div>
      </div>

      {list.is_system && (
        <p className="text-sm text-muted-foreground">
          System-Listen können nicht bearbeitet werden. Dupliziere sie, um eine eigene Version zu erstellen.
        </p>
      )}

      {/* Name/Beschreibung/Service-Typ bearbeiten */}
      {!list.is_system && (
        <Card>
          <CardHeader>
            <CardTitle>Details bearbeiten</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSave} className="space-y-4">
              <div>
                <Label htmlFor="name">Name</Label>
                <Input id="name" value={name} onChange={(e) => setName(e.target.value)} />
              </div>
              <div>
                <Label htmlFor="description">Beschreibung</Label>
                <Input id="description" value={description} onChange={(e) => setDescription(e.target.value)} />
              </div>
              {serviceTypes.length > 0 && (
                <div>
                  <Label htmlFor="serviceType">Standard für Service-Typ</Label>
                  <select
                    id="serviceType"
                    value={selectedServiceType}
                    onChange={(e) => setSelectedServiceType(e.target.value)}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    <option value="">Kein Standard</option>
                    {serviceTypes.map((st) => (
                      <option key={st.id} value={st.id}>{st.name}</option>
                    ))}
                  </select>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Wird im Mandanten-Modal als empfohlene Liste für diesen Service-Typ angezeigt.
                  </p>
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
      )}

      {/* Items-Tabelle */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Vorlagen ({list.items.length})</CardTitle>
            {!list.is_system && (
              <Button variant="outline" size="sm" onClick={() => setShowPicker(!showPicker)}>
                {showPicker ? "Schließen" : "Vorlage hinzufügen"}
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {/* Template-Picker */}
          {showPicker && availableTemplates.length > 0 && (
            <div className="mb-4 rounded-md border p-3">
              <p className="mb-2 text-sm font-medium">Vorlage auswählen:</p>
              <div className="max-h-48 space-y-1 overflow-y-auto">
                {availableTemplates
                  .sort((a, b) => a.name.localeCompare(b.name))
                  .map((tpl) => (
                  <button
                    key={tpl.id}
                    type="button"
                    onClick={() => handleAddTemplate(tpl.id)}
                    className="flex w-full items-center gap-2 rounded px-2 py-1.5 text-left text-sm hover:bg-muted"
                  >
                    <span className="flex-1">{tpl.name}</span>
                    <span className="rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-600">
                      {ACTION_LABELS[tpl.action_type] || tpl.action_type}
                    </span>
                    {tpl.is_system && (
                      <span className="rounded bg-purple-100 px-1.5 py-0.5 text-xs text-purple-800">System</span>
                    )}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Datalist für Gruppen-Suggestions */}
          <datalist id="group-suggestions">
            {existingGroups.map((g) => (
              <option key={g} value={g} />
            ))}
          </datalist>

          {list.items.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              Keine Vorlagen in dieser Liste.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="pb-2 pr-2">#</th>
                    <th className="pb-2 pr-2">Name</th>
                    <th className="pb-2 pr-2">Gruppe</th>
                    <th className="pb-2 pr-2">Tag-Offset</th>
                    <th className="pb-2 pr-2">Typ</th>
                    <th className="pb-2 pr-2">Priorität</th>
                    {!list.is_system && <th className="pb-2" />}
                  </tr>
                </thead>
                <tbody>
                  {list.items.map((item, index) => (
                    <tr key={item.id} className="border-b last:border-0">
                      <td className="py-2 pr-2 text-muted-foreground">{index + 1}</td>
                      <td className="py-2 pr-2 font-medium">
                        <Link
                          href={`/aufgaben/vorlagen/${item.task_template}`}
                          className="text-blue-600 underline-offset-2 hover:underline"
                        >
                          {item.template_name}
                        </Link>
                      </td>
                      <td className="py-2 pr-2">
                        {!list.is_system ? (
                          <input
                            type="text"
                            list="group-suggestions"
                            defaultValue={item.group_label}
                            onBlur={(e) => {
                              if (e.target.value !== item.group_label) {
                                handleItemUpdate(item, "group_label", e.target.value);
                              }
                            }}
                            className="w-28 rounded border border-input bg-background px-2 py-1 text-xs"
                            placeholder="Gruppe..."
                          />
                        ) : (
                          <span className="text-xs text-muted-foreground">{item.group_label || "–"}</span>
                        )}
                      </td>
                      <td className="py-2 pr-2">
                        {!list.is_system ? (
                          <input
                            type="number"
                            defaultValue={item.day_offset ?? ""}
                            onBlur={(e) => {
                              const newVal = e.target.value;
                              const oldVal = item.day_offset !== null ? String(item.day_offset) : "";
                              if (newVal !== oldVal) {
                                handleItemUpdate(item, "day_offset", newVal);
                              }
                            }}
                            className="w-16 rounded border border-input bg-background px-2 py-1 text-xs"
                            placeholder={String(item.template_day_offset)}
                          />
                        ) : (
                          <span className="text-xs text-muted-foreground">
                            {item.day_offset !== null ? item.day_offset : item.template_day_offset}
                          </span>
                        )}
                      </td>
                      <td className="py-2 pr-2">
                        <span className="rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-600">
                          {ACTION_LABELS[item.action_type] || item.action_type}
                        </span>
                      </td>
                      <td className="py-2 pr-2">
                        <span className={`rounded px-1.5 py-0.5 text-xs font-medium ${PRIORITY_COLORS[item.priority]}`}>
                          {PRIORITY_LABELS[item.priority]}
                        </span>
                      </td>
                      {!list.is_system && (
                        <td className="py-2">
                          <div className="flex items-center gap-1">
                            <button
                              type="button"
                              onClick={() => handleMoveItem(index, "up")}
                              disabled={index === 0}
                              className="rounded px-1 text-xs text-muted-foreground hover:text-foreground disabled:opacity-30"
                              title="Nach oben"
                            >
                              &#9650;
                            </button>
                            <button
                              type="button"
                              onClick={() => handleMoveItem(index, "down")}
                              disabled={index === list.items.length - 1}
                              className="rounded px-1 text-xs text-muted-foreground hover:text-foreground disabled:opacity-30"
                              title="Nach unten"
                            >
                              &#9660;
                            </button>
                            <button
                              type="button"
                              onClick={() => handleRemoveTemplate(item.task_template)}
                              className="ml-1 text-xs text-red-500 hover:text-red-700"
                            >
                              Entfernen
                            </button>
                          </div>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Verwendet bei */}
      {usageClients.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Verwendet bei ({usageClients.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {usageClients.map((client) => (
                <Link
                  key={client.slug}
                  href={`/mandanten/${client.slug}`}
                  className="rounded bg-muted px-2 py-1 text-sm hover:bg-muted/80"
                >
                  {client.name}
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
