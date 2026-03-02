"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";
import { useTenant } from "@/hooks/use-tenant";
import type { NPSDashboard, NPSTrendPoint, NPSResponse } from "@/types/nps";

const SEGMENT_COLORS = {
  promoter: "#22c55e",
  passive: "#eab308",
  detractor: "#ef4444",
};

const SEGMENT_LABELS: Record<string, string> = {
  promoter: "Promoter",
  passive: "Passive",
  detractor: "Detractor",
};

function scoreColor(score: number): string {
  if (score > 50) return "text-green-500";
  if (score > 0) return "text-yellow-500";
  return "text-red-500";
}

function ScoreBadge({ score }: { score: number }) {
  let bg = "bg-green-100 text-green-800";
  if (score <= 6) bg = "bg-red-100 text-red-800";
  else if (score <= 8) bg = "bg-yellow-100 text-yellow-800";
  return <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${bg}`}>{score}</span>;
}

function DonutChart({ promoters, passives, detractors, total }: { promoters: number; passives: number; detractors: number; total: number }) {
  if (total === 0) {
    return <div className="flex items-center justify-center h-48 text-muted-foreground text-sm">Noch keine Daten</div>;
  }

  const segments = [
    { label: "Promoter", value: promoters, color: SEGMENT_COLORS.promoter },
    { label: "Passive", value: passives, color: SEGMENT_COLORS.passive },
    { label: "Detractor", value: detractors, color: SEGMENT_COLORS.detractor },
  ].filter((s) => s.value > 0);

  // SVG donut chart
  const size = 160;
  const strokeWidth = 30;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;

  let offset = 0;
  const arcs = segments.map((seg) => {
    const pct = seg.value / total;
    const dashArray = `${pct * circumference} ${circumference}`;
    const dashOffset = -offset * circumference;
    offset += pct;
    return { ...seg, dashArray, dashOffset };
  });

  return (
    <div className="flex items-center gap-6">
      <svg width={size} height={size} className="shrink-0">
        {arcs.map((arc) => (
          <circle
            key={arc.label}
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={arc.color}
            strokeWidth={strokeWidth}
            strokeDasharray={arc.dashArray}
            strokeDashoffset={arc.dashOffset}
            transform={`rotate(-90 ${size / 2} ${size / 2})`}
          />
        ))}
      </svg>
      <div className="space-y-2 text-sm">
        {segments.map((seg) => (
          <div key={seg.label} className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: seg.color }} />
            <span>{seg.label}: {seg.value} ({Math.round((seg.value / total) * 100)}%)</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function TrendChart({ data }: { data: NPSTrendPoint[] }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || data.length === 0) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const w = rect.width;
    const h = rect.height;
    const padding = { top: 20, right: 20, bottom: 30, left: 40 };
    const chartW = w - padding.left - padding.right;
    const chartH = h - padding.top - padding.bottom;

    ctx.clearRect(0, 0, w, h);

    // Y axis range: -100 to +100
    const yMin = -100;
    const yMax = 100;
    const yRange = yMax - yMin;

    function toX(i: number) {
      return padding.left + (i / Math.max(data.length - 1, 1)) * chartW;
    }
    function toY(val: number) {
      return padding.top + (1 - (val - yMin) / yRange) * chartH;
    }

    // Grid lines
    ctx.strokeStyle = "#e5e7eb";
    ctx.lineWidth = 1;
    for (const val of [-100, -50, 0, 50, 100]) {
      const y = toY(val);
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(w - padding.right, y);
      ctx.stroke();

      ctx.fillStyle = "#9ca3af";
      ctx.font = "11px sans-serif";
      ctx.textAlign = "right";
      ctx.fillText(String(val), padding.left - 6, y + 4);
    }

    // Zero line emphasized
    ctx.strokeStyle = "#d1d5db";
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(padding.left, toY(0));
    ctx.lineTo(w - padding.right, toY(0));
    ctx.stroke();

    // Line
    ctx.strokeStyle = "#3b82f6";
    ctx.lineWidth = 2;
    ctx.beginPath();
    data.forEach((point, i) => {
      const x = toX(i);
      const y = toY(point.score);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    // Dots
    data.forEach((point, i) => {
      const x = toX(i);
      const y = toY(point.score);
      ctx.fillStyle = point.score >= 0 ? "#22c55e" : "#ef4444";
      ctx.beginPath();
      ctx.arc(x, y, 4, 0, Math.PI * 2);
      ctx.fill();
    });

    // X axis labels
    ctx.fillStyle = "#9ca3af";
    ctx.font = "10px sans-serif";
    ctx.textAlign = "center";
    data.forEach((point, i) => {
      if (data.length <= 6 || i % 2 === 0) {
        ctx.fillText(point.month.slice(5), toX(i), h - 5);
      }
    });
  }, [data]);

  if (data.length === 0) {
    return <div className="flex items-center justify-center h-48 text-muted-foreground text-sm">Noch keine Daten</div>;
  }

  return <canvas ref={canvasRef} className="w-full h-48" />;
}

export default function NPSPage() {
  const { currentTenantId } = useTenant();
  const [dashboard, setDashboard] = useState<NPSDashboard | null>(null);
  const [trend, setTrend] = useState<NPSTrendPoint[]>([]);
  const [recentResponses, setRecentResponses] = useState<NPSResponse[]>([]);

  const fetchData = useCallback(async () => {
    if (!currentTenantId) return;
    try {
      const [dashData, trendData, responsesData] = await Promise.all([
        apiFetch<NPSDashboard>("/api/v1/nps/dashboard/", { tenantId: currentTenantId }),
        apiFetch<NPSTrendPoint[]>("/api/v1/nps/dashboard/trend/", { tenantId: currentTenantId }),
        apiFetch<NPSResponse[]>("/api/v1/nps/responses/", { tenantId: currentTenantId }),
      ]);
      setDashboard(dashData);
      setTrend(trendData);
      setRecentResponses(responsesData.slice(0, 10));
    } catch {
      /* ignore */
    }
  }, [currentTenantId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">NPS & Feedback</h1>
        <p className="text-muted-foreground">Net Promoter Score Uebersicht und Auswertung.</p>
      </div>

      {/* Score Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">NPS Score</CardTitle>
          </CardHeader>
          <CardContent>
            <p className={`text-4xl font-bold ${dashboard ? scoreColor(dashboard.score) : ""}`}>
              {dashboard ? dashboard.score : "—"}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Antworten</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold">{dashboard?.total ?? "—"}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Response Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold">{dashboard ? `${dashboard.response_rate}%` : "—"}</p>
            <p className="text-xs text-muted-foreground mt-1">
              {dashboard ? `${dashboard.surveys_responded} von ${dashboard.surveys_sent} gesendet` : ""}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Segment-Verteilung</CardTitle>
          </CardHeader>
          <CardContent>
            {dashboard ? (
              <div className="text-sm space-y-1">
                <div className="flex justify-between"><span className="text-green-600">Promoter</span><span>{dashboard.promoters} ({dashboard.promoter_pct}%)</span></div>
                <div className="flex justify-between"><span className="text-yellow-600">Passive</span><span>{dashboard.passives} ({dashboard.passive_pct}%)</span></div>
                <div className="flex justify-between"><span className="text-red-600">Detractor</span><span>{dashboard.detractors} ({dashboard.detractor_pct}%)</span></div>
              </div>
            ) : <span className="text-muted-foreground">—</span>}
          </CardContent>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Segment-Verteilung</CardTitle>
          </CardHeader>
          <CardContent>
            {dashboard ? (
              <DonutChart
                promoters={dashboard.promoters}
                passives={dashboard.passives}
                detractors={dashboard.detractors}
                total={dashboard.total}
              />
            ) : <div className="h-48 flex items-center justify-center text-muted-foreground">Laden...</div>}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>NPS Trend (12 Monate)</CardTitle>
          </CardHeader>
          <CardContent>
            <TrendChart data={trend} />
          </CardContent>
        </Card>
      </div>

      {/* Recent Responses */}
      <Card>
        <CardHeader>
          <CardTitle>Letzte Antworten</CardTitle>
        </CardHeader>
        <CardContent>
          {recentResponses.length === 0 ? (
            <p className="text-sm text-muted-foreground">Noch keine Antworten vorhanden.</p>
          ) : (
            <div className="space-y-3">
              {recentResponses.map((r) => (
                <div key={r.id} className="flex items-start gap-3 py-2 border-b last:border-0">
                  <ScoreBadge score={r.score} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 text-sm">
                      <span className="font-medium">{r.client_name}</span>
                      <span className="text-muted-foreground">
                        {SEGMENT_LABELS[r.segment]}
                      </span>
                      <span className="text-muted-foreground text-xs ml-auto">
                        {new Date(r.responded_at).toLocaleDateString("de-DE")}
                      </span>
                    </div>
                    {r.comment && (
                      <p className="text-sm text-muted-foreground mt-1 truncate">{r.comment}</p>
                    )}
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
