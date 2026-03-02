"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useTenant } from "@/hooks/use-tenant";
import { apiFetch } from "@/lib/api";
import type { ActionExecutionListItem } from "@/types/integration";

const statusColors: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-800",
  running: "bg-blue-100 text-blue-800",
  completed: "bg-green-100 text-green-800",
  failed: "bg-red-100 text-red-800",
  cancelled: "bg-gray-100 text-gray-800",
};

export default function VerlaufPage() {
  const { currentTenantId } = useTenant();
  const [executions, setExecutions] = useState<ActionExecutionListItem[]>([]);
  const [statusFilter, setStatusFilter] = useState("");

  useEffect(() => {
    if (!currentTenantId) return;
    const params = statusFilter ? `?status=${statusFilter}` : "";
    apiFetch<ActionExecutionListItem[]>(`/api/v1/integrations/executions/${params}`, {
      tenantId: currentTenantId,
    })
      .then(setExecutions)
      .catch(() => {});
  }, [currentTenantId, statusFilter]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Ausführungsverlauf</h1>
        <Link href="/integrationen/jira">
          <Button variant="outline" size="sm">Zurück</Button>
        </Link>
      </div>

      {/* Filter */}
      <div className="flex gap-2">
        {["", "pending", "running", "completed", "failed", "cancelled"].map((s) => (
          <Button
            key={s}
            variant={statusFilter === s ? "default" : "outline"}
            size="sm"
            onClick={() => setStatusFilter(s)}
          >
            {s || "Alle"}
          </Button>
        ))}
      </div>

      {/* Execution list */}
      <div className="space-y-2">
        {executions.map((exec) => (
          <Link key={exec.id} href={`/integrationen/jira/verlauf/${exec.id}`}>
            <Card className="cursor-pointer transition-shadow hover:shadow-md">
              <CardContent className="flex items-center justify-between py-4">
                <div>
                  <p className="font-medium">
                    {exec.sequence_slug || exec.template_slug || "—"}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {exec.triggered_by_email}
                    {exec.entity_type && ` — ${exec.entity_type}`}
                    {exec.entity_id && `: ${exec.entity_id.slice(0, 8)}...`}
                  </p>
                </div>
                <div className="flex items-center gap-3 text-sm">
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${statusColors[exec.status] || "bg-gray-100"}`}>
                    {exec.status}
                  </span>
                  <span className="text-muted-foreground">
                    {new Date(exec.created_at).toLocaleString("de-DE")}
                  </span>
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
        {executions.length === 0 && (
          <p className="text-sm text-muted-foreground">Keine Ausführungen gefunden.</p>
        )}
      </div>
    </div>
  );
}
