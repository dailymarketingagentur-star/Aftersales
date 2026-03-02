"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useTenant } from "@/hooks/use-tenant";
import { apiFetch } from "@/lib/api";
import type { ActionExecutionListItem, ActionSequence, ActionTemplate } from "@/types/integration";

export default function WebhooksPage() {
  const { currentTenantId } = useTenant();
  const [templates, setTemplates] = useState<ActionTemplate[]>([]);
  const [sequences, setSequences] = useState<ActionSequence[]>([]);
  const [recentExecutions, setRecentExecutions] = useState<ActionExecutionListItem[]>([]);

  useEffect(() => {
    if (!currentTenantId) return;

    apiFetch<ActionTemplate[]>("/api/v1/integrations/templates/?target_type=webhook", { tenantId: currentTenantId })
      .then(setTemplates)
      .catch(() => {});

    apiFetch<ActionSequence[]>("/api/v1/integrations/sequences/", { tenantId: currentTenantId })
      .then(setSequences)
      .catch(() => {});

    apiFetch<ActionExecutionListItem[]>("/api/v1/integrations/executions/", { tenantId: currentTenantId })
      .then((data) => setRecentExecutions(data.slice(0, 5)))
      .catch(() => {});
  }, [currentTenantId]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Webhooks</h1>
        <Link href="/integrationen">
          <Button variant="outline" size="sm">Zurück</Button>
        </Link>
      </div>

      {/* Sequenzen */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Sequenzen</CardTitle>
              <CardDescription>
                Mehrstufige Webhook-Aufrufe, die aus Aufgaben heraus ausgeführt werden können
              </CardDescription>
            </div>
            <Link href="/integrationen/webhooks/sequenzen">
              <Button variant="outline" size="sm">Alle Sequenzen</Button>
            </Link>
          </div>
        </CardHeader>
        <CardContent>
          {sequences.length === 0 ? (
            <div className="flex items-center justify-between rounded-lg border border-dashed p-4">
              <p className="text-sm text-muted-foreground">
                Noch keine Sequenzen angelegt.
              </p>
              <Link href="/integrationen/webhooks/sequenzen/neu">
                <Button size="sm">Neue Sequenz</Button>
              </Link>
            </div>
          ) : (
            <div className="space-y-2">
              {sequences.map((seq) => (
                <Link
                  key={seq.id}
                  href={`/integrationen/webhooks/sequenzen/${seq.id}`}
                  className="flex items-center justify-between rounded-lg border p-3 text-sm transition-colors hover:bg-accent"
                >
                  <div className="flex items-center gap-3">
                    <span className="font-medium">{seq.name}</span>
                    {seq.description && (
                      <span className="text-muted-foreground">{seq.description}</span>
                    )}
                  </div>
                  <span className="rounded bg-violet-100 px-2 py-0.5 text-xs font-medium text-violet-700">
                    {seq.step_count} {seq.step_count === 1 ? "Schritt" : "Schritte"}
                  </span>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Vorlagen + Verlauf */}
      <div className="grid gap-4 md:grid-cols-2">
        <Link href="/integrationen/webhooks/vorlagen">
          <Card className="cursor-pointer transition-shadow hover:shadow-md">
            <CardHeader>
              <CardTitle>Vorlagen</CardTitle>
              <CardDescription>{templates.length} Webhook-Vorlagen verfügbar</CardDescription>
            </CardHeader>
          </Card>
        </Link>

        <Link href="/integrationen/webhooks/verlauf">
          <Card className="cursor-pointer transition-shadow hover:shadow-md">
            <CardHeader>
              <CardTitle>Verlauf</CardTitle>
              <CardDescription>{recentExecutions.length} letzte Ausführungen</CardDescription>
            </CardHeader>
          </Card>
        </Link>
      </div>

      {/* Recent Executions */}
      {recentExecutions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Letzte Ausführungen</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {recentExecutions.map((exec) => (
                <Link
                  key={exec.id}
                  href={`/integrationen/webhooks/verlauf/${exec.id}`}
                  className="flex items-center justify-between rounded-lg border p-3 text-sm transition-colors hover:bg-accent"
                >
                  <span className="font-medium">
                    {exec.sequence_slug || exec.template_slug}
                  </span>
                  <div className="flex items-center gap-2">
                    <StatusBadge status={exec.status} />
                    <span className="text-muted-foreground">
                      {new Date(exec.created_at).toLocaleString("de-DE")}
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    pending: "bg-yellow-100 text-yellow-800",
    running: "bg-blue-100 text-blue-800",
    completed: "bg-green-100 text-green-800",
    failed: "bg-red-100 text-red-800",
    cancelled: "bg-gray-100 text-gray-800",
  };

  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${colors[status] || "bg-gray-100"}`}>
      {status}
    </span>
  );
}
