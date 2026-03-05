"use client";

import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { apiFetch } from "@/lib/api";
import type { ClientNPSData, NPSResponse, TestimonialRequest } from "@/types/nps";

interface NPSSectionProps {
  slug: string;
  tenantId: string;
  clientId: string;
}

interface PreviewData {
  subject: string;
  body_html: string;
  default_email: string;
  available_emails: { email: string; label: string }[];
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

  // Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [preview, setPreview] = useState<PreviewData | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [selectedEmail, setSelectedEmail] = useState("");
  const [sending, setSending] = useState(false);
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

  async function handleOpenModal() {
    setModalOpen(true);
    setSendResult(null);
    setPreview(null);
    setPreviewLoading(true);
    try {
      const result = await apiFetch<PreviewData>("/api/v1/nps/surveys/preview/", {
        method: "POST",
        body: JSON.stringify({ client_id: clientId }),
        tenantId,
      });
      setPreview(result);
      setSelectedEmail(result.default_email);
    } catch (err) {
      setSendResult({
        ok: false,
        message: err instanceof Error ? err.message : "Vorschau konnte nicht geladen werden.",
      });
    } finally {
      setPreviewLoading(false);
    }
  }

  async function handleSendSurvey() {
    setSending(true);
    setSendResult(null);
    try {
      await apiFetch("/api/v1/nps/surveys/send/", {
        method: "POST",
        body: JSON.stringify({
          client_id: clientId,
          recipient_email: selectedEmail || undefined,
        }),
        tenantId,
      });
      setSendResult({ ok: true, message: "NPS-Umfrage wurde erfolgreich gesendet." });
      fetchData();
      // Schließe Modal nach kurzem Delay damit Erfolg sichtbar ist
      setTimeout(() => setModalOpen(false), 1500);
    } catch (err) {
      setSendResult({
        ok: false,
        message: err instanceof Error ? err.message : "Fehler beim Senden.",
      });
    } finally {
      setSending(false);
    }
  }

  const latestResponse = data?.responses?.[0];
  const hasPending = data?.surveys?.some((s) => s.status === "pending");

  return (
    <>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>NPS & Feedback</CardTitle>
          <div className="flex items-center gap-2">
            {hasPending && (
              <span className="text-xs text-muted-foreground">Ausstehende Umfrage</span>
            )}
            <Button variant="outline" size="sm" onClick={handleOpenModal}>
              NPS senden
            </Button>
          </div>
        </CardHeader>
        <CardContent>
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

      {/* NPS Senden Modal */}
      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>NPS-Umfrage senden</DialogTitle>
          </DialogHeader>

          {previewLoading && (
            <p className="text-sm text-muted-foreground py-4">Vorschau wird geladen...</p>
          )}

          {sendResult && !sendResult.ok && (
            <p className="text-sm text-destructive">{sendResult.message}</p>
          )}

          {sendResult?.ok && (
            <p className="text-sm text-green-600 font-medium">{sendResult.message}</p>
          )}

          {preview && !sendResult?.ok && (
            <div className="space-y-4">
              {/* E-Mail-Adresse Auswahl */}
              <div className="space-y-1.5">
                <label className="text-sm font-medium" htmlFor="nps-email-select">
                  Empfänger
                </label>
                {preview.available_emails.length > 1 ? (
                  <select
                    id="nps-email-select"
                    className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                    value={selectedEmail}
                    onChange={(e) => setSelectedEmail(e.target.value)}
                  >
                    {preview.available_emails.map((entry) => (
                      <option key={entry.email} value={entry.email}>
                        {entry.email} ({entry.label})
                      </option>
                    ))}
                  </select>
                ) : (
                  <p className="text-sm">{selectedEmail || "Keine E-Mail-Adresse vorhanden"}</p>
                )}
              </div>

              {/* Betreff */}
              <div className="space-y-1.5">
                <p className="text-sm font-medium">Betreff</p>
                <p className="text-sm bg-muted rounded-md px-3 py-2">{preview.subject}</p>
              </div>

              {/* E-Mail-Vorschau */}
              <div className="space-y-1.5">
                <p className="text-sm font-medium">Vorschau</p>
                <div
                  className="border rounded-md p-4 text-sm bg-white max-h-[300px] overflow-y-auto"
                  dangerouslySetInnerHTML={{ __html: preview.body_html }}
                />
              </div>
            </div>
          )}

          <DialogFooter>
            <Button variant="ghost" onClick={() => setModalOpen(false)}>
              Abbrechen
            </Button>
            <Button
              onClick={handleSendSurvey}
              disabled={sending || !preview || !selectedEmail || !!sendResult?.ok}
            >
              {sending ? "Wird gesendet..." : "Senden"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
