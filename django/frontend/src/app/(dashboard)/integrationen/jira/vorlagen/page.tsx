"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useTenant } from "@/hooks/use-tenant";
import { apiFetch } from "@/lib/api";
import type { ActionTemplate } from "@/types/integration";

const TEMPLATE_INFO: Record<string, { summary: string; example: string }> = {
  "create-jira-project": {
    summary: "Erstellt ein neues Projekt in Jira für einen Mandanten.",
    example: 'z.B. Projektname: "Muster GmbH", Projekt-Key: "MUSTERGMB"',
  },
  "create-jira-issue": {
    summary: "Erstellt ein neues Ticket (Issue) in einem bestehenden Jira-Projekt.",
    example: 'z.B. "Onboarding: Muster GmbH" als Task-Ticket',
  },
  "update-jira-issue": {
    summary: "Aktualisiert ein bestehendes Jira-Ticket (z.B. Titel ändern).",
    example: "z.B. Ticket MUSTER-1 umbenennen",
  },
};

const VARIABLE_LABELS: Record<string, string> = {
  PROJECT_KEY: "Projekt-Kürzel",
  PROJECT_NAME: "Projektname",
  LEAD_ACCOUNT_ID: "Verantwortlicher (Jira-Account-ID)",
  ISSUE_SUMMARY: "Ticket-Titel",
  ISSUE_DESCRIPTION: "Ticket-Beschreibung",
  ISSUE_TYPE: "Ticket-Typ (z.B. Task)",
  ISSUE_KEY: "Ticket-Schlüssel (z.B. MUSTER-1)",
};

export default function VorlagenPage() {
  const { currentTenantId } = useTenant();
  const [templates, setTemplates] = useState<ActionTemplate[]>([]);

  useEffect(() => {
    if (!currentTenantId) return;
    apiFetch<ActionTemplate[]>("/api/v1/integrations/templates/", { tenantId: currentTenantId })
      .then(setTemplates)
      .catch(() => {});
  }, [currentTenantId]);

  const methodColors: Record<string, string> = {
    GET: "bg-blue-100 text-blue-800",
    POST: "bg-green-100 text-green-800",
    PUT: "bg-yellow-100 text-yellow-800",
    DELETE: "bg-red-100 text-red-800",
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Vorlagen</h1>
        <div className="flex gap-2">
          <Link href="/integrationen/jira">
            <Button variant="outline" size="sm">Zurück</Button>
          </Link>
          <Link href="/integrationen/jira/vorlagen/neu">
            <Button size="sm">Neue Vorlage</Button>
          </Link>
        </div>
      </div>

      <div className="space-y-3">
        {templates.map((tpl) => {
          const info = TEMPLATE_INFO[tpl.slug];
          return (
            <Link key={tpl.id} href={`/integrationen/jira/vorlagen/${tpl.id}`}>
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
                  <p className="text-sm text-muted-foreground">
                    {info?.summary || tpl.description || "Keine Beschreibung"}
                  </p>
                  {info?.example && (
                    <p className="text-sm italic text-muted-foreground/70">{info.example}</p>
                  )}
                  {tpl.variables.length > 0 && (
                    <div>
                      <p className="mb-1 text-xs font-medium text-muted-foreground">Benötigte Eingaben:</p>
                      <div className="flex flex-wrap gap-1">
                        {tpl.variables.map((v) => (
                          <span key={v} className="rounded bg-muted px-1.5 py-0.5 text-xs">
                            {VARIABLE_LABELS[v] || v}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  <p className="font-mono text-xs text-muted-foreground/50">
                    <span className={`mr-1 rounded px-1 py-0.5 text-[10px] font-bold ${methodColors[tpl.method] || "bg-gray-100"}`}>
                      {tpl.method}
                    </span>
                    {tpl.endpoint}
                  </p>
                </CardContent>
              </Card>
            </Link>
          );
        })}
        {templates.length === 0 && (
          <p className="text-sm text-muted-foreground">Keine Vorlagen vorhanden.</p>
        )}
      </div>
    </div>
  );
}
