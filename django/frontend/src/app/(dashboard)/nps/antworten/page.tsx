"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";
import { useTenant } from "@/hooks/use-tenant";
import type { NPSResponse } from "@/types/nps";

const SEGMENT_LABELS: Record<string, string> = {
  promoter: "Promoter",
  passive: "Passive",
  detractor: "Detractor",
};

const SEGMENT_STYLES: Record<string, string> = {
  promoter: "bg-green-100 text-green-800",
  passive: "bg-yellow-100 text-yellow-800",
  detractor: "bg-red-100 text-red-800",
};

export default function AntwortenPage() {
  const { currentTenantId } = useTenant();
  const [responses, setResponses] = useState<NPSResponse[]>([]);
  const [filter, setFilter] = useState("");

  const fetchResponses = useCallback(async () => {
    if (!currentTenantId) return;
    const params = filter ? `?segment=${filter}` : "";
    try {
      const data = await apiFetch<NPSResponse[]>(`/api/v1/nps/responses/${params}`, { tenantId: currentTenantId });
      setResponses(data);
    } catch {
      /* ignore */
    }
  }, [currentTenantId, filter]);

  useEffect(() => {
    fetchResponses();
  }, [fetchResponses]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">NPS-Antworten</h1>
          <p className="text-muted-foreground">Alle eingegangenen NPS-Bewertungen.</p>
        </div>
      </div>

      {/* Filter */}
      <div className="flex gap-2">
        {[
          { value: "", label: "Alle" },
          { value: "promoter", label: "Promoter (9-10)" },
          { value: "passive", label: "Passive (7-8)" },
          { value: "detractor", label: "Detractor (0-6)" },
        ].map((opt) => (
          <button
            key={opt.value}
            onClick={() => setFilter(opt.value)}
            className={`px-3 py-1.5 rounded-md text-sm transition-colors ${
              filter === opt.value
                ? "bg-primary text-primary-foreground"
                : "bg-muted text-muted-foreground hover:bg-muted/80"
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      <Card>
        <CardContent className="pt-6">
          {responses.length === 0 ? (
            <p className="text-sm text-muted-foreground">Noch keine Antworten vorhanden.</p>
          ) : (
            <div className="space-y-0 divide-y">
              {responses.map((r) => (
                <div key={r.id} className="py-4 first:pt-0 last:pb-0">
                  <div className="flex items-start gap-3">
                    <div className="flex items-center justify-center w-10 h-10 rounded-full bg-muted font-bold text-lg">
                      {r.score}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <Link
                          href={`/mandanten/${r.client_slug}`}
                          className="font-medium text-sm hover:underline"
                        >
                          {r.client_name}
                        </Link>
                        <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${SEGMENT_STYLES[r.segment]}`}>
                          {SEGMENT_LABELS[r.segment]}
                        </span>
                        <span className="text-xs text-muted-foreground ml-auto">
                          {new Date(r.responded_at).toLocaleDateString("de-DE", {
                            day: "2-digit",
                            month: "2-digit",
                            year: "numeric",
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </span>
                      </div>
                      {r.comment && (
                        <p className="text-sm text-muted-foreground mt-1">{r.comment}</p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
