"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { apiFetch } from "@/lib/api";
import { useTenant } from "@/hooks/use-tenant";
import { TimelineSection } from "../timeline-section";

export default function AktivitaetenPage() {
  const params = useParams();
  const slug = params.slug as string;
  const { currentTenantId } = useTenant();
  const [clientName, setClientName] = useState("");

  useEffect(() => {
    if (!currentTenantId || !slug) return;
    apiFetch<{ name: string }>(`/api/v1/clients/${slug}/`, { tenantId: currentTenantId })
      .then((data) => setClientName(data.name))
      .catch(() => {});
  }, [currentTenantId, slug]);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href={`/mandanten/${slug}`}>
          <Button variant="outline" size="sm">&larr; Zurück</Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Aktivitäten</h1>
          {clientName && (
            <p className="text-muted-foreground">{clientName}</p>
          )}
        </div>
      </div>

      {currentTenantId && (
        <TimelineSection slug={slug} tenantId={currentTenantId} />
      )}
    </div>
  );
}
