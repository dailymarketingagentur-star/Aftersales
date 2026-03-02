"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useTenant } from "@/hooks/use-tenant";
import { apiFetch } from "@/lib/api";
import type { TaskList } from "@/types/task";

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

export default function AufgabenListenPage() {
  const { currentTenantId } = useTenant();
  const [lists, setLists] = useState<TaskList[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!currentTenantId) return;
    apiFetch<TaskList[]>("/api/v1/tasks/lists/", { tenantId: currentTenantId })
      .then(setLists)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [currentTenantId]);

  function getGroupSummary(list: TaskList): string {
    if (list.items.length === 0) return "Keine Vorlagen";
    const groups = [...new Set(list.items.map((i) => i.group_label).filter(Boolean))];
    if (groups.length === 0) return `${list.item_count} Vorlagen`;
    return groups.join(", ");
  }

  function getActionTypeSummary(list: TaskList): Record<string, number> {
    const counts: Record<string, number> = {};
    for (const item of list.items) {
      counts[item.action_type] = (counts[item.action_type] || 0) + 1;
    }
    return counts;
  }

  if (loading) return <p className="text-sm text-muted-foreground">Laden...</p>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Aufgabenlisten</h1>
        <Link href="/aufgaben/listen/neu">
          <Button size="sm">Neue Liste</Button>
        </Link>
      </div>

      <div className="space-y-3">
        {lists.map((list) => {
          const actionCounts = getActionTypeSummary(list);
          return (
            <Link key={list.id} href={`/aufgaben/listen/${list.id}`}>
              <Card className="cursor-pointer transition-shadow hover:shadow-md">
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center gap-2 text-base">
                    {list.name}
                    {list.is_system && (
                      <span className="rounded bg-purple-100 px-2 py-0.5 text-xs text-purple-800">
                        System
                      </span>
                    )}
                    {list.default_for_service_type_name && (
                      <span className="rounded bg-teal-100 px-2 py-0.5 text-xs text-teal-800">
                        Standard: {list.default_for_service_type_name}
                      </span>
                    )}
                    <span className="rounded bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                      {list.item_count} Vorlagen
                    </span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 pt-0">
                  {list.description && (
                    <p className="text-sm text-muted-foreground">{list.description}</p>
                  )}
                  <div className="flex flex-wrap gap-2">
                    <span className="rounded bg-blue-50 px-2 py-0.5 text-xs text-blue-700">
                      {getGroupSummary(list)}
                    </span>
                    {Object.entries(actionCounts).map(([type, count]) => (
                      <span key={type} className="rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-600">
                        {count}x {ACTION_LABELS[type] || type}
                      </span>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </Link>
          );
        })}
        {lists.length === 0 && (
          <p className="text-sm text-muted-foreground">
            Keine Aufgabenlisten vorhanden.{" "}
            <Link href="/aufgaben/listen/neu" className="underline">
              Jetzt erstellen
            </Link>
          </p>
        )}
      </div>
    </div>
  );
}
