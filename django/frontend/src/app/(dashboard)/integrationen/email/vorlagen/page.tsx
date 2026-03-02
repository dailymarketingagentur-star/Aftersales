"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useTenant } from "@/hooks/use-tenant";
import { apiFetch } from "@/lib/api";
import type { EmailTemplate } from "@/types/email";

export default function VorlagenPage() {
  const { currentTenantId } = useTenant();
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!currentTenantId) return;
    apiFetch<EmailTemplate[]>("/api/v1/emails/templates/", { tenantId: currentTenantId })
      .then(setTemplates)
      .catch(() => setTemplates([]))
      .finally(() => setLoading(false));
  }, [currentTenantId]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">E-Mail-Vorlagen</h1>
        <div className="flex gap-2">
          <Link href="/integrationen/email">
            <Button variant="outline" size="sm">Zurück</Button>
          </Link>
          <Link href="/integrationen/email/vorlagen/neu">
            <Button size="sm">Neue Vorlage</Button>
          </Link>
        </div>
      </div>

      {loading ? (
        <p className="text-muted-foreground">Lade Vorlagen...</p>
      ) : templates.length === 0 ? (
        <p className="text-muted-foreground">Keine Vorlagen vorhanden.</p>
      ) : (
        <div className="space-y-3">
          {templates.map((tpl) => (
            <Link key={tpl.id} href={`/integrationen/email/vorlagen/${tpl.id}`}>
              <Card className="cursor-pointer transition-shadow hover:shadow-md">
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center justify-between text-base">
                    <span>{tpl.name}</span>
                    <span className="flex items-center gap-2">
                      {!tpl.tenant && (
                        <span className="rounded bg-blue-100 px-2 py-0.5 text-xs text-blue-700">System</span>
                      )}
                      <span className={`inline-block h-2.5 w-2.5 rounded-full ${tpl.is_active ? "bg-green-500" : "bg-gray-300"}`} />
                    </span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <p className="text-sm text-muted-foreground">
                    <span className="font-mono text-xs">{tpl.slug}</span> — {tpl.subject}
                  </p>
                  {tpl.variables.length > 0 && (
                    <p className="mt-1 text-xs text-muted-foreground">
                      Variablen: {tpl.variables.map((v) => `{{${v}}}`).join(", ")}
                    </p>
                  )}
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
