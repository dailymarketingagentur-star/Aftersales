"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
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
  whatsapp: "WhatsApp",
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

export default function VorlagenPage() {
  const { currentTenantId } = useTenant();
  const [templates, setTemplates] = useState<TaskTemplate[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!currentTenantId) return;
    apiFetch<TaskTemplate[]>("/api/v1/tasks/templates/", { tenantId: currentTenantId })
      .then(setTemplates)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [currentTenantId]);

  // Gruppiert nach Aktionstyp
  const grouped = templates.reduce<Record<string, TaskTemplate[]>>((acc, t) => {
    const key = t.action_type;
    if (!acc[key]) acc[key] = [];
    acc[key].push(t);
    return acc;
  }, {});

  // Sortierung: Aktionstypen alphabetisch nach Label
  const actionTypes = Object.keys(grouped).sort((a, b) => {
    return (ACTION_LABELS[a] || a).localeCompare(ACTION_LABELS[b] || b);
  });

  if (loading) return <p className="text-sm text-muted-foreground">Laden...</p>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Aufgaben-Vorlagen</h1>
        <Link href="/aufgaben/vorlagen/neu">
          <Button size="sm">Neue Vorlage</Button>
        </Link>
      </div>

      {actionTypes.map((actionType) => (
        <div key={actionType}>
          <h2 className="mb-3 text-sm font-semibold text-muted-foreground">
            {ACTION_LABELS[actionType] || actionType}
            <span className="ml-2 text-xs font-normal">({grouped[actionType].length})</span>
          </h2>
          <div className="space-y-2">
            {grouped[actionType]
              .sort((a, b) => a.name.localeCompare(b.name))
              .map((tpl) => (
              <Link key={tpl.id} href={`/aufgaben/vorlagen/${tpl.id}`}>
                <Card className="cursor-pointer transition-shadow hover:shadow-md">
                  <CardContent className="flex items-center gap-3 py-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">{tpl.name}</span>
                        {tpl.is_system && (
                          <span className="rounded bg-purple-100 px-1.5 py-0.5 text-xs text-purple-800">System</span>
                        )}
                        {tpl.email_templates_detail?.length > 0 && (
                          <span className="rounded bg-green-100 px-1.5 py-0.5 text-xs text-green-800">E-Mail</span>
                        )}
                        {(tpl.action_template_slug || tpl.action_sequence_slug) && (
                          <span className="rounded bg-indigo-100 px-1.5 py-0.5 text-xs text-indigo-800">Jira</span>
                        )}
                        {!tpl.is_active && (
                          <span className="rounded bg-yellow-100 px-1.5 py-0.5 text-xs text-yellow-800">Inaktiv</span>
                        )}
                      </div>
                      {tpl.description && (
                        <p className="mt-0.5 text-xs text-muted-foreground line-clamp-1">{tpl.description}</p>
                      )}
                    </div>
                    <span className={`shrink-0 rounded px-1.5 py-0.5 text-xs font-medium ${PRIORITY_COLORS[tpl.priority]}`}>
                      {PRIORITY_LABELS[tpl.priority]}
                    </span>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        </div>
      ))}

      {templates.length === 0 && (
        <p className="text-sm text-muted-foreground">Keine Vorlagen vorhanden.</p>
      )}
    </div>
  );
}
