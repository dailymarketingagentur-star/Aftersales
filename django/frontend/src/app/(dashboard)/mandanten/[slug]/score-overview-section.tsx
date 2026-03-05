"use client";

import { useCallback, useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";
import type { HealthScoreAssessment, ChurnWarningAssessment } from "@/types/client";

interface ScoreOverviewSectionProps {
  slug: string;
  tenantId: string;
  healthScore: number;
  churnWarningCount: number;
  lastHealthAt: string | null;
  lastChurnAt: string | null;
}

function healthStatusLabel(score: number): string {
  if (score >= 30) return "Exzellent";
  if (score >= 24) return "Gut";
  if (score >= 18) return "Neutral";
  if (score >= 12) return "Risiko";
  return "Kritisch";
}

function healthStatusColor(score: number): string {
  if (score >= 24) return "text-green-600";
  if (score >= 18) return "text-yellow-600";
  return "text-red-600";
}

function churnColor(count: number): string {
  if (count <= 1) return "text-green-600";
  if (count <= 3) return "text-yellow-600";
  return "text-red-600";
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "Noch nicht durchgeführt";
  return new Date(dateStr).toLocaleDateString("de-DE", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

const HEALTH_FIELD_LABELS: Record<string, string> = {
  result_satisfaction: "Ergebnis-Zufriedenheit",
  communication: "Kommunikation",
  engagement: "Engagement",
  relationship: "Beziehungsqualität",
  payment_behavior: "Zahlungsverhalten",
  growth_potential: "Wachstumspotenzial",
  referral_readiness: "Empfehlungsbereitschaft",
};

const CHURN_FIELD_LABELS: Record<string, string> = {
  slower_responses: "Langsamere Antworten",
  missed_checkins: "Verpasste Check-ins",
  decreased_usage: "Weniger Nutzung",
  contract_inquiries: "Vertragsfragen",
  new_decision_maker: "Neuer Entscheider",
  budget_cuts_mentioned: "Budgetkürzungen",
  competitor_mentions: "Wettbewerber erwähnt",
  critical_feedback: "Kritisches Feedback",
  delayed_payments: "Verspätete Zahlungen",
  fewer_approvals: "Weniger Freigaben",
};

export function ScoreOverviewSection({
  slug,
  tenantId,
  healthScore,
  churnWarningCount,
  lastHealthAt,
  lastChurnAt,
}: ScoreOverviewSectionProps) {
  const [healthHistory, setHealthHistory] = useState<HealthScoreAssessment[]>([]);
  const [churnHistory, setChurnHistory] = useState<ChurnWarningAssessment[]>([]);
  const [showHealthHistory, setShowHealthHistory] = useState(false);
  const [showChurnHistory, setShowChurnHistory] = useState(false);

  const fetchHistories = useCallback(async () => {
    try {
      const [h, c] = await Promise.all([
        apiFetch<HealthScoreAssessment[]>(`/api/v1/clients/${slug}/health-assessments/`, { tenantId }),
        apiFetch<ChurnWarningAssessment[]>(`/api/v1/clients/${slug}/churn-assessments/`, { tenantId }),
      ]);
      setHealthHistory(h);
      setChurnHistory(c);
    } catch {
      /* ignore */
    }
  }, [slug, tenantId]);

  useEffect(() => {
    fetchHistories();
  }, [fetchHistories]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Score-Übersicht</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          {/* Health Score */}
          <div className="space-y-2">
            <div className="flex items-baseline justify-between">
              <span className="text-sm font-medium text-muted-foreground">Health Score</span>
              <span className={`text-2xl font-bold ${healthStatusColor(healthScore)}`}>
                {healthScore}/35
              </span>
            </div>
            <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${
              healthScore >= 24 ? "bg-green-100 text-green-800" :
              healthScore >= 18 ? "bg-yellow-100 text-yellow-800" :
              "bg-red-100 text-red-800"
            }`}>
              {healthStatusLabel(healthScore)}
            </span>
            <p className="text-xs text-muted-foreground">
              Letztes Assessment: {formatDate(lastHealthAt)}
            </p>

            {healthHistory.length > 0 && (
              <button
                type="button"
                onClick={() => setShowHealthHistory(!showHealthHistory)}
                className="text-xs text-primary hover:underline"
              >
                {showHealthHistory ? "Historie ausblenden" : `Historie anzeigen (${healthHistory.length})`}
              </button>
            )}

            {showHealthHistory && healthHistory.length > 0 && (
              <div className="space-y-2 pt-1">
                {healthHistory.slice(0, 5).map((a) => (
                  <div key={a.id} className="rounded-md border p-2 text-xs">
                    <div className="flex items-center justify-between">
                      <span className={`font-semibold ${healthStatusColor(a.total_score)}`}>
                        {a.total_score}/35 — {a.status_label}
                      </span>
                      <span className="text-muted-foreground">
                        {new Date(a.created_at).toLocaleDateString("de-DE")}
                      </span>
                    </div>
                    <div className="mt-1 grid grid-cols-2 gap-x-3 gap-y-0.5 text-muted-foreground">
                      {Object.entries(HEALTH_FIELD_LABELS).map(([field, label]) => (
                        <span key={field}>
                          {label}: <strong className="text-foreground">{a[field as keyof HealthScoreAssessment] as number}</strong>/5
                        </span>
                      ))}
                    </div>
                    {a.notes && <p className="mt-1 italic">{a.notes}</p>}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Churn Warnings */}
          <div className="space-y-2">
            <div className="flex items-baseline justify-between">
              <span className="text-sm font-medium text-muted-foreground">Churn-Warnsignale</span>
              <span className={`text-2xl font-bold ${churnColor(churnWarningCount)}`}>
                {churnWarningCount}/10
              </span>
            </div>
            <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${
              churnWarningCount <= 1 ? "bg-green-100 text-green-800" :
              churnWarningCount <= 3 ? "bg-yellow-100 text-yellow-800" :
              "bg-red-100 text-red-800"
            }`}>
              {churnWarningCount <= 1 ? "Niedrig" : churnWarningCount <= 3 ? "Mittel" : "Hoch"}
            </span>
            <p className="text-xs text-muted-foreground">
              Letztes Assessment: {formatDate(lastChurnAt)}
            </p>

            {churnHistory.length > 0 && (
              <button
                type="button"
                onClick={() => setShowChurnHistory(!showChurnHistory)}
                className="text-xs text-primary hover:underline"
              >
                {showChurnHistory ? "Historie ausblenden" : `Historie anzeigen (${churnHistory.length})`}
              </button>
            )}

            {showChurnHistory && churnHistory.length > 0 && (
              <div className="space-y-2 pt-1">
                {churnHistory.slice(0, 5).map((a) => (
                  <div key={a.id} className="rounded-md border p-2 text-xs">
                    <div className="flex items-center justify-between">
                      <span className={`font-semibold ${churnColor(a.active_signals)}`}>
                        {a.active_signals}/10 Warnsignale
                      </span>
                      <span className="text-muted-foreground">
                        {new Date(a.created_at).toLocaleDateString("de-DE")}
                      </span>
                    </div>
                    <div className="mt-1 flex flex-wrap gap-1">
                      {Object.entries(CHURN_FIELD_LABELS).map(([field, label]) => (
                        a[field as keyof ChurnWarningAssessment] === true && (
                          <span key={field} className="rounded bg-red-100 px-1.5 py-0.5 text-red-700">
                            {label}
                          </span>
                        )
                      ))}
                      {a.active_signals === 0 && (
                        <span className="text-muted-foreground">Keine Warnsignale</span>
                      )}
                    </div>
                    {a.notes && <p className="mt-1 italic text-muted-foreground">{a.notes}</p>}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
