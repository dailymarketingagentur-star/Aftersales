"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useTenant } from "@/hooks/use-tenant";
import { apiFetch } from "@/lib/api";
import type { ActionSequence } from "@/types/integration";

export default function SequenzenPage() {
  const { currentTenantId } = useTenant();
  const [sequences, setSequences] = useState<ActionSequence[]>([]);

  useEffect(() => {
    if (!currentTenantId) return;
    apiFetch<ActionSequence[]>("/api/v1/integrations/sequences/", { tenantId: currentTenantId })
      .then(setSequences)
      .catch(() => {});
  }, [currentTenantId]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Sequenzen</h1>
        <div className="flex gap-2">
          <Link href="/integrationen/jira">
            <Button variant="outline" size="sm">Zurück</Button>
          </Link>
          <Link href="/integrationen/jira/sequenzen/neu">
            <Button size="sm">Neue Sequenz</Button>
          </Link>
        </div>
      </div>

      <div className="space-y-3">
        {sequences.map((seq) => (
          <Link key={seq.id} href={`/integrationen/jira/sequenzen/${seq.id}`}>
            <Card className="cursor-pointer transition-shadow hover:shadow-md">
              <CardHeader className="pb-2">
                <CardTitle className="text-base">{seq.name}</CardTitle>
              </CardHeader>
              <CardContent className="pt-0">
                {seq.description && (
                  <p className="text-sm text-muted-foreground">{seq.description}</p>
                )}
                <div className="mt-2 flex items-center gap-4 text-sm text-muted-foreground">
                  <span>{seq.step_count} Schritte</span>
                  <span className="font-mono text-xs">{seq.slug}</span>
                </div>
                {seq.steps.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {seq.steps.map((step) => (
                      <span key={step.id} className="rounded bg-muted px-2 py-0.5 text-xs">
                        {step.position}. {step.template_slug}
                        {step.delay_seconds > 0 && ` (+${step.delay_seconds}s)`}
                      </span>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </Link>
        ))}
        {sequences.length === 0 && (
          <p className="text-sm text-muted-foreground">Keine Sequenzen vorhanden.</p>
        )}
      </div>
    </div>
  );
}
