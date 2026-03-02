"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useTenant } from "@/hooks/use-tenant";
import { apiFetch } from "@/lib/api";
import type { ActionExecution } from "@/types/integration";

const statusColors: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-800",
  running: "bg-blue-100 text-blue-800",
  completed: "bg-green-100 text-green-800",
  failed: "bg-red-100 text-red-800",
  cancelled: "bg-gray-100 text-gray-800",
  success: "bg-green-100 text-green-800",
  skipped: "bg-gray-100 text-gray-800",
};

export default function WebhookVerlaufDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { currentTenantId } = useTenant();
  const [execution, setExecution] = useState<ActionExecution | null>(null);
  const [cancelling, setCancelling] = useState(false);

  function fetchExecution() {
    if (!currentTenantId || !id) return;
    apiFetch<ActionExecution>(`/api/v1/integrations/executions/${id}/`, { tenantId: currentTenantId })
      .then(setExecution)
      .catch(() => {});
  }

  useEffect(() => {
    fetchExecution();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentTenantId, id]);

  async function handleCancel() {
    setCancelling(true);
    try {
      await apiFetch(`/api/v1/integrations/executions/${id}/cancel/`, {
        method: "POST",
        tenantId: currentTenantId!,
      });
      fetchExecution();
    } catch {
      // ignore
    } finally {
      setCancelling(false);
    }
  }

  if (!execution) return <p>Laden...</p>;

  const canCancel = execution.status === "pending" || execution.status === "running";

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">
          Ausführung: {execution.sequence_slug || execution.template_slug || "—"}
        </h1>
        <div className="flex gap-2">
          <Link href="/integrationen/webhooks/verlauf">
            <Button variant="outline" size="sm">Zurück</Button>
          </Link>
          {canCancel && (
            <Button variant="destructive" size="sm" onClick={handleCancel} disabled={cancelling}>
              {cancelling ? "Abbrechen..." : "Abbrechen"}
            </Button>
          )}
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            Übersicht
            <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${statusColors[execution.status] || ""}`}>
              {execution.status}
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid gap-2 text-sm md:grid-cols-2">
            <div>
              <dt className="font-medium">Ausgelöst von</dt>
              <dd className="text-muted-foreground">{execution.triggered_by_email || "—"}</dd>
            </div>
            <div>
              <dt className="font-medium">Zeitpunkt</dt>
              <dd className="text-muted-foreground">{new Date(execution.created_at).toLocaleString("de-DE")}</dd>
            </div>
            {execution.entity_type && (
              <div>
                <dt className="font-medium">Entität</dt>
                <dd className="text-muted-foreground">{execution.entity_type}: {execution.entity_id}</dd>
              </div>
            )}
            {execution.error_message && (
              <div className="md:col-span-2">
                <dt className="font-medium text-red-600">Fehler</dt>
                <dd className="text-red-600">{execution.error_message}</dd>
              </div>
            )}
          </dl>
        </CardContent>
      </Card>

      {Object.keys(execution.input_context).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Input-Kontext</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="overflow-auto rounded-md bg-muted p-4 font-mono text-sm">
              {JSON.stringify(execution.input_context, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Schritte ({execution.step_logs.length})</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {execution.step_logs.length === 0 && (
            <p className="text-sm text-muted-foreground">Noch keine Schritte ausgeführt.</p>
          )}
          {execution.step_logs.map((log) => (
            <div key={log.id} className="rounded-lg border p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="font-medium">Schritt {log.position}</span>
                  <span className="font-mono text-xs text-muted-foreground">{log.template_slug}</span>
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${statusColors[log.status] || ""}`}>
                    {log.status}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  {log.status_code && <span>HTTP {log.status_code}</span>}
                  {log.duration_ms != null && <span>{log.duration_ms}ms</span>}
                </div>
              </div>

              <div className="text-sm">
                <span className="font-mono font-bold">{log.method}</span>{" "}
                <span className="font-mono text-muted-foreground">{log.url}</span>
              </div>

              {log.error_message && (
                <p className="text-sm text-red-600">{log.error_message}</p>
              )}

              <details className="text-sm">
                <summary className="cursor-pointer font-medium text-muted-foreground hover:text-foreground">
                  Request/Response Details
                </summary>
                <div className="mt-2 space-y-2">
                  {Object.keys(log.request_body).length > 0 && (
                    <div>
                      <p className="font-medium">Request Body:</p>
                      <pre className="overflow-auto rounded bg-muted p-2 font-mono text-xs">
                        {JSON.stringify(log.request_body, null, 2)}
                      </pre>
                    </div>
                  )}
                  {Object.keys(log.response_body).length > 0 && (
                    <div>
                      <p className="font-medium">Response Body:</p>
                      <pre className="overflow-auto rounded bg-muted p-2 font-mono text-xs">
                        {JSON.stringify(log.response_body, null, 2)}
                      </pre>
                    </div>
                  )}
                  {Object.keys(log.extracted_outputs).length > 0 && (
                    <div>
                      <p className="font-medium">Extrahierte Outputs:</p>
                      <pre className="overflow-auto rounded bg-muted p-2 font-mono text-xs">
                        {JSON.stringify(log.extracted_outputs, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              </details>
            </div>
          ))}
        </CardContent>
      </Card>

      {Object.keys(execution.accumulated_context).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Akkumulierter Kontext</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="overflow-auto rounded-md bg-muted p-4 font-mono text-sm">
              {JSON.stringify(execution.accumulated_context, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
