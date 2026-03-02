"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { Bar } from "react-chartjs-2";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { apiFetch } from "@/lib/api";
import { useTenant } from "@/hooks/use-tenant";
import type { CashflowMonth, Client, ServiceType } from "@/types/client";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const RANGE_OPTIONS = [
  { label: "1M", months: 4, future: 3 },
  { label: "6M", months: 6, future: 3 },
  { label: "1J", months: 12, future: 3 },
  { label: "3J", months: 36, future: 3 },
] as const;

const RANGE_DISPLAY: Record<number, string> = {
  4: "1 Monat",
  6: "6 Monate",
  12: "12 Monate",
  36: "3 Jahre",
};

export default function CashflowPage() {
  const { currentTenantId } = useTenant();
  const [data, setData] = useState<CashflowMonth[]>([]);
  const [loading, setLoading] = useState(true);
  const [range, setRange] = useState(12);
  const [future, setFuture] = useState(3);
  const [clientFilter, setClientFilter] = useState("");
  const [serviceTypeFilter, setServiceTypeFilter] = useState("");
  const [clients, setClients] = useState<Client[]>([]);
  const [serviceTypes, setServiceTypes] = useState<ServiceType[]>([]);

  // Fetch filter options
  useEffect(() => {
    if (!currentTenantId) return;
    apiFetch<Client[]>("/api/v1/clients/", { tenantId: currentTenantId })
      .then(setClients)
      .catch(() => setClients([]));
    apiFetch<ServiceType[]>("/api/v1/service-types/", { tenantId: currentTenantId })
      .then(setServiceTypes)
      .catch(() => setServiceTypes([]));
  }, [currentTenantId]);

  const fetchCashflow = useCallback(() => {
    if (!currentTenantId) return;
    setLoading(true);
    const params = new URLSearchParams({
      months: String(range),
      future: String(future),
    });
    if (clientFilter) params.set("client", clientFilter);
    if (serviceTypeFilter) params.set("service_type", serviceTypeFilter);

    apiFetch<CashflowMonth[]>(`/api/v1/clients/cashflow-prognose/?${params}`, {
      tenantId: currentTenantId,
    })
      .then(setData)
      .catch(() => setData([]))
      .finally(() => setLoading(false));
  }, [currentTenantId, range, future, clientFilter, serviceTypeFilter]);

  useEffect(() => {
    fetchCashflow();
  }, [fetchCashflow]);

  const total = data.reduce((sum, m) => sum + Number(m.total), 0);
  const average = data.length > 0 ? total / data.length : 0;

  const chartData = {
    labels: data.map((m) => m.label),
    datasets: [
      {
        label: "Monatlicher Umsatz (EUR)",
        data: data.map((m) => Number(m.total)),
        backgroundColor: "rgba(59, 130, 246, 0.6)",
        borderColor: "rgb(59, 130, 246)",
        borderWidth: 1,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: { display: false },
      title: { display: false },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          callback: (value: string | number) =>
            Number(value).toLocaleString("de-DE", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }),
        },
      },
    },
  };

  if (loading) {
    return <p className="text-muted-foreground">Laden...</p>;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold tracking-tight">Cashflow-Prognose</h1>

      {/* Zeitraum-Buttons + Filter */}
      <div className="flex flex-wrap items-end gap-4">
        <div className="space-y-1">
          <span className="text-sm text-muted-foreground">Zeitraum</span>
          <div className="flex gap-1">
            {RANGE_OPTIONS.map((opt) => (
              <Button
                key={opt.label}
                variant={range === opt.months ? "default" : "outline"}
                size="sm"
                onClick={() => { setRange(opt.months); setFuture(opt.future); }}
              >
                {opt.label}
              </Button>
            ))}
          </div>
        </div>

        <div className="space-y-1">
          <span className="text-sm text-muted-foreground">Mandant</span>
          <select
            className="h-9 rounded-md border border-input bg-background px-3 text-sm"
            value={clientFilter}
            onChange={(e) => setClientFilter(e.target.value)}
          >
            <option value="">Alle</option>
            {clients.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>

        <div className="space-y-1">
          <span className="text-sm text-muted-foreground">Service-Art</span>
          <select
            className="h-9 rounded-md border border-input bg-background px-3 text-sm"
            value={serviceTypeFilter}
            onChange={(e) => setServiceTypeFilter(e.target.value)}
          >
            <option value="">Alle</option>
            {serviceTypes.map((st) => (
              <option key={st.id} value={st.id}>{st.name}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm text-muted-foreground">Gesamt ({RANGE_DISPLAY[range] || `${range} Monate`})</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">
              {total.toLocaleString("de-DE", { style: "currency", currency: "EUR" })}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm text-muted-foreground">Durchschnitt / Monat</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">
              {average.toLocaleString("de-DE", { style: "currency", currency: "EUR" })}
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Monatliche Prognose</CardTitle>
        </CardHeader>
        <CardContent>
          <Bar data={chartData} options={chartOptions} />
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          <table className="w-full">
            <thead>
              <tr className="border-b text-left text-sm text-muted-foreground">
                <th className="p-4">Monat</th>
                <th className="p-4 text-right">Umsatz</th>
              </tr>
            </thead>
            <tbody>
              {data.map((m) => (
                <tr key={m.month} className="border-b last:border-0 hover:bg-muted/50">
                  <td className="p-4 text-sm">{m.label}</td>
                  <td className="p-4 text-sm font-mono text-right">
                    {Number(m.total).toLocaleString("de-DE", { style: "currency", currency: "EUR" })}
                  </td>
                </tr>
              ))}
              {data.length === 0 && (
                <tr>
                  <td colSpan={2} className="p-4 text-center text-sm text-muted-foreground">
                    Keine Daten vorhanden.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
