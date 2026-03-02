"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useTenant } from "@/hooks/use-tenant";
import { apiFetch } from "@/lib/api";
import type { ActionTemplate } from "@/types/integration";

const METHOD_COLORS: Record<string, string> = {
  GET: "bg-blue-100 text-blue-800",
  POST: "bg-green-100 text-green-800",
  PUT: "bg-yellow-100 text-yellow-800",
  DELETE: "bg-red-100 text-red-800",
};

const AUTH_LABELS: Record<string, string> = {
  none: "Keine Auth",
  bearer: "Bearer Token",
  basic: "Basic Auth",
  api_key: "API Key",
};

export default function WebhookVorlagenPage() {
  const { currentTenantId } = useTenant();
  const [templates, setTemplates] = useState<ActionTemplate[]>([]);

  useEffect(() => {
    if (!currentTenantId) return;
    apiFetch<ActionTemplate[]>("/api/v1/integrations/templates/?target_type=webhook", { tenantId: currentTenantId })
      .then(setTemplates)
      .catch(() => {});
  }, [currentTenantId]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Webhook-Vorlagen</h1>
        <div className="flex gap-2">
          <Link href="/integrationen/webhooks">
            <Button variant="outline" size="sm">Zurück</Button>
          </Link>
          <Link href="/integrationen/webhooks/vorlagen/neu">
            <Button size="sm">Neue Vorlage</Button>
          </Link>
        </div>
      </div>

      <div className="space-y-3">
        {templates.map((tpl) => (
          <Link key={tpl.id} href={`/integrationen/webhooks/vorlagen/${tpl.id}`}>
            <Card className="cursor-pointer transition-shadow hover:shadow-md">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-base">
                  {tpl.name}
                  {tpl.is_system && (
                    <span className="rounded bg-purple-100 px-2 py-0.5 text-xs text-purple-800">System</span>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 pt-0">
                {tpl.description && (
                  <p className="text-sm text-muted-foreground">{tpl.description}</p>
                )}
                <div className="flex items-center gap-2">
                  <span className={`rounded px-1.5 py-0.5 text-[10px] font-bold ${METHOD_COLORS[tpl.method] || "bg-gray-100"}`}>
                    {tpl.method}
                  </span>
                  <span className="truncate font-mono text-xs text-muted-foreground">
                    {tpl.webhook_url || tpl.endpoint}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="rounded bg-violet-100 px-2 py-0.5 text-xs text-violet-700">
                    {AUTH_LABELS[tpl.auth_type] || tpl.auth_type}
                  </span>
                  {tpl.variables.length > 0 && (
                    <span className="text-xs text-muted-foreground">
                      {tpl.variables.length} Variable{tpl.variables.length !== 1 && "n"}
                    </span>
                  )}
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
        {templates.length === 0 && (
          <p className="text-sm text-muted-foreground">Keine Webhook-Vorlagen vorhanden.</p>
        )}
      </div>
    </div>
  );
}
