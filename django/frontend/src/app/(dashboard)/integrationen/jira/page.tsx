"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useTenant } from "@/hooks/use-tenant";
import { apiFetch } from "@/lib/api";
import type { ActionExecutionListItem, ActionSequence, ActionTemplate, JiraConnection } from "@/types/integration";

export default function JiraPage() {
  const { currentTenantId } = useTenant();
  const [connection, setConnection] = useState<JiraConnection | null>(null);
  const [templates, setTemplates] = useState<ActionTemplate[]>([]);
  const [sequences, setSequences] = useState<ActionSequence[]>([]);
  const [recentExecutions, setRecentExecutions] = useState<ActionExecutionListItem[]>([]);

  useEffect(() => {
    if (!currentTenantId) return;

    apiFetch<JiraConnection>("/api/v1/integrations/connection/", { tenantId: currentTenantId })
      .then(setConnection)
      .catch(() => setConnection(null));

    apiFetch<ActionTemplate[]>("/api/v1/integrations/templates/", { tenantId: currentTenantId })
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
        <h1 className="text-2xl font-bold">Jira-Integration</h1>
        <Link href="/integrationen">
          <Button variant="outline" size="sm">Zurück</Button>
        </Link>
      </div>

      {/* Warning Banner bei fehlgeschlagener Verbindung */}
      {connection && connection.last_test_success === false && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <div className="flex items-start gap-3">
            <span className="mt-0.5 text-red-600 text-lg">&#9888;</span>
            <div>
              <p className="font-medium text-red-800">
                Jira-Verbindung fehlgeschlagen
              </p>
              <p className="mt-1 text-sm text-red-700">
                Der letzte Verbindungstest war nicht erfolgreich. Dein API-Token ist
                wahrscheinlich abgelaufen oder ungültig. Jira-Aktionen (z.B. Projekt-
                oder Ticket-Erstellung) funktionieren nicht, bis der Token erneuert wird.
              </p>
              <div className="mt-3">
                <Link href="/integrationen/jira/verbindung">
                  <Button size="sm" variant="destructive">
                    Token jetzt erneuern
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Connection Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            Verbindungsstatus
            <span
              className={`inline-block h-3 w-3 rounded-full ${
                !connection
                  ? "bg-gray-300"
                  : connection.last_test_success === false
                    ? "bg-red-500"
                    : "bg-green-500"
              }`}
            />
          </CardTitle>
        </CardHeader>
        <CardContent>
          {connection ? (
            <div className="space-y-1 text-sm">
              <p><span className="font-medium">URL:</span> {connection.jira_url}</p>
              <p><span className="font-medium">Email:</span> {connection.jira_email}</p>
              {connection.last_tested_at && (
                <p>
                  <span className="font-medium">Letzter Test:</span>{" "}
                  {new Date(connection.last_tested_at).toLocaleString("de-DE")}{" — "}
                  <span className={connection.last_test_success === false ? "font-medium text-red-600" : "text-green-600"}>
                    {connection.last_test_success ? "Erfolgreich" : "Fehlgeschlagen"}
                  </span>
                </p>
              )}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">Keine Verbindung konfiguriert.</p>
          )}
          <div className="mt-4">
            <Link href="/integrationen/jira/verbindung">
              <Button variant="outline" size="sm">
                {connection ? "Verbindung bearbeiten" : "Verbindung einrichten"}
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>

      {/* Sequenzen — prominent */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Sequenzen</CardTitle>
              <CardDescription>
                Mehrstufige Jira-Aktionen, die direkt aus Aufgaben heraus ausgeführt werden können
              </CardDescription>
            </div>
            <Link href="/integrationen/jira/sequenzen">
              <Button variant="outline" size="sm">Alle Sequenzen ansehen</Button>
            </Link>
          </div>
        </CardHeader>
        <CardContent>
          {sequences.length === 0 ? (
            <div className="flex items-center justify-between rounded-lg border border-dashed p-4">
              <p className="text-sm text-muted-foreground">
                Noch keine Sequenzen angelegt. Erstelle eine Sequenz, um mehrere Jira-Aktionen zu verketten.
              </p>
              <Link href="/integrationen/jira/sequenzen/neu">
                <Button size="sm">Neue Sequenz</Button>
              </Link>
            </div>
          ) : (
            <div className="space-y-2">
              {sequences.map((seq) => (
                <Link
                  key={seq.id}
                  href={`/integrationen/jira/sequenzen/${seq.id}`}
                  className="flex items-center justify-between rounded-lg border p-3 text-sm transition-colors hover:bg-accent"
                >
                  <div className="flex items-center gap-3">
                    <span className="font-medium">{seq.name}</span>
                    {seq.description && (
                      <span className="text-muted-foreground">{seq.description}</span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="rounded bg-indigo-100 px-2 py-0.5 text-xs font-medium text-indigo-700">
                      {seq.step_count} {seq.step_count === 1 ? "Schritt" : "Schritte"}
                    </span>
                    {!seq.is_active && (
                      <span className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
                        inaktiv
                      </span>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Vorlagen + Verlauf */}
      <div className="grid gap-4 md:grid-cols-2">
        <Link href="/integrationen/jira/vorlagen">
          <Card className="cursor-pointer transition-shadow hover:shadow-md">
            <CardHeader>
              <CardTitle>Vorlagen</CardTitle>
              <CardDescription>{templates.length} API-Vorlagen verfügbar</CardDescription>
            </CardHeader>
          </Card>
        </Link>

        <Link href="/integrationen/jira/verlauf">
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
                  href={`/integrationen/jira/verlauf/${exec.id}`}
                  className="flex items-center justify-between rounded-lg border p-3 text-sm transition-colors hover:bg-accent"
                >
                  <div>
                    <span className="font-medium">
                      {exec.sequence_slug || exec.template_slug}
                    </span>
                    {exec.entity_type && (
                      <span className="ml-2 text-muted-foreground">
                        ({exec.entity_type})
                      </span>
                    )}
                  </div>
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
