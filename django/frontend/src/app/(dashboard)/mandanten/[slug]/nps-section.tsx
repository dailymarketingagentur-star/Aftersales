"use client";

import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";
import type { ClientNPSData, NPSResponse, TestimonialRequest } from "@/types/nps";

interface NPSSectionProps {
  slug: string;
  tenantId: string;
  clientId: string;
}

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

const TESTIMONIAL_STATUS: Record<string, string> = {
  requested: "Angefragt",
  accepted: "Zugesagt",
  received: "Erhalten",
  published: "Veroeffentlicht",
  declined: "Abgelehnt",
};

export function NPSSection({ slug, tenantId, clientId }: NPSSectionProps) {
  const [data, setData] = useState<ClientNPSData | null>(null);
  const [sending, setSending] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [sendResult, setSendResult] = useState<{ ok: boolean; message: string } | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const result = await apiFetch<ClientNPSData>(`/api/v1/nps/clients/${slug}/`, { tenantId });
      setData(result);
    } catch {
      /* ignore */
    }
  }, [slug, tenantId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  async function handleSendSurvey() {
    setSending(true);
    setSendResult(null);
    try {
      await apiFetch("/api/v1/nps/surveys/send/", {
        method: "POST",
        body: JSON.stringify({ client_id: clientId }),
        tenantId,
      });
      setSendResult({ ok: true, message: "NPS-Umfrage wurde gesendet." });
      setShowConfirm(false);
      fetchData();
    } catch (err) {
      setSendResult({ ok: false, message: err instanceof Error ? err.message : "Fehler beim Senden." });
    } finally {
      setSending(false);
    }
  }

  const latestResponse = data?.responses?.[0];
  const hasPending = data?.surveys?.some((s) => s.status === "pending");

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>NPS & Feedback</CardTitle>
        <div className="flex items-center gap-2">
          {hasPending && (
            <span className="text-xs text-muted-foreground">Ausstehende Umfrage</span>
          )}
          {!showConfirm ? (
            <Button variant="outline" size="sm" onClick={() => setShowConfirm(true)}>
              NPS senden
            </Button>
          ) : (
            <div className="flex items-center gap-2">
              <span className="text-sm">NPS-Umfrage senden?</span>
              <Button size="sm" onClick={handleSendSurvey} disabled={sending}>
                {sending ? "..." : "Senden"}
              </Button>
              <Button variant="ghost" size="sm" onClick={() => setShowConfirm(false)}>
                Abbrechen
              </Button>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {sendResult && (
          <p className={`text-sm mb-3 ${sendResult.ok ? "text-green-600" : "text-destructive"}`}>
            {sendResult.message}
          </p>
        )}

        {!data || (data.responses.length === 0 && data.testimonials.length === 0) ? (
          <p className="text-sm text-muted-foreground">Noch kein NPS-Feedback vorhanden.</p>
        ) : (
          <div className="space-y-4">
            {/* Latest score */}
            {latestResponse && (
              <div className="flex items-center gap-3">
                <div className="flex items-center justify-center w-12 h-12 rounded-full bg-muted font-bold text-xl">
                  {latestResponse.score}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${SEGMENT_STYLES[latestResponse.segment]}`}>
                      {SEGMENT_LABELS[latestResponse.segment]}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {new Date(latestResponse.responded_at).toLocaleDateString("de-DE")}
                    </span>
                  </div>
                  {latestResponse.comment && (
                    <p className="text-sm text-muted-foreground mt-1">{latestResponse.comment}</p>
                  )}
                </div>
              </div>
            )}

            {/* Score history */}
            {data.responses.length > 1 && (
              <div>
                <p className="text-xs font-medium text-muted-foreground mb-2">Verlauf</p>
                <div className="flex gap-2 flex-wrap">
                  {data.responses.map((r) => (
                    <div
                      key={r.id}
                      className={`flex items-center gap-1 rounded-full px-2 py-0.5 text-xs ${SEGMENT_STYLES[r.segment]}`}
                      title={new Date(r.responded_at).toLocaleDateString("de-DE")}
                    >
                      {r.score}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Testimonials */}
            {data.testimonials.length > 0 && (
              <div>
                <p className="text-xs font-medium text-muted-foreground mb-2">Testimonials</p>
                <div className="space-y-2">
                  {data.testimonials.map((t) => (
                    <div key={t.id} className="flex items-center gap-2 text-sm">
                      <span className="text-muted-foreground">{TESTIMONIAL_STATUS[t.status]}</span>
                      <span className="text-xs text-muted-foreground">
                        ({new Date(t.requested_at).toLocaleDateString("de-DE")})
                      </span>
                      {t.content && <span className="text-xs truncate max-w-[200px]">{t.content}</span>}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
