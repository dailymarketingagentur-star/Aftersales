"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";
import { useTenant } from "@/hooks/use-tenant";
import type { TestimonialRequest } from "@/types/nps";

const STATUS_LABELS: Record<string, string> = {
  requested: "Angefragt",
  accepted: "Zugesagt",
  received: "Erhalten",
  published: "Veroeffentlicht",
  declined: "Abgelehnt",
};

const STATUS_STYLES: Record<string, string> = {
  requested: "bg-blue-100 text-blue-800",
  accepted: "bg-yellow-100 text-yellow-800",
  received: "bg-green-100 text-green-800",
  published: "bg-emerald-100 text-emerald-800",
  declined: "bg-gray-100 text-gray-600",
};

const TYPE_LABELS: Record<string, string> = {
  google_review: "Google-Bewertung",
  video: "Video",
  written: "Schriftlich",
  draft_approve: "Entwurf",
};

const NEXT_STATUS: Record<string, string> = {
  requested: "accepted",
  accepted: "received",
  received: "published",
};

export default function TestimonialsPage() {
  const { currentTenantId } = useTenant();
  const [testimonials, setTestimonials] = useState<TestimonialRequest[]>([]);
  const [filter, setFilter] = useState("");

  const fetchTestimonials = useCallback(async () => {
    if (!currentTenantId) return;
    const params = filter ? `?status=${filter}` : "";
    try {
      const data = await apiFetch<TestimonialRequest[]>(`/api/v1/nps/testimonials/${params}`, { tenantId: currentTenantId });
      setTestimonials(data);
    } catch {
      /* ignore */
    }
  }, [currentTenantId, filter]);

  useEffect(() => {
    fetchTestimonials();
  }, [fetchTestimonials]);

  async function advanceStatus(id: string, currentStatus: string) {
    if (!currentTenantId) return;
    const next = NEXT_STATUS[currentStatus];
    if (!next) return;
    try {
      await apiFetch(`/api/v1/nps/testimonials/${id}/`, {
        method: "PATCH",
        body: JSON.stringify({ status: next }),
        tenantId: currentTenantId,
      });
      fetchTestimonials();
    } catch {
      /* ignore */
    }
  }

  async function declineTestimonial(id: string) {
    if (!currentTenantId) return;
    try {
      await apiFetch(`/api/v1/nps/testimonials/${id}/`, {
        method: "PATCH",
        body: JSON.stringify({ status: "declined" }),
        tenantId: currentTenantId,
      });
      fetchTestimonials();
    } catch {
      /* ignore */
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Testimonials</h1>
        <p className="text-muted-foreground">Testimonial-Anfragen und deren Status verwalten.</p>
      </div>

      {/* Filter */}
      <div className="flex gap-2 flex-wrap">
        {[
          { value: "", label: "Alle" },
          { value: "requested", label: "Angefragt" },
          { value: "accepted", label: "Zugesagt" },
          { value: "received", label: "Erhalten" },
          { value: "published", label: "Veroeffentlicht" },
          { value: "declined", label: "Abgelehnt" },
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
          {testimonials.length === 0 ? (
            <p className="text-sm text-muted-foreground">Noch keine Testimonial-Anfragen vorhanden.</p>
          ) : (
            <div className="space-y-0 divide-y">
              {testimonials.map((t) => (
                <div key={t.id} className="py-4 first:pt-0 last:pb-0">
                  <div className="flex items-start gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <Link href={`/mandanten/${t.client_slug}`} className="font-medium text-sm hover:underline">
                          {t.client_name}
                        </Link>
                        <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLES[t.status]}`}>
                          {STATUS_LABELS[t.status]}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {TYPE_LABELS[t.request_type]}
                        </span>
                        <span className="text-xs text-muted-foreground ml-auto">
                          {new Date(t.requested_at).toLocaleDateString("de-DE")}
                        </span>
                      </div>
                      {t.content && (
                        <p className="text-sm text-muted-foreground mt-1">{t.content}</p>
                      )}
                      {t.platform_url && (
                        <a href={t.platform_url} target="_blank" rel="noopener noreferrer" className="text-xs text-primary hover:underline mt-1 inline-block">
                          Zur Bewertung
                        </a>
                      )}
                      {t.notes && (
                        <p className="text-xs text-muted-foreground mt-1">Notiz: {t.notes}</p>
                      )}
                    </div>
                    <div className="flex gap-1 shrink-0">
                      {NEXT_STATUS[t.status] && (
                        <Button variant="outline" size="sm" onClick={() => advanceStatus(t.id, t.status)}>
                          {STATUS_LABELS[NEXT_STATUS[t.status]]}
                        </Button>
                      )}
                      {t.status !== "declined" && t.status !== "published" && (
                        <Button variant="ghost" size="sm" onClick={() => declineTestimonial(t.id)}>
                          Ablehnen
                        </Button>
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
