"use client";

import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";
import type { Task, Subtask, TaskStatus, TaskTemplate, TaskList, EmailTemplateSummary, EmailPreview, TriggerMode } from "@/types/task";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------
const STATUS_LABELS: Record<TaskStatus, string> = {
  planned: "Geplant",
  open: "Offen",
  in_progress: "In Bearbeitung",
  completed: "Erledigt",
  skipped: "Übersprungen",
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

const ACTION_LABELS: Record<string, string> = {
  email: "E-Mail",
  email_sequence: "E-Mail-Sequenz",
  package: "Paket",
  phone: "Telefonat",
  meeting: "Meeting",
  document: "Dokument",
  jira_project: "Jira-Projekt",
  jira_ticket: "Jira-Ticket",
  webhook: "Webhook",
  health_check: "Health-Check",
  churn_check: "Churn-Check",
  whatsapp: "WhatsApp",
  manual: "Manuell",
};

const PHASE_LABELS: Record<number, string> = {
  0: "Phase 0: Setup",
  1: "Phase 1: Willkommen",
  2: "Phase 2: Onboarding",
  3: "Phase 3: Erste Woche",
  4: "Phase 4: Quick Wins",
  5: "Phase 5: Erster Monat",
  6: "Phase 6: Laufende Betreuung",
  7: "Phase 7: NPS & Feedback",
  8: "Phase 8: Quartal-Review",
  9: "Phase 9: Upselling",
  10: "Phase 10: Anti-Churn",
};

const ONBOARDING_PHASES = [0, 1, 2, 3, 4];
const ONBOARDING_GROUP_LABELS = ["Setup & Vorbereitung", "Willkommen", "Onboarding", "Erste Woche", "Quick Wins"];

type TabKey = "due" | "backlog" | "recurring" | "onboarding" | "done";

interface TaskSectionProps {
  slug: string;
  tenantId: string;
}

function isDoneTask(t: Task): boolean {
  return t.status === "completed" || t.status === "skipped";
}

// ---------------------------------------------------------------------------
// Progress Bar
// ---------------------------------------------------------------------------
function ProgressBar({ done, total }: { done: number; total: number }) {
  const pct = total === 0 ? 0 : Math.round((done / total) * 100);
  return (
    <div className="flex items-center gap-3">
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
        <div
          className={`h-full rounded-full transition-all ${pct === 100 ? "bg-emerald-500" : "bg-primary"}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="shrink-0 text-xs text-muted-foreground">
        {done}/{total} ({pct}%)
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Template-Auswahl Modal (Multi-Step: Listen → Vorschau → Laden)
// ---------------------------------------------------------------------------
type ModalView = "lists" | "preview" | "templates";

function TemplatePickerModal({
  tenantId,
  clientServiceTypeIds,
  onGenerate,
  onGenerateFromList,
  onClose,
}: {
  tenantId: string;
  clientServiceTypeIds?: string[];
  onGenerate: (templateIds: string[]) => void;
  onGenerateFromList: (listId: string, templateIds: string[]) => void;
  onClose: () => void;
}) {
  const [view, setView] = useState<ModalView>("lists");

  // Listen-Ansicht
  const [lists, setLists] = useState<TaskList[]>([]);
  const [loadingLists, setLoadingLists] = useState(true);

  // Vorschau-Ansicht (nach Listen-Auswahl)
  const [selectedList, setSelectedList] = useState<TaskList | null>(null);
  const [previewSelected, setPreviewSelected] = useState<Set<string>>(new Set());

  // Einzelne Vorlagen-Ansicht (Fallback)
  const [templates, setTemplates] = useState<TaskTemplate[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [search, setSearch] = useState("");
  const [loadingTemplates, setLoadingTemplates] = useState(false);

  useEffect(() => {
    apiFetch<TaskList[]>("/api/v1/tasks/lists/", { tenantId })
      .then(setLists)
      .catch(() => {})
      .finally(() => setLoadingLists(false));
  }, [tenantId]);

  function handleSelectList(list: TaskList) {
    setSelectedList(list);
    setPreviewSelected(new Set(list.items.map((i) => i.task_template)));
    setView("preview");
  }

  function handleLoadFromList() {
    if (!selectedList) return;
    const templateIds = selectedList.items
      .filter((i) => previewSelected.has(i.task_template))
      .map((i) => i.task_template);
    onGenerateFromList(selectedList.id, templateIds);
  }

  function togglePreviewTemplate(templateId: string) {
    setPreviewSelected((prev) => {
      const next = new Set(prev);
      if (next.has(templateId)) next.delete(templateId);
      else next.add(templateId);
      return next;
    });
  }

  function showTemplatesFallback() {
    setView("templates");
    if (templates.length === 0) {
      setLoadingTemplates(true);
      apiFetch<TaskTemplate[]>("/api/v1/tasks/templates/", { tenantId })
        .then((data) => {
          setTemplates(data);
          setSelected(new Set(data.map((t) => t.id)));
        })
        .catch(() => {})
        .finally(() => setLoadingTemplates(false));
    }
  }

  // Einzelne-Vorlagen: Gruppierung
  const filtered = templates.filter((t) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      t.name.toLowerCase().includes(q) ||
      t.description.toLowerCase().includes(q) ||
      (PHASE_LABELS[t.phase] || "").toLowerCase().includes(q) ||
      (ACTION_LABELS[t.action_type] || "").toLowerCase().includes(q)
    );
  });
  const grouped = filtered.reduce<Record<number, TaskTemplate[]>>((acc, t) => {
    if (!acc[t.phase]) acc[t.phase] = [];
    acc[t.phase].push(t);
    return acc;
  }, {});
  const phases = Object.keys(grouped).map(Number).sort((a, b) => a - b);

  function toggleTemplate(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function togglePhase(phase: number) {
    const phaseIds = grouped[phase].map((t) => t.id);
    const allSelected = phaseIds.every((id) => selected.has(id));
    setSelected((prev) => {
      const next = new Set(prev);
      phaseIds.forEach((id) => {
        if (allSelected) next.delete(id);
        else next.add(id);
      });
      return next;
    });
  }

  // Vorschau: Gruppierung nach group_label (Fallback phase)
  const previewGrouped = selectedList
    ? selectedList.items.reduce<Record<string, typeof selectedList.items>>((acc, item) => {
        const key = item.group_label || `Phase ${item.phase}`;
        if (!acc[key]) acc[key] = [];
        acc[key].push(item);
        return acc;
      }, {})
    : {};
  const previewGroupKeys = Object.keys(previewGrouped);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="mx-4 flex max-h-[80vh] w-full max-w-2xl flex-col rounded-lg border bg-background shadow-lg">
        {/* Header */}
        <div className="flex items-center justify-between border-b p-4">
          <h2 className="text-lg font-semibold">
            {view === "lists" && "Aufgabenliste laden"}
            {view === "preview" && selectedList?.name}
            {view === "templates" && "Einzelne Vorlagen auswählen"}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            &#10005;
          </button>
        </div>

        {/* ============ Listen-Ansicht ============ */}
        {view === "lists" && (
          <>
            <div className="flex-1 overflow-y-auto p-4">
              {loadingLists ? (
                <p className="text-sm text-muted-foreground">Laden...</p>
              ) : lists.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  Keine Aufgabenlisten vorhanden.
                </p>
              ) : (
                <div className="space-y-3">
                  {[...lists]
                    .sort((a, b) => {
                      // Empfohlene Listen zuerst
                      const aRec = clientServiceTypeIds?.includes(a.default_for_service_type || "") ? 1 : 0;
                      const bRec = clientServiceTypeIds?.includes(b.default_for_service_type || "") ? 1 : 0;
                      return bRec - aRec;
                    })
                    .map((list) => {
                    const isRecommended = clientServiceTypeIds?.includes(list.default_for_service_type || "");
                    const listGroups = [...new Set(list.items.map((i) => i.group_label).filter(Boolean))];
                    return (
                      <button
                        key={list.id}
                        type="button"
                        onClick={() => handleSelectList(list)}
                        className="w-full rounded-lg border p-4 text-left transition-shadow hover:shadow-md"
                      >
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-semibold">{list.name}</span>
                          {isRecommended && (
                            <span className="rounded bg-teal-100 px-2 py-0.5 text-xs font-medium text-teal-800">
                              Empfohlen: {list.default_for_service_type_name}
                            </span>
                          )}
                          {list.is_system && (
                            <span className="rounded bg-purple-100 px-2 py-0.5 text-xs text-purple-800">System</span>
                          )}
                          <span className="rounded bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                            {list.item_count} Vorlagen
                          </span>
                        </div>
                        {list.description && (
                          <p className="mt-1 text-sm text-muted-foreground">{list.description}</p>
                        )}
                        {listGroups.length > 0 && (
                          <p className="mt-1 text-xs text-muted-foreground">
                            {listGroups.join(", ")}
                          </p>
                        )}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
            <div className="border-t p-4">
              <button
                type="button"
                onClick={showTemplatesFallback}
                className="text-sm text-muted-foreground underline hover:text-foreground"
              >
                Oder einzelne Vorlagen auswählen →
              </button>
            </div>
          </>
        )}

        {/* ============ Vorschau-Ansicht (nach Listenauswahl) ============ */}
        {view === "preview" && selectedList && (
          <>
            <div className="flex-1 overflow-y-auto p-4">
              <div className="space-y-4">
                {previewGroupKeys.map((groupKey) => {
                  const items = previewGrouped[groupKey];
                  return (
                    <div key={groupKey}>
                      <p className="mb-1 text-sm font-semibold">
                        {groupKey}
                      </p>
                      <div className="ml-2 space-y-1">
                        {items.map((item) => (
                          <label
                            key={item.id}
                            className="flex cursor-pointer items-start gap-2 rounded px-2 py-1 hover:bg-muted/50"
                          >
                            <input
                              type="checkbox"
                              checked={previewSelected.has(item.task_template)}
                              onChange={() => togglePreviewTemplate(item.task_template)}
                              className="mt-0.5 h-4 w-4 rounded border-gray-300"
                            />
                            <div className="flex-1">
                              <span className="text-sm">{item.template_name}</span>
                              <div className="flex gap-2">
                                <span className="rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-600">
                                  {ACTION_LABELS[item.action_type] || item.action_type}
                                </span>
                                <span className={`rounded px-1.5 py-0.5 text-xs font-medium ${PRIORITY_COLORS[item.priority]}`}>
                                  {PRIORITY_LABELS[item.priority]}
                                </span>
                                {(() => {
                                  const offset = item.day_offset ?? item.template_day_offset;
                                  return offset !== 0 ? (
                                    <span className="text-xs text-muted-foreground">
                                      Tag {offset > 0 ? "+" : ""}{offset}
                                    </span>
                                  ) : null;
                                })()}
                              </div>
                            </div>
                          </label>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
            <div className="flex items-center justify-between border-t p-4">
              <button
                type="button"
                onClick={() => setView("lists")}
                className="text-sm text-muted-foreground underline hover:text-foreground"
              >
                ← Zurück zu Listen
              </button>
              <div className="flex gap-2">
                <Button variant="outline" onClick={onClose}>
                  Abbrechen
                </Button>
                <Button
                  onClick={handleLoadFromList}
                  disabled={previewSelected.size === 0}
                >
                  {previewSelected.size} Aufgaben laden
                </Button>
              </div>
            </div>
          </>
        )}

        {/* ============ Einzelne-Vorlagen-Ansicht (Fallback) ============ */}
        {view === "templates" && (
          <>
            <div className="flex items-center gap-2 border-b px-4 py-3">
              <Input
                placeholder="Vorlage suchen..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="flex-1"
              />
              <Button variant="ghost" size="sm" onClick={() => setSelected(new Set(filtered.map((t) => t.id)))}>
                Alle
              </Button>
              <Button variant="ghost" size="sm" onClick={() => setSelected(new Set())}>
                Keine
              </Button>
            </div>
            <div className="flex-1 overflow-y-auto p-4">
              {loadingTemplates ? (
                <p className="text-sm text-muted-foreground">Laden...</p>
              ) : filtered.length === 0 ? (
                <p className="text-sm text-muted-foreground">Keine Vorlagen gefunden.</p>
              ) : (
                <div className="space-y-4">
                  {phases.map((phase) => {
                    const phaseTemplates = grouped[phase];
                    const phaseIds = phaseTemplates.map((t) => t.id);
                    const allChecked = phaseIds.every((id) => selected.has(id));
                    const someChecked = !allChecked && phaseIds.some((id) => selected.has(id));
                    return (
                      <div key={phase}>
                        <label className="mb-1 flex cursor-pointer items-center gap-2">
                          <input
                            type="checkbox"
                            checked={allChecked}
                            ref={(el) => { if (el) el.indeterminate = someChecked; }}
                            onChange={() => togglePhase(phase)}
                            className="h-4 w-4 rounded border-gray-300"
                          />
                          <span className="text-sm font-semibold">{PHASE_LABELS[phase] || `Phase ${phase}`}</span>
                          <span className="text-xs text-muted-foreground">({phaseTemplates.length})</span>
                        </label>
                        <div className="ml-6 space-y-1">
                          {phaseTemplates.map((tpl) => (
                            <label key={tpl.id} className="flex cursor-pointer items-start gap-2 rounded px-2 py-1 hover:bg-muted/50">
                              <input
                                type="checkbox"
                                checked={selected.has(tpl.id)}
                                onChange={() => toggleTemplate(tpl.id)}
                                className="mt-0.5 h-4 w-4 rounded border-gray-300"
                              />
                              <div className="flex-1">
                                <span className="text-sm">{tpl.name}</span>
                                <div className="flex gap-2">
                                  <span className="rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-600">
                                    {ACTION_LABELS[tpl.action_type] || tpl.action_type}
                                  </span>
                                  <span className={`rounded px-1.5 py-0.5 text-xs font-medium ${PRIORITY_COLORS[tpl.priority]}`}>
                                    {PRIORITY_LABELS[tpl.priority]}
                                  </span>
                                  {tpl.day_offset !== 0 && (
                                    <span className="text-xs text-muted-foreground">
                                      Tag {tpl.day_offset > 0 ? "+" : ""}{tpl.day_offset}
                                    </span>
                                  )}
                                </div>
                                {tpl.description && (
                                  <p className="mt-0.5 text-xs text-muted-foreground">{tpl.description}</p>
                                )}
                              </div>
                            </label>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
            <div className="flex items-center justify-between border-t p-4">
              <button
                type="button"
                onClick={() => setView("lists")}
                className="text-sm text-muted-foreground underline hover:text-foreground"
              >
                ← Zurück zu Listen
              </button>
              <div className="flex gap-2">
                <Button variant="outline" onClick={onClose}>Abbrechen</Button>
                <Button onClick={() => onGenerate(Array.from(selected))} disabled={selected.size === 0}>
                  {selected.size} Aufgaben laden
                </Button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// EmailSendModal — Email-Preview + Senden aus Task heraus
// ---------------------------------------------------------------------------
function EmailSendModal({
  slug,
  taskId,
  templates,
  tenantId,
  onClose,
  onSent,
}: {
  slug: string;
  taskId: string;
  templates: EmailTemplateSummary[];
  tenantId: string;
  onClose: () => void;
  onSent: () => void;
}) {
  const [selectedSlug, setSelectedSlug] = useState(templates[0]?.slug || "");
  const [preview, setPreview] = useState<EmailPreview | null>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [sending, setSending] = useState(false);
  const [feedback, setFeedback] = useState("");

  // Preview laden wenn Template wechselt
  useEffect(() => {
    if (!selectedSlug) return;
    setLoadingPreview(true);
    setFeedback("");
    apiFetch<EmailPreview>(
      `/api/v1/clients/${slug}/tasks/${taskId}/email-preview/`,
      {
        method: "POST",
        body: JSON.stringify({ template_slug: selectedSlug }),
        tenantId,
      }
    )
      .then(setPreview)
      .catch(() => setFeedback("Vorschau konnte nicht geladen werden."))
      .finally(() => setLoadingPreview(false));
  }, [selectedSlug, slug, taskId, tenantId]);

  async function handleSend() {
    setSending(true);
    setFeedback("");
    try {
      await apiFetch(`/api/v1/clients/${slug}/tasks/${taskId}/send-email/`, {
        method: "POST",
        body: JSON.stringify({ template_slug: selectedSlug }),
        tenantId,
      });
      setFeedback("E-Mail wurde gesendet!");
      setTimeout(() => {
        onSent();
        onClose();
      }, 1200);
    } catch (err) {
      setFeedback(
        err instanceof Error ? err.message : "Fehler beim Senden."
      );
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="mx-4 flex max-h-[85vh] w-full max-w-2xl flex-col rounded-lg border bg-background shadow-lg">
        {/* Header */}
        <div className="flex items-center justify-between border-b p-4">
          <h2 className="text-lg font-semibold">E-Mail senden</h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            &#10005;
          </button>
        </div>

        {/* Template-Dropdown */}
        <div className="border-b px-4 py-3">
          <label className="mb-1 block text-xs font-medium text-muted-foreground">
            Vorlage
          </label>
          <select
            value={selectedSlug}
            onChange={(e) => setSelectedSlug(e.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            {templates.map((tpl) => (
              <option key={tpl.slug} value={tpl.slug}>
                {tpl.name}
              </option>
            ))}
          </select>
        </div>

        {/* Preview */}
        <div className="flex-1 overflow-y-auto p-4">
          {loadingPreview ? (
            <p className="text-sm text-muted-foreground">Vorschau wird geladen...</p>
          ) : preview ? (
            <div className="space-y-3">
              <div>
                <p className="text-xs font-medium text-muted-foreground">Empfänger</p>
                <p className="text-sm">{preview.recipient_email || "Keine E-Mail-Adresse"}</p>
              </div>
              <div>
                <p className="text-xs font-medium text-muted-foreground">Betreff</p>
                <p className="text-sm font-medium">{preview.subject}</p>
              </div>
              <div>
                <p className="mb-1 text-xs font-medium text-muted-foreground">Vorschau</p>
                <iframe
                  srcDoc={preview.body_html}
                  title="E-Mail-Vorschau"
                  className="h-64 w-full rounded border bg-white"
                  sandbox=""
                />
              </div>
            </div>
          ) : null}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t p-4">
          <span className="text-sm">
            {feedback && (
              <span className={feedback.includes("gesendet") ? "text-green-600" : "text-red-600"}>
                {feedback}
              </span>
            )}
          </span>
          <div className="flex gap-2">
            <Button variant="outline" onClick={onClose}>
              Abbrechen
            </Button>
            <Button
              onClick={handleSend}
              disabled={sending || !preview?.recipient_email}
            >
              {sending ? "Sende..." : "E-Mail senden"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// SequenceStartModal — E-Mail-Sequenz aus Task starten
// ---------------------------------------------------------------------------
function SequenceStartModal({
  slug,
  taskId,
  taskTitle,
  sequenceName,
  tenantId,
  onClose,
  onStarted,
}: {
  slug: string;
  taskId: string;
  taskTitle: string;
  sequenceName: string;
  tenantId: string;
  onClose: () => void;
  onStarted: () => void;
}) {
  const [starting, setStarting] = useState(false);
  const [feedback, setFeedback] = useState("");

  async function handleStart() {
    setStarting(true);
    setFeedback("");
    try {
      await apiFetch(`/api/v1/clients/${slug}/tasks/${taskId}/start-sequence/`, {
        method: "POST",
        body: JSON.stringify({}),
        tenantId,
      });
      setFeedback("E-Mail-Sequenz wurde gestartet!");
      setTimeout(() => {
        onStarted();
        onClose();
      }, 1500);
    } catch (err) {
      setFeedback(
        err instanceof Error ? err.message : "Fehler beim Starten der Sequenz."
      );
    } finally {
      setStarting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="mx-4 w-full max-w-md rounded-lg border bg-background p-6 shadow-lg">
        <h2 className="mb-2 text-lg font-semibold">E-Mail-Sequenz starten</h2>
        <p className="mb-1 text-sm text-muted-foreground">
          Aufgabe: <strong>{taskTitle}</strong>
        </p>
        <p className="mb-4 text-sm text-muted-foreground">
          Sequenz: <strong>{sequenceName}</strong>
        </p>
        <p className="mb-4 text-sm">
          Soll die E-Mail-Sequenz jetzt gestartet werden? Alle E-Mails der Sequenz
          werden automatisch zum geplanten Zeitpunkt versendet.
        </p>

        {feedback && (
          <p className={`mb-4 text-sm ${feedback.includes("gestartet") ? "text-green-600" : "text-red-600"}`}>
            {feedback}
          </p>
        )}

        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={onClose}>
            Abbrechen
          </Button>
          <Button onClick={handleStart} disabled={starting}>
            {starting ? "Starte..." : "Sequenz starten"}
          </Button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// JiraExecuteModal — Bestätigung + Ausführung einer Jira-Aktion aus Task
// ---------------------------------------------------------------------------
function JiraExecuteModal({
  slug,
  taskId,
  taskTitle,
  actionLabel,
  tenantId,
  onClose,
  onExecuted,
}: {
  slug: string;
  taskId: string;
  taskTitle: string;
  actionLabel: string;
  tenantId: string;
  onClose: () => void;
  onExecuted: () => void;
}) {
  const [executing, setExecuting] = useState(false);
  const [polling, setPolling] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [feedbackType, setFeedbackType] = useState<"success" | "error" | "info">("info");

  async function pollExecution(executionId: string) {
    setPolling(true);
    setFeedback("Warte auf Jira-Ergebnis...");
    setFeedbackType("info");

    const maxAttempts = 30; // 30 × 2s = 60s max
    for (let i = 0; i < maxAttempts; i++) {
      await new Promise((r) => setTimeout(r, 2000));
      try {
        const exec = await apiFetch<{ status: string; error_message: string }>(
          `/api/v1/integrations/executions/${executionId}/`,
          { tenantId }
        );

        if (exec.status === "completed") {
          setFeedback("Jira-Aktion erfolgreich ausgeführt!");
          setFeedbackType("success");
          // Auto-Complete: Task als erledigt markieren
          try {
            await apiFetch(`/api/v1/clients/${slug}/tasks/${taskId}/complete/`, {
              method: "POST",
              body: JSON.stringify({}),
              tenantId,
            });
          } catch {
            // Complete-Fehler ignorieren
          }
          setPolling(false);
          setTimeout(() => {
            onExecuted();
            onClose();
          }, 1500);
          return;
        }

        if (exec.status === "failed") {
          setFeedback(exec.error_message || "Jira-Aktion fehlgeschlagen.");
          setFeedbackType("error");
          setPolling(false);
          return;
        }
        // pending / running → weiter pollen
      } catch {
        // Netzwerkfehler beim Polling → weiter versuchen
      }
    }
    // Timeout nach 60s
    setFeedback("Zeitüberschreitung — prüfe den Status in Jira.");
    setFeedbackType("error");
    setPolling(false);
  }

  async function handleExecute() {
    setExecuting(true);
    setFeedback("");
    try {
      const result = await apiFetch<{ execution_id: string }>(
        `/api/v1/clients/${slug}/tasks/${taskId}/execute-jira/`,
        {
          method: "POST",
          body: JSON.stringify({}),
          tenantId,
        }
      );
      setExecuting(false);
      // Jetzt auf das tatsächliche Ergebnis warten
      pollExecution(result.execution_id);
    } catch (err) {
      setFeedback(
        err instanceof Error ? err.message : "Jira-Aktion konnte nicht gestartet werden."
      );
      setFeedbackType("error");
      setExecuting(false);
    }
  }

  const feedbackColor = {
    success: "text-green-600",
    error: "text-red-600",
    info: "text-muted-foreground",
  }[feedbackType];

  const busy = executing || polling;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="mx-4 w-full max-w-md rounded-lg border bg-background shadow-lg">
        {/* Header */}
        <div className="flex items-center justify-between border-b p-4">
          <h2 className="text-lg font-semibold">Jira-Aktion ausführen</h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            &#10005;
          </button>
        </div>

        {/* Body */}
        <div className="space-y-3 p-4">
          <div>
            <p className="text-xs font-medium text-muted-foreground">Aufgabe</p>
            <p className="text-sm font-medium">{taskTitle}</p>
          </div>
          <div>
            <p className="text-xs font-medium text-muted-foreground">Aktion</p>
            <p className="text-sm">{actionLabel}</p>
          </div>
          {feedback && (
            <p className={`text-sm ${feedbackColor}`}>
              {polling && <span className="mr-1 inline-block animate-spin">&#8635;</span>}
              {feedback}
            </p>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-2 border-t p-4">
          <Button variant="outline" onClick={onClose}>
            {feedbackType === "error" ? "Schließen" : "Abbrechen"}
          </Button>
          {feedbackType !== "success" && (
            <Button onClick={handleExecute} disabled={busy}>
              {executing ? "Wird gestartet..." : polling ? "Läuft..." : "Ausführen"}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// WebhookExecuteModal — Bestätigung + Ausführung einer Webhook-Aktion
// ---------------------------------------------------------------------------
function WebhookExecuteModal({
  slug,
  taskId,
  taskTitle,
  actionLabel,
  tenantId,
  onClose,
  onExecuted,
}: {
  slug: string;
  taskId: string;
  taskTitle: string;
  actionLabel: string;
  tenantId: string;
  onClose: () => void;
  onExecuted: () => void;
}) {
  const [executing, setExecuting] = useState(false);
  const [polling, setPolling] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [feedbackType, setFeedbackType] = useState<"success" | "error" | "info">("info");

  async function pollExecution(executionId: string) {
    setPolling(true);
    setFeedback("Warte auf Webhook-Ergebnis...");
    setFeedbackType("info");

    const maxAttempts = 30;
    for (let i = 0; i < maxAttempts; i++) {
      await new Promise((r) => setTimeout(r, 2000));
      try {
        const exec = await apiFetch<{ status: string; error_message: string }>(
          `/api/v1/integrations/executions/${executionId}/`,
          { tenantId }
        );

        if (exec.status === "completed") {
          setFeedback("Webhook erfolgreich ausgeführt!");
          setFeedbackType("success");
          try {
            await apiFetch(`/api/v1/clients/${slug}/tasks/${taskId}/complete/`, {
              method: "POST",
              body: JSON.stringify({}),
              tenantId,
            });
          } catch {
            // Complete-Fehler ignorieren
          }
          setPolling(false);
          setTimeout(() => {
            onExecuted();
            onClose();
          }, 1500);
          return;
        }

        if (exec.status === "failed") {
          setFeedback(exec.error_message || "Webhook-Aktion fehlgeschlagen.");
          setFeedbackType("error");
          setPolling(false);
          return;
        }
      } catch {
        // Netzwerkfehler beim Polling → weiter versuchen
      }
    }
    setFeedback("Zeitüberschreitung — prüfe den Webhook-Verlauf.");
    setFeedbackType("error");
    setPolling(false);
  }

  async function handleExecute() {
    setExecuting(true);
    setFeedback("");
    try {
      const result = await apiFetch<{ execution_id: string }>(
        `/api/v1/clients/${slug}/tasks/${taskId}/execute-webhook/`,
        {
          method: "POST",
          body: JSON.stringify({}),
          tenantId,
        }
      );
      setExecuting(false);
      pollExecution(result.execution_id);
    } catch (err) {
      setFeedback(
        err instanceof Error ? err.message : "Webhook konnte nicht gestartet werden."
      );
      setFeedbackType("error");
      setExecuting(false);
    }
  }

  const feedbackColor = {
    success: "text-green-600",
    error: "text-red-600",
    info: "text-muted-foreground",
  }[feedbackType];

  const busy = executing || polling;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="mx-4 w-full max-w-md rounded-lg border bg-background shadow-lg">
        <div className="flex items-center justify-between border-b p-4">
          <h2 className="text-lg font-semibold">Webhook ausführen</h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            &#10005;
          </button>
        </div>
        <div className="space-y-3 p-4">
          <div>
            <p className="text-xs font-medium text-muted-foreground">Aufgabe</p>
            <p className="text-sm font-medium">{taskTitle}</p>
          </div>
          <div>
            <p className="text-xs font-medium text-muted-foreground">Aktion</p>
            <p className="text-sm">{actionLabel}</p>
          </div>
          {feedback && (
            <p className={`text-sm ${feedbackColor}`}>
              {polling && <span className="mr-1 inline-block animate-spin">&#8635;</span>}
              {feedback}
            </p>
          )}
        </div>
        <div className="flex justify-end gap-2 border-t p-4">
          <Button variant="outline" onClick={onClose}>
            {feedbackType === "error" ? "Schließen" : "Abbrechen"}
          </Button>
          {feedbackType !== "success" && (
            <Button onClick={handleExecute} disabled={busy}>
              {executing ? "Wird gestartet..." : polling ? "Läuft..." : "Ausführen"}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// HealthCheckModal — 7 Kategorien (1-5) bewerten
// ---------------------------------------------------------------------------
const HEALTH_CATEGORIES: { field: string; label: string; description: string }[] = [
  { field: "result_satisfaction", label: "Ergebnis-Zufriedenheit", description: "Erreichen wir die vereinbarten KPIs?" },
  { field: "communication", label: "Kommunikation", description: "Wie gut funktioniert die Zusammenarbeit?" },
  { field: "engagement", label: "Engagement", description: "Wie aktiv ist der Mandant eingebunden?" },
  { field: "relationship", label: "Beziehungsqualität", description: "Wie ist die persönliche Beziehung?" },
  { field: "payment_behavior", label: "Zahlungsverhalten", description: "Werden Rechnungen pünktlich bezahlt?" },
  { field: "growth_potential", label: "Wachstumspotenzial", description: "Gibt es Upselling-Möglichkeiten?" },
  { field: "referral_readiness", label: "Empfehlungsbereitschaft", description: "Würde der Mandant uns weiterempfehlen?" },
];

function HealthCheckModal({
  slug,
  taskId,
  tenantId,
  onClose,
  onSubmitted,
}: {
  slug: string;
  taskId: string;
  tenantId: string;
  onClose: () => void;
  onSubmitted: () => void;
}) {
  const [scores, setScores] = useState<Record<string, number>>(() => {
    const init: Record<string, number> = {};
    for (const cat of HEALTH_CATEGORIES) init[cat.field] = 3;
    return init;
  });
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [feedbackType, setFeedbackType] = useState<"success" | "error">("error");

  const totalScore = Object.values(scores).reduce((a, b) => a + b, 0);

  function statusLabel(score: number): string {
    if (score >= 30) return "Exzellent";
    if (score >= 24) return "Gut";
    if (score >= 18) return "Neutral";
    if (score >= 12) return "Risiko";
    return "Kritisch";
  }

  function statusColor(score: number): string {
    if (score >= 24) return "text-green-600";
    if (score >= 18) return "text-yellow-600";
    return "text-red-600";
  }

  async function handleSubmit() {
    setSubmitting(true);
    setFeedback("");
    try {
      const result = await apiFetch<{ detail: string }>(
        `/api/v1/clients/${slug}/tasks/${taskId}/submit-health-check/`,
        {
          method: "POST",
          body: JSON.stringify({ ...scores, notes }),
          tenantId,
        }
      );
      setFeedback(result.detail);
      setFeedbackType("success");
      setTimeout(() => {
        onSubmitted();
        onClose();
      }, 1500);
    } catch (err) {
      setFeedback(err instanceof Error ? err.message : "Fehler beim Speichern.");
      setFeedbackType("error");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="mx-4 w-full max-w-lg rounded-lg border bg-background shadow-lg">
        <div className="flex items-center justify-between border-b p-4">
          <h2 className="text-lg font-semibold">Health-Score Fragebogen</h2>
          <button type="button" onClick={onClose} className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground">&#10005;</button>
        </div>

        <div className="max-h-[60vh] space-y-3 overflow-y-auto p-4">
          {HEALTH_CATEGORIES.map((cat) => (
            <div key={cat.field} className="flex items-center gap-3">
              <div className="flex-1">
                <p className="text-sm font-medium">{cat.label}</p>
                <p className="text-xs text-muted-foreground">{cat.description}</p>
              </div>
              <select
                className="h-8 w-16 rounded-md border border-input bg-background px-2 text-sm"
                value={scores[cat.field]}
                onChange={(e) => setScores({ ...scores, [cat.field]: Number(e.target.value) })}
              >
                {[1, 2, 3, 4, 5].map((v) => (
                  <option key={v} value={v}>{v}</option>
                ))}
              </select>
            </div>
          ))}

          <div className="space-y-1 pt-2">
            <label className="text-xs font-medium text-muted-foreground">Notizen (optional)</label>
            <textarea
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </div>

          <div className="flex items-center justify-between rounded-md bg-muted p-3">
            <span className="text-sm font-medium">Gesamt-Score</span>
            <span className={`text-lg font-bold ${statusColor(totalScore)}`}>
              {totalScore}/35 — {statusLabel(totalScore)}
            </span>
          </div>

          {feedback && (
            <p className={`text-sm ${feedbackType === "success" ? "text-green-600" : "text-red-600"}`}>
              {feedback}
            </p>
          )}
        </div>

        <div className="flex justify-end gap-2 border-t p-4">
          <Button variant="outline" onClick={onClose}>Abbrechen</Button>
          {feedbackType !== "success" && (
            <Button onClick={handleSubmit} disabled={submitting}>
              {submitting ? "Speichern..." : "Health-Check abgeben"}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// ChurnCheckModal — 10 Warnsignale als Checkboxen
// ---------------------------------------------------------------------------
const CHURN_SIGNALS: { field: string; label: string }[] = [
  { field: "slower_responses", label: "Langsamere Antworten auf E-Mails/Anrufe" },
  { field: "missed_checkins", label: "Verpasste oder abgesagte Check-in-Termine" },
  { field: "decreased_usage", label: "Weniger Nutzung der bereitgestellten Services" },
  { field: "contract_inquiries", label: "Fragen zu Vertragslaufzeit oder Kündigungsfristen" },
  { field: "new_decision_maker", label: "Neuer Ansprechpartner / Entscheider" },
  { field: "budget_cuts_mentioned", label: "Budgetkürzungen erwähnt" },
  { field: "competitor_mentions", label: "Wettbewerber oder Alternativen erwähnt" },
  { field: "critical_feedback", label: "Kritisches Feedback oder Beschwerden" },
  { field: "delayed_payments", label: "Verspätete Zahlungen" },
  { field: "fewer_approvals", label: "Weniger Freigaben / geringere Beteiligung" },
];

function ChurnCheckModal({
  slug,
  taskId,
  tenantId,
  onClose,
  onSubmitted,
}: {
  slug: string;
  taskId: string;
  tenantId: string;
  onClose: () => void;
  onSubmitted: () => void;
}) {
  const [signals, setSignals] = useState<Record<string, boolean>>(() => {
    const init: Record<string, boolean> = {};
    for (const s of CHURN_SIGNALS) init[s.field] = false;
    return init;
  });
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [feedbackType, setFeedbackType] = useState<"success" | "error">("error");

  const activeCount = Object.values(signals).filter(Boolean).length;

  function churnColor(count: number): string {
    if (count <= 1) return "text-green-600";
    if (count <= 3) return "text-yellow-600";
    return "text-red-600";
  }

  async function handleSubmit() {
    setSubmitting(true);
    setFeedback("");
    try {
      const result = await apiFetch<{ detail: string }>(
        `/api/v1/clients/${slug}/tasks/${taskId}/submit-churn-check/`,
        {
          method: "POST",
          body: JSON.stringify({ ...signals, notes }),
          tenantId,
        }
      );
      setFeedback(result.detail);
      setFeedbackType("success");
      setTimeout(() => {
        onSubmitted();
        onClose();
      }, 1500);
    } catch (err) {
      setFeedback(err instanceof Error ? err.message : "Fehler beim Speichern.");
      setFeedbackType("error");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="mx-4 w-full max-w-lg rounded-lg border bg-background shadow-lg">
        <div className="flex items-center justify-between border-b p-4">
          <h2 className="text-lg font-semibold">Churn-Warnsignale prüfen</h2>
          <button type="button" onClick={onClose} className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground">&#10005;</button>
        </div>

        <div className="max-h-[60vh] space-y-3 overflow-y-auto p-4">
          {CHURN_SIGNALS.map((s) => (
            <label key={s.field} className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={signals[s.field]}
                onChange={() => setSignals({ ...signals, [s.field]: !signals[s.field] })}
                className="h-4 w-4 rounded border-gray-300"
              />
              <span className="text-sm">{s.label}</span>
            </label>
          ))}

          <div className="space-y-1 pt-2">
            <label className="text-xs font-medium text-muted-foreground">Notizen (optional)</label>
            <textarea
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </div>

          <div className="flex items-center justify-between rounded-md bg-muted p-3">
            <span className="text-sm font-medium">Warnsignale aktiv</span>
            <span className={`text-lg font-bold ${churnColor(activeCount)}`}>
              {activeCount}/10
            </span>
          </div>

          {feedback && (
            <p className={`text-sm ${feedbackType === "success" ? "text-green-600" : "text-red-600"}`}>
              {feedback}
            </p>
          )}
        </div>

        <div className="flex justify-end gap-2 border-t p-4">
          <Button variant="outline" onClick={onClose}>Abbrechen</Button>
          {feedbackType !== "success" && (
            <Button onClick={handleSubmit} disabled={submitting}>
              {submitting ? "Speichern..." : "Churn-Check abgeben"}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// WhatsAppSendModal — WhatsApp-Nachricht aus Task senden
// ---------------------------------------------------------------------------
function WhatsAppSendModal({
  slug,
  taskId,
  taskTitle,
  tenantId,
  onClose,
  onSent,
}: {
  slug: string;
  taskId: string;
  taskTitle: string;
  tenantId: string;
  onClose: () => void;
  onSent: () => void;
}) {
  const [phoneNumbers, setPhoneNumbers] = useState<{ label: string; number: string }[]>([]);
  const [selectedNumber, setSelectedNumber] = useState("");
  const [messageText, setMessageText] = useState("");
  const [sending, setSending] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch<{ phone_numbers: { label: string; number: string }[] }>(
      `/api/v1/clients/${slug}/`,
      { tenantId }
    )
      .then((client) => {
        const nums = client.phone_numbers || [];
        setPhoneNumbers(nums);
        if (nums.length > 0) setSelectedNumber(nums[0].number);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [slug, tenantId]);

  async function handleSend() {
    if (!selectedNumber || !messageText.trim()) return;
    setSending(true);
    setFeedback("");
    try {
      await apiFetch("/api/v1/integrations/whatsapp/send/", {
        method: "POST",
        body: JSON.stringify({
          to_number: selectedNumber,
          body_text: messageText.trim(),
          client_slug: slug,
        }),
        tenantId,
      });
      // Auto-complete the task
      try {
        await apiFetch(`/api/v1/clients/${slug}/tasks/${taskId}/complete/`, {
          method: "POST",
          body: JSON.stringify({}),
          tenantId,
        });
      } catch {
        // Complete-Fehler ignorieren
      }
      setFeedback("WhatsApp-Nachricht wurde gesendet!");
      setTimeout(() => {
        onSent();
        onClose();
      }, 1200);
    } catch (err) {
      setFeedback(err instanceof Error ? err.message : "Fehler beim Senden.");
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="mx-4 w-full max-w-md rounded-lg border bg-background shadow-lg">
        {/* Header */}
        <div className="flex items-center justify-between border-b p-4">
          <h2 className="text-lg font-semibold">WhatsApp senden</h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            &#10005;
          </button>
        </div>

        {/* Body */}
        <div className="space-y-4 p-4">
          <div>
            <p className="text-xs font-medium text-muted-foreground">Aufgabe</p>
            <p className="text-sm font-medium">{taskTitle}</p>
          </div>

          {loading ? (
            <p className="text-sm text-muted-foreground">Lade Telefonnummern...</p>
          ) : phoneNumbers.length === 0 ? (
            <div className="rounded border border-yellow-200 bg-yellow-50 p-3">
              <p className="text-sm text-yellow-800">
                Keine Telefonnummern für diesen Mandanten hinterlegt.
              </p>
            </div>
          ) : (
            <>
              <div>
                <label className="mb-1 block text-xs font-medium text-muted-foreground">
                  Empfänger
                </label>
                <select
                  value={selectedNumber}
                  onChange={(e) => setSelectedNumber(e.target.value)}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  {phoneNumbers.map((pn) => (
                    <option key={pn.number} value={pn.number}>
                      {pn.label ? `${pn.label}: ${pn.number}` : pn.number}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-muted-foreground">
                  Nachricht
                </label>
                <textarea
                  value={messageText}
                  onChange={(e) => setMessageText(e.target.value)}
                  placeholder="Nachricht eingeben..."
                  rows={4}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  autoFocus
                />
              </div>
            </>
          )}

          {feedback && (
            <p className={`text-sm ${feedback.includes("gesendet") ? "text-green-600" : "text-red-600"}`}>
              {feedback}
            </p>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-2 border-t p-4">
          <Button variant="outline" onClick={onClose}>
            Abbrechen
          </Button>
          <Button
            onClick={handleSend}
            disabled={sending || !selectedNumber || !messageText.trim()}
            className="bg-green-600 hover:bg-green-700"
          >
            {sending ? "Sende..." : "WhatsApp senden"}
          </Button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// ManualTaskCreateModal — Neue manuelle Aufgabe erstellen
// ---------------------------------------------------------------------------
function ManualTaskCreateModal({
  slug,
  tenantId,
  onClose,
  onCreated,
}: {
  slug: string;
  tenantId: string;
  onClose: () => void;
  onCreated: () => void;
}) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState("medium");
  const [dueDate, setDueDate] = useState("");
  const [notes, setNotes] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit() {
    if (!title.trim()) return;
    setCreating(true);
    setError("");
    try {
      await apiFetch(`/api/v1/clients/${slug}/tasks/`, {
        method: "POST",
        body: JSON.stringify({
          title: title.trim(),
          description: description.trim() || undefined,
          priority,
          due_date: dueDate || null,
          notes: notes.trim() || undefined,
          action_type: "manual",
        }),
        tenantId,
      });
      onCreated();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Fehler beim Erstellen.");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="mx-4 w-full max-w-md rounded-lg border bg-background shadow-lg">
        {/* Header */}
        <div className="flex items-center justify-between border-b p-4">
          <h2 className="text-lg font-semibold">Neue Aufgabe</h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            &#10005;
          </button>
        </div>

        {/* Body */}
        <div className="space-y-4 p-4">
          <div>
            <label className="mb-1 block text-xs font-medium text-muted-foreground">
              Titel *
            </label>
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="z.B. Rechnung erneut zusenden"
              autoFocus
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-muted-foreground">
              Beschreibung
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optionale Beschreibung..."
              rows={2}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            />
          </div>
          <div className="flex gap-4">
            <div className="flex-1">
              <label className="mb-1 block text-xs font-medium text-muted-foreground">
                Priorität
              </label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="low">Niedrig</option>
                <option value="medium">Mittel</option>
                <option value="high">Hoch</option>
                <option value="critical">Kritisch</option>
              </select>
            </div>
            <div className="flex-1">
              <label className="mb-1 block text-xs font-medium text-muted-foreground">
                Fälligkeitsdatum
              </label>
              <input
                type="date"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              />
            </div>
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-muted-foreground">
              Notizen
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Optionale Notizen..."
              rows={2}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            />
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-2 border-t p-4">
          <Button variant="outline" onClick={onClose}>
            Abbrechen
          </Button>
          <Button onClick={handleSubmit} disabled={creating || !title.trim()}>
            {creating ? "Erstelle..." : "Aufgabe erstellen"}
          </Button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Single Task Row (shared across tabs)
// ---------------------------------------------------------------------------
function TaskRow({
  task,
  today,
  isExpanded,
  onToggleExpand,
  onComplete,
  onSkip,
  onDelete,
  onSubtaskToggle,
  onSendEmail,
  onStartSequence,
  onExecuteJira,
  onExecuteWebhook,
  onSendWhatsApp,
  onHealthCheck,
  onChurnCheck,
}: {
  task: Task;
  today: string;
  isExpanded: boolean;
  onToggleExpand: () => void;
  onComplete: () => void;
  onSkip: () => void;
  onDelete: () => void;
  onSubtaskToggle: (subtask: Subtask) => void;
  onSendEmail?: () => void;
  onStartSequence?: () => void;
  onExecuteJira?: () => void;
  onExecuteWebhook?: () => void;
  onSendWhatsApp?: () => void;
  onHealthCheck?: () => void;
  onChurnCheck?: () => void;
}) {
  const done = isDoneTask(task);
  const overdue = !done && task.due_date !== null && task.due_date < today;

  return (
    <div
      className={`rounded-md border p-3 ${done ? "opacity-60" : ""} ${overdue ? "border-red-300 bg-red-50/50" : ""}`}
    >
      <div className="flex items-center gap-3">
        <input
          type="checkbox"
          checked={task.status === "completed"}
          disabled={done}
          onChange={onComplete}
          className="h-4 w-4 shrink-0 rounded border-gray-300"
        />
        <button
          type="button"
          className="flex-1 text-left"
          onClick={onToggleExpand}
        >
          <span
            className={`text-sm font-medium ${done ? "line-through" : ""}`}
          >
            {task.title}
          </span>
        </button>
        <span
          className={`shrink-0 rounded px-2 py-0.5 text-xs font-medium ${PRIORITY_COLORS[task.priority]}`}
        >
          {PRIORITY_LABELS[task.priority]}
        </span>
        <span className="shrink-0 rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
          {ACTION_LABELS[task.action_type] || task.action_type}
        </span>
        {task.effective_trigger_mode === "auto_on_due" && (
          <span className="shrink-0 rounded bg-emerald-100 px-1.5 py-0.5 text-[10px] font-semibold text-emerald-700">
            Auto
          </span>
        )}
        {!done && task.effective_trigger_mode === "auto_on_due" && task.due_date && (() => {
          const diffDays = Math.ceil(
            (new Date(task.due_date).getTime() - new Date(today).getTime()) / 86400000
          );
          if (diffDays < 0) return null;
          const label =
            diffDays === 0 ? "triggert heute" :
            diffDays === 1 ? "triggert morgen" :
            `triggert in ${diffDays} Tagen`;
          return (
            <span className="ml-1 shrink-0 text-[11px] italic text-emerald-600">
              {label}
            </span>
          );
        })()}
        {!done && onSendEmail && (
          <Button variant="outline" size="sm" className="h-6 shrink-0 border-blue-300 bg-blue-50 px-2 text-xs text-blue-700 hover:bg-blue-100" onClick={(e) => { e.stopPropagation(); onSendEmail(); }}>
            Senden
          </Button>
        )}
        {!done && onStartSequence && (
          <Button variant="outline" size="sm" className="h-6 shrink-0 border-blue-300 bg-blue-50 px-2 text-xs text-blue-700 hover:bg-blue-100" onClick={(e) => { e.stopPropagation(); onStartSequence(); }}>
            Sequenz
          </Button>
        )}
        {!done && onExecuteJira && (
          <Button variant="outline" size="sm" className="h-6 shrink-0 border-indigo-300 bg-indigo-50 px-2 text-xs text-indigo-700 hover:bg-indigo-100" onClick={(e) => { e.stopPropagation(); onExecuteJira(); }}>
            Ausführen
          </Button>
        )}
        {!done && onExecuteWebhook && (
          <Button variant="outline" size="sm" className="h-6 shrink-0 border-violet-300 bg-violet-50 px-2 text-xs text-violet-700 hover:bg-violet-100" onClick={(e) => { e.stopPropagation(); onExecuteWebhook(); }}>
            Webhook
          </Button>
        )}
        {!done && onSendWhatsApp && (
          <Button variant="outline" size="sm" className="h-6 shrink-0 border-green-300 bg-green-50 px-2 text-xs text-green-700 hover:bg-green-100" onClick={(e) => { e.stopPropagation(); onSendWhatsApp(); }}>
            WhatsApp
          </Button>
        )}
        {!done && onHealthCheck && (
          <Button variant="outline" size="sm" className="h-6 shrink-0 border-emerald-300 bg-emerald-50 px-2 text-xs text-emerald-700 hover:bg-emerald-100" onClick={(e) => { e.stopPropagation(); onHealthCheck(); }}>
            Health-Check
          </Button>
        )}
        {!done && onChurnCheck && (
          <Button variant="outline" size="sm" className="h-6 shrink-0 border-amber-300 bg-amber-50 px-2 text-xs text-amber-700 hover:bg-amber-100" onClick={(e) => { e.stopPropagation(); onChurnCheck(); }}>
            Churn-Check
          </Button>
        )}
        {task.due_date && (
          <span
            className={`shrink-0 text-xs ${overdue ? "font-medium text-red-600" : "text-muted-foreground"}`}
          >
            {new Date(task.due_date).toLocaleDateString("de-DE")}
          </span>
        )}
        {!done && (
          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); onDelete(); }}
            className="shrink-0 rounded p-1 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
            title="Aufgabe löschen"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        )}
      </div>

      {!done && task.auto_trigger_error && (
        <p className="mt-1 pl-7 text-xs text-red-600">
          Auto-Trigger fehlgeschlagen: {task.auto_trigger_error}
        </p>
      )}

      {isExpanded && (
        <div className="mt-3 space-y-3 border-t pt-3">
          {task.description && (
            <p className="text-sm text-muted-foreground">{task.description}</p>
          )}
          {task.assigned_to_email && (
            <p className="text-xs text-muted-foreground">
              Zugewiesen: {task.assigned_to_email}
            </p>
          )}
          <p className="text-xs text-muted-foreground">
            Status: {STATUS_LABELS[task.status]}
            {task.completed_at &&
              ` am ${new Date(task.completed_at).toLocaleDateString("de-DE")}`}
            {task.completed_by_email && ` von ${task.completed_by_email}`}
          </p>
          {task.subtasks.length > 0 && (
            <div className="space-y-1">
              <p className="text-xs font-medium">Checkliste:</p>
              {task.subtasks.map((st) => (
                <label key={st.id} className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={st.is_done}
                    onChange={() => onSubtaskToggle(st)}
                    className="h-3.5 w-3.5 rounded border-gray-300"
                  />
                  <span
                    className={st.is_done ? "line-through opacity-60" : ""}
                  >
                    {st.title}
                  </span>
                </label>
              ))}
            </div>
          )}
          {task.notes && (
            <div>
              <p className="text-xs font-medium">Notizen:</p>
              <p className="whitespace-pre-wrap text-sm text-muted-foreground">
                {task.notes}
              </p>
            </div>
          )}
          {!done && (
            <div className="flex gap-2">
              {onSendEmail && (
                <Button variant="outline" size="sm" onClick={onSendEmail}>
                  E-Mail senden
                </Button>
              )}
              {onStartSequence && (
                <Button variant="outline" size="sm" onClick={onStartSequence}>
                  Sequenz starten
                </Button>
              )}
              {onExecuteJira && (
                <Button variant="outline" size="sm" onClick={onExecuteJira}>
                  In Jira ausführen
                </Button>
              )}
              {onExecuteWebhook && (
                <Button variant="outline" size="sm" onClick={onExecuteWebhook}>
                  Webhook ausführen
                </Button>
              )}
              {onSendWhatsApp && (
                <Button variant="outline" size="sm" onClick={onSendWhatsApp}>
                  WhatsApp senden
                </Button>
              )}
              {onHealthCheck && (
                <Button variant="outline" size="sm" onClick={onHealthCheck}>
                  Health-Check ausfüllen
                </Button>
              )}
              {onChurnCheck && (
                <Button variant="outline" size="sm" onClick={onChurnCheck}>
                  Churn-Check ausfüllen
                </Button>
              )}
              <Button size="sm" onClick={onComplete}>
                Erledigt
              </Button>
              <Button variant="outline" size="sm" onClick={onSkip}>
                Überspringen
              </Button>
              <Button variant="destructive" size="sm" onClick={onDelete}>
                Löschen
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------
export function TaskSection({ slug, tenantId }: TaskSectionProps) {
  const [allTasks, setAllTasks] = useState<Task[]>([]);
  const [activeTab, setActiveTab] = useState<TabKey>("due");
  const [showModal, setShowModal] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [message, setMessage] = useState("");
  const [expandedTask, setExpandedTask] = useState<string | null>(null);
  const [collapsedPhases, setCollapsedPhases] = useState<Set<number>>(
    new Set()
  );
  const [emailModalTask, setEmailModalTask] = useState<Task | null>(null);
  const [jiraModalTask, setJiraModalTask] = useState<Task | null>(null);
  const [webhookModalTask, setWebhookModalTask] = useState<Task | null>(null);
  const [sequenceModalTask, setSequenceModalTask] = useState<Task | null>(null);
  const [healthCheckModalTask, setHealthCheckModalTask] = useState<Task | null>(null);
  const [churnCheckModalTask, setChurnCheckModalTask] = useState<Task | null>(null);
  const [whatsAppModalTask, setWhatsAppModalTask] = useState<Task | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [hasEmailProvider, setHasEmailProvider] = useState<boolean | null>(null);
  const [hasWhatsApp, setHasWhatsApp] = useState<boolean | null>(null);
  const [clientServiceTypeIds, setClientServiceTypeIds] = useState<string[]>([]);

  const fetchTasks = useCallback(async () => {
    try {
      const data = await apiFetch<Task[]>(
        `/api/v1/clients/${slug}/tasks/`,
        { tenantId }
      );
      setAllTasks(data);
    } catch {
      /* ignore */
    }
  }, [slug, tenantId]);

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  // Provider-Status einmalig prüfen
  useEffect(() => {
    apiFetch<{ has_active_provider: boolean }>(
      "/api/v1/emails/providers/status/",
      { tenantId }
    )
      .then((data) => setHasEmailProvider(data.has_active_provider))
      .catch(() => setHasEmailProvider(false));
    apiFetch("/api/v1/integrations/whatsapp/connection/", { tenantId })
      .then(() => setHasWhatsApp(true))
      .catch(() => setHasWhatsApp(false));
  }, [tenantId]);

  // Client-Services laden für empfohlene Listen
  useEffect(() => {
    apiFetch<{ service_type: string }[]>(
      `/api/v1/clients/${slug}/services/`,
      { tenantId }
    )
      .then((services) => {
        const ids = [...new Set(services.map((s) => s.service_type).filter(Boolean))];
        setClientServiceTypeIds(ids);
      })
      .catch(() => {});
  }, [slug, tenantId]);

  // --- Tab-Filter (Faellig und Onboarding sind NICHT exklusiv) ---
  const dueTasks = allTasks.filter(
    (t) => t.status === "open" || t.status === "in_progress"
  );

  const backlogTasks = allTasks.filter((t) => t.status === "planned");

  const recurringTasks = allTasks.filter(
    (t) => t.effective_trigger_mode === "auto_on_due" || t.source_list_id
  );

  const onboardingTasks = allTasks.filter((t) =>
    ONBOARDING_GROUP_LABELS.includes(t.group_label) || ONBOARDING_PHASES.includes(t.phase)
  );

  const doneTasks = allTasks.filter((t) => isDoneTask(t));

  const tabConfig: { key: TabKey; label: string; count: number }[] = [
    { key: "due", label: "Fällig", count: dueTasks.length },
    { key: "backlog", label: "Zukünftig", count: backlogTasks.length },
    { key: "recurring", label: "Wiederkehrend", count: recurringTasks.length },
    { key: "onboarding", label: "Onboarding", count: onboardingTasks.length },
    { key: "done", label: "Erledigt", count: doneTasks.length },
  ];

  // --- Onboarding: Auto-Collapse wenn mehrere Gruppen offen ---
  useEffect(() => {
    if (activeTab !== "onboarding") return;

    const phasesWithOpenTasks = ONBOARDING_PHASES.filter((phase) =>
      onboardingTasks.some((t) => t.phase === phase && !isDoneTask(t))
    );

    if (phasesWithOpenTasks.length > 1) {
      setCollapsedPhases(new Set(ONBOARDING_PHASES));
    } else {
      setCollapsedPhases(new Set());
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  function togglePhase(phase: number) {
    setCollapsedPhases((prev) => {
      const next = new Set(prev);
      if (next.has(phase)) next.delete(phase);
      else next.add(phase);
      return next;
    });
  }

  // --- Actions ---
  async function handleGenerateFromModal(templateIds: string[]) {
    setShowModal(false);
    setGenerating(true);
    setMessage("");
    try {
      const created = await apiFetch<Task[]>(
        `/api/v1/clients/${slug}/tasks/generate/`,
        {
          method: "POST",
          body: JSON.stringify({ template_ids: templateIds }),
          tenantId,
        }
      );
      if (created.length === 0) {
        setMessage(
          "Keine neuen Aufgaben erstellt — alle ausgewählten Vorlagen wurden bereits geladen."
        );
      } else {
        setMessage(`${created.length} Aufgaben geladen.`);
      }
      fetchTasks();
    } catch (err) {
      setMessage(
        err instanceof Error ? err.message : "Fehler beim Generieren."
      );
    } finally {
      setGenerating(false);
    }
  }

  async function handleGenerateFromList(listId: string, templateIds: string[]) {
    setShowModal(false);
    setGenerating(true);
    setMessage("");
    try {
      const created = await apiFetch<Task[]>(
        `/api/v1/clients/${slug}/tasks/generate/`,
        {
          method: "POST",
          body: JSON.stringify({
            task_list_id: listId,
            template_ids: templateIds,
          }),
          tenantId,
        }
      );
      if (created.length === 0) {
        setMessage(
          "Keine neuen Aufgaben erstellt — alle ausgewählten Vorlagen wurden bereits geladen."
        );
      } else {
        setMessage(`${created.length} Aufgaben geladen.`);
      }
      fetchTasks();
    } catch (err) {
      setMessage(
        err instanceof Error ? err.message : "Fehler beim Generieren."
      );
    } finally {
      setGenerating(false);
    }
  }

  async function handleComplete(taskId: string) {
    try {
      await apiFetch(`/api/v1/clients/${slug}/tasks/${taskId}/complete/`, {
        method: "POST",
        body: JSON.stringify({}),
        tenantId,
      });
      fetchTasks();
    } catch {
      /* ignore */
    }
  }

  async function handleSkip(taskId: string) {
    try {
      await apiFetch(`/api/v1/clients/${slug}/tasks/${taskId}/skip/`, {
        method: "POST",
        body: JSON.stringify({}),
        tenantId,
      });
      fetchTasks();
    } catch {
      /* ignore */
    }
  }

  async function handleDeleteTask(taskId: string) {
    if (!window.confirm("Aufgabe wirklich löschen?")) return;
    try {
      await apiFetch(`/api/v1/clients/${slug}/tasks/${taskId}/`, {
        method: "DELETE",
        tenantId,
      });
      fetchTasks();
    } catch {
      /* ignore */
    }
  }

  async function handleRemoveList(listId: string, listName: string) {
    if (!window.confirm(`Aufgabenliste "${listName}" entfernen? Alle offenen Aufgaben aus dieser Liste werden gelöscht. Erledigte Aufgaben bleiben erhalten.`)) {
      return;
    }
    try {
      const result = await apiFetch<{ detail: string; deleted_count: number }>(
        `/api/v1/clients/${slug}/tasks/remove-list/`,
        {
          method: "POST",
          body: JSON.stringify({ task_list_id: listId }),
          tenantId,
        }
      );
      setMessage(`${result.detail} (${result.deleted_count} Aufgaben entfernt)`);
      fetchTasks();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Fehler beim Entfernen.");
    }
  }

  function handleExecuteJira(task: Task) {
    setJiraModalTask(task);
  }

  function handleExecuteWebhook(task: Task) {
    setWebhookModalTask(task);
  }

  async function handleSubtaskToggle(taskId: string, subtask: Subtask) {
    try {
      await apiFetch(
        `/api/v1/clients/${slug}/tasks/${taskId}/subtasks/${subtask.id}/`,
        {
          method: "PATCH",
          body: JSON.stringify({ is_done: !subtask.is_done }),
          tenantId,
        }
      );
      fetchTasks();
    } catch {
      /* ignore */
    }
  }

  // --- Render-Helpers ---
  function getVisibleTasks(): Task[] {
    switch (activeTab) {
      case "due":
        return dueTasks;
      case "backlog":
        return backlogTasks;
      case "recurring":
        return recurringTasks;
      case "onboarding":
        return onboardingTasks;
      case "done":
        return doneTasks;
    }
  }

  function renderTaskList(tasks: Task[]) {
    // Gruppierung: group_label wenn vorhanden, sonst Phase
    const grouped = tasks.reduce<Record<string, Task[]>>((acc, task) => {
      const key = task.group_label || PHASE_LABELS[task.phase] || `Phase ${task.phase}`;
      if (!acc[key]) acc[key] = [];
      acc[key].push(task);
      return acc;
    }, {});
    const groupKeys = Object.keys(grouped);

    return (
      <div className="space-y-6">
        {groupKeys.map((groupKey) => (
          <div key={groupKey}>
            <h3 className="mb-2 text-sm font-semibold text-muted-foreground">
              {groupKey}
            </h3>
            <div className="space-y-2">
              {grouped[groupKey].map((task) => (
                <TaskRow
                  key={task.id}
                  task={task}
                  today={today}
                  isExpanded={expandedTask === task.id}
                  onToggleExpand={() =>
                    setExpandedTask(
                      expandedTask === task.id ? null : task.id
                    )
                  }
                  onComplete={() => handleComplete(task.id)}
                  onSkip={() => handleSkip(task.id)}
                  onDelete={() => handleDeleteTask(task.id)}
                  onSubtaskToggle={(st) => handleSubtaskToggle(task.id, st)}
                  onSendEmail={
                    hasEmailProvider && task.action_type === "email" && task.email_templates_detail?.length > 0
                      ? () => setEmailModalTask(task)
                      : undefined
                  }
                  onStartSequence={
                    hasEmailProvider && task.action_type === "email_sequence" && task.email_sequence_slug
                      ? () => setSequenceModalTask(task)
                      : undefined
                  }
                  onExecuteJira={
                    (task.action_type === "jira_project" || task.action_type === "jira_ticket") &&
                    (task.action_template_slug || task.action_sequence_slug)
                      ? () => handleExecuteJira(task)
                      : undefined
                  }
                  onExecuteWebhook={
                    task.action_type === "webhook" &&
                    (task.action_template_slug || task.action_sequence_slug)
                      ? () => handleExecuteWebhook(task)
                      : undefined
                  }
                  onSendWhatsApp={
                    hasWhatsApp && task.action_type === "whatsapp"
                      ? () => setWhatsAppModalTask(task)
                      : undefined
                  }
                  onHealthCheck={
                    task.action_type === "health_check"
                      ? () => setHealthCheckModalTask(task)
                      : undefined
                  }
                  onChurnCheck={
                    task.action_type === "churn_check"
                      ? () => setChurnCheckModalTask(task)
                      : undefined
                  }
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    );
  }

  function renderOnboardingTab() {
    // Gruppierung nach group_label (Fallback Phase)
    const grouped = onboardingTasks.reduce<Record<string, Task[]>>(
      (acc, t) => {
        const key = t.group_label || PHASE_LABELS[t.phase] || `Phase ${t.phase}`;
        if (!acc[key]) acc[key] = [];
        acc[key].push(t);
        return acc;
      },
      {}
    );
    const groupKeys = Object.keys(grouped);

    const totalDone = onboardingTasks.filter((t) => isDoneTask(t)).length;
    const total = onboardingTasks.length;

    return (
      <div className="space-y-4">
        <div>
          <p className="mb-1 text-xs font-medium text-muted-foreground">
            Onboarding-Fortschritt
          </p>
          <ProgressBar done={totalDone} total={total} />
        </div>

        <div className="space-y-3">
          {groupKeys.map((groupKey) => {
            const groupTasks = grouped[groupKey];
            const groupDone = groupTasks.filter((t) => isDoneTask(t)).length;
            const isCollapsed = collapsedPhases.has(groupTasks[0]?.phase ?? 0);
            const allGroupDone = groupDone === groupTasks.length;

            return (
              <div key={groupKey} className="rounded-md border">
                <button
                  type="button"
                  onClick={() => togglePhase(groupTasks[0]?.phase ?? 0)}
                  className="flex w-full items-center gap-3 p-3 text-left hover:bg-muted/50"
                >
                  <span
                    className={`text-xs transition-transform ${isCollapsed ? "" : "rotate-90"}`}
                  >
                    &#9654;
                  </span>
                  <span
                    className={`flex-1 text-sm font-semibold ${allGroupDone ? "text-muted-foreground" : ""}`}
                  >
                    {groupKey}
                  </span>
                  <span className="shrink-0">
                    <ProgressBar
                      done={groupDone}
                      total={groupTasks.length}
                    />
                  </span>
                </button>

                {!isCollapsed && (
                  <div className="space-y-2 border-t px-3 pb-3 pt-2">
                    {groupTasks.map((task) => (
                      <TaskRow
                        key={task.id}
                        task={task}
                        today={today}
                        isExpanded={expandedTask === task.id}
                        onToggleExpand={() =>
                          setExpandedTask(
                            expandedTask === task.id ? null : task.id
                          )
                        }
                        onComplete={() => handleComplete(task.id)}
                        onSkip={() => handleSkip(task.id)}
                        onDelete={() => handleDeleteTask(task.id)}
                        onSubtaskToggle={(st) =>
                          handleSubtaskToggle(task.id, st)
                        }
                        onSendEmail={
                          hasEmailProvider && task.action_type === "email" && task.email_templates_detail?.length > 0
                            ? () => setEmailModalTask(task)
                            : undefined
                        }
                        onStartSequence={
                          hasEmailProvider && task.action_type === "email_sequence" && task.email_sequence_slug
                            ? () => setSequenceModalTask(task)
                            : undefined
                        }
                        onExecuteJira={
                          (task.action_type === "jira_project" || task.action_type === "jira_ticket") &&
                          (task.action_template_slug || task.action_sequence_slug)
                            ? () => handleExecuteJira(task)
                            : undefined
                        }
                        onExecuteWebhook={
                          task.action_type === "webhook" &&
                          (task.action_template_slug || task.action_sequence_slug)
                            ? () => handleExecuteWebhook(task)
                            : undefined
                        }
                        onSendWhatsApp={
                          hasWhatsApp && task.action_type === "whatsapp"
                            ? () => setWhatsAppModalTask(task)
                            : undefined
                        }
                      />
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  // --- Main Render ---
  const visibleTasks = getVisibleTasks();

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Aufgaben</CardTitle>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowCreateModal(true)}
              >
                + Neue Aufgabe
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowModal(true)}
                disabled={generating}
              >
                {generating ? "Laden..." : "Aufgabenliste laden"}
              </Button>
            </div>
          </div>

          {/* Active Lists */}
          {(() => {
            const listMap = new Map<string, { name: string; open: number; total: number }>();
            for (const t of allTasks) {
              if (t.source_list_id && t.source_list_name) {
                const entry = listMap.get(t.source_list_id) || { name: t.source_list_name, open: 0, total: 0 };
                entry.total++;
                if (t.status === "open" || t.status === "in_progress") entry.open++;
                listMap.set(t.source_list_id, entry);
              }
            }
            if (listMap.size === 0) return null;
            return (
              <div className="flex flex-wrap gap-2">
                {Array.from(listMap.entries()).map(([listId, info]) => (
                  <span
                    key={listId}
                    className="inline-flex items-center gap-1 rounded-full bg-muted px-2.5 py-1 text-xs"
                  >
                    {info.name}
                    <span className="text-muted-foreground">
                      ({info.open} offen / {info.total} gesamt)
                    </span>
                    <button
                      type="button"
                      onClick={() => handleRemoveList(listId, info.name)}
                      className="ml-0.5 rounded-full p-0.5 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                      title={`"${info.name}" entfernen`}
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                    </button>
                  </span>
                ))}
              </div>
            );
          })()}

          {/* Tabs */}
          <div className="flex gap-1 border-b">
            {tabConfig.map((tab) => (
              <button
                key={tab.key}
                type="button"
                onClick={() => setActiveTab(tab.key)}
                className={`relative px-3 py-2 text-sm font-medium transition-colors ${
                  activeTab === tab.key
                    ? "text-foreground"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {tab.label}
                {tab.count > 0 && (
                  <span
                    className={`ml-1.5 inline-flex h-5 min-w-5 items-center justify-center rounded-full px-1 text-xs ${
                      activeTab === tab.key
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {tab.count}
                  </span>
                )}
                {activeTab === tab.key && (
                  <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
                )}
              </button>
            ))}
          </div>
        </CardHeader>

        <CardContent>
          {hasEmailProvider === false && (
            <div className="mb-4 rounded-lg border border-yellow-200 bg-yellow-50 p-3">
              <p className="text-sm font-medium text-yellow-800">
                E-Mail-Versand ist noch nicht eingerichtet.
              </p>
              <p className="mt-1 text-sm text-yellow-700">
                E-Mail-Aktionen sind deaktiviert.{" "}
                <a
                  href="/integrationen/nachrichten"
                  className="font-medium underline hover:text-yellow-900"
                >
                  Jetzt konfigurieren →
                </a>
              </p>
            </div>
          )}

          {message && (
            <p
              className={`mb-4 text-sm ${message.includes("Fehler") ? "text-red-600" : "text-green-600"}`}
            >
              {message}
            </p>
          )}

          {visibleTasks.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              {allTasks.length === 0
                ? 'Keine Aufgaben vorhanden. Klicke "Aufgabenliste laden" um Aufgaben aus Vorlagen zu erstellen.'
                : "Keine Aufgaben in dieser Ansicht."}
            </p>
          ) : activeTab === "onboarding" ? (
            renderOnboardingTab()
          ) : (
            renderTaskList(visibleTasks)
          )}
        </CardContent>
      </Card>

      {/* Task-Template Picker Modal */}
      {showModal && (
        <TemplatePickerModal
          tenantId={tenantId}
          clientServiceTypeIds={clientServiceTypeIds}
          onGenerate={handleGenerateFromModal}
          onGenerateFromList={handleGenerateFromList}
          onClose={() => setShowModal(false)}
        />
      )}

      {/* Email Send Modal */}
      {emailModalTask && (
        <EmailSendModal
          slug={slug}
          taskId={emailModalTask.id}
          templates={emailModalTask.email_templates_detail}
          tenantId={tenantId}
          onClose={() => setEmailModalTask(null)}
          onSent={fetchTasks}
        />
      )}

      {/* Jira Execute Modal */}
      {jiraModalTask && (
        <JiraExecuteModal
          slug={slug}
          taskId={jiraModalTask.id}
          taskTitle={jiraModalTask.title}
          actionLabel={jiraModalTask.action_template_slug || jiraModalTask.action_sequence_slug || "Jira-Aktion"}
          tenantId={tenantId}
          onClose={() => setJiraModalTask(null)}
          onExecuted={fetchTasks}
        />
      )}

      {/* Webhook Execute Modal */}
      {webhookModalTask && (
        <WebhookExecuteModal
          slug={slug}
          taskId={webhookModalTask.id}
          taskTitle={webhookModalTask.title}
          actionLabel={webhookModalTask.action_template_slug || webhookModalTask.action_sequence_slug || "Webhook"}
          tenantId={tenantId}
          onClose={() => setWebhookModalTask(null)}
          onExecuted={fetchTasks}
        />
      )}

      {/* Sequence Start Modal */}
      {sequenceModalTask && (
        <SequenceStartModal
          slug={slug}
          taskId={sequenceModalTask.id}
          taskTitle={sequenceModalTask.title}
          sequenceName={sequenceModalTask.email_sequence_slug || ""}
          tenantId={tenantId}
          onClose={() => setSequenceModalTask(null)}
          onStarted={fetchTasks}
        />
      )}

      {/* Manual Task Create Modal */}
      {showCreateModal && (
        <ManualTaskCreateModal
          slug={slug}
          tenantId={tenantId}
          onClose={() => setShowCreateModal(false)}
          onCreated={fetchTasks}
        />
      )}

      {/* Health-Check Modal */}
      {healthCheckModalTask && (
        <HealthCheckModal
          slug={slug}
          taskId={healthCheckModalTask.id}
          tenantId={tenantId}
          onClose={() => setHealthCheckModalTask(null)}
          onSubmitted={fetchTasks}
        />
      )}

      {/* Churn-Check Modal */}
      {churnCheckModalTask && (
        <ChurnCheckModal
          slug={slug}
          taskId={churnCheckModalTask.id}
          tenantId={tenantId}
          onClose={() => setChurnCheckModalTask(null)}
          onSubmitted={fetchTasks}
        />
      )}

      {/* WhatsApp Send Modal */}
      {whatsAppModalTask && (
        <WhatsAppSendModal
          slug={slug}
          taskId={whatsAppModalTask.id}
          taskTitle={whatsAppModalTask.title}
          tenantId={tenantId}
          onClose={() => setWhatsAppModalTask(null)}
          onSent={fetchTasks}
        />
      )}
    </>
  );
}
