"use client";

import { Fragment, useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";
import { useTenant } from "@/hooks/use-tenant";
import type { Service, ServiceType } from "@/types/client";

const STATUS_LABELS: Record<string, string> = {
  active: "Aktiv",
  paused: "Pausiert",
  completed: "Abgeschlossen",
  cancelled: "Storniert",
};

const STATUS_COLORS: Record<string, string> = {
  active: "bg-green-100 text-green-800",
  paused: "bg-yellow-100 text-yellow-800",
  completed: "bg-gray-100 text-gray-800",
  cancelled: "bg-red-100 text-red-800",
};

const EMPTY_FORM = {
  name: "",
  service_type: "",
  monthly_budget: "",
  status: "active",
  start_date: "",
  end_date: "",
  description: "",
  link: "",
};

export default function ServicesPage() {
  const params = useParams();
  const slug = params.slug as string;
  const { currentTenantId } = useTenant();

  const [services, setServices] = useState<Service[]>([]);
  const [serviceTypes, setServiceTypes] = useState<ServiceType[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editingService, setEditingService] = useState<Service | null>(null);
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const [form, setForm] = useState({ ...EMPTY_FORM });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchServices = useCallback(async () => {
    if (!currentTenantId || !slug) return;
    try {
      const data = await apiFetch<Service[]>(`/api/v1/clients/${slug}/services/`, { tenantId: currentTenantId });
      setServices(data);
    } catch {
      /* ignore */
    }
  }, [currentTenantId, slug]);

  const fetchServiceTypes = useCallback(async () => {
    if (!currentTenantId) return;
    try {
      const data = await apiFetch<ServiceType[]>("/api/v1/service-types/", { tenantId: currentTenantId });
      setServiceTypes(data);
    } catch {
      /* ignore */
    }
  }, [currentTenantId]);

  useEffect(() => {
    fetchServices();
    fetchServiceTypes();
  }, [fetchServices, fetchServiceTypes]);

  function startEdit(service: Service) {
    setEditingService(service);
    setForm({
      name: service.name,
      service_type: service.service_type,
      monthly_budget: service.monthly_budget,
      status: service.status,
      start_date: service.start_date || "",
      end_date: service.end_date || "",
      description: service.description,
      link: service.link,
    });
    setShowForm(true);
    setError("");
  }

  function cancelForm() {
    setShowForm(false);
    setEditingService(null);
    setForm({ ...EMPTY_FORM });
    setError("");
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!currentTenantId || !slug) return;
    setError("");
    setLoading(true);

    const payload = {
      name: form.name,
      service_type: form.service_type,
      monthly_budget: form.monthly_budget || "0.00",
      status: form.status,
      start_date: form.start_date || null,
      end_date: form.end_date || null,
      description: form.description,
      link: form.link || "",
    };

    try {
      if (editingService) {
        await apiFetch(`/api/v1/clients/${slug}/services/${editingService.id}/`, {
          method: "PATCH",
          body: JSON.stringify(payload),
          tenantId: currentTenantId,
        });
      } else {
        await apiFetch(`/api/v1/clients/${slug}/services/`, {
          method: "POST",
          body: JSON.stringify(payload),
          tenantId: currentTenantId,
        });
      }
      setForm({ ...EMPTY_FORM });
      setShowForm(false);
      setEditingService(null);
      fetchServices();
    } catch (err) {
      setError(err instanceof Error ? err.message : editingService ? "Fehler beim Speichern." : "Fehler beim Erstellen.");
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(serviceId: string) {
    if (!currentTenantId || !slug) return;
    if (!confirm("Service wirklich löschen?")) return;
    try {
      await apiFetch(`/api/v1/clients/${slug}/services/${serviceId}/`, {
        method: "DELETE",
        tenantId: currentTenantId,
      });
      fetchServices();
    } catch {
      /* ignore */
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
            <Link href="/mandanten" className="hover:underline">Mandanten</Link>
            <span>/</span>
            <Link href={`/mandanten/${slug}`} className="hover:underline">{slug}</Link>
            <span>/</span>
            <span>Services</span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight">Services</h1>
        </div>
        <Button onClick={() => { if (showForm) { cancelForm(); } else { setShowForm(true); } }}>
          {showForm ? "Abbrechen" : "Neuer Service"}
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>{editingService ? "Service bearbeiten" : "Neuen Service anlegen"}</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="svc-name">Name</Label>
                  <Input id="svc-name" placeholder="z.B. SEO Kampagne Q1" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="svc-type">Typ</Label>
                  <select
                    id="svc-type"
                    className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                    value={form.service_type}
                    onChange={(e) => setForm({ ...form, service_type: e.target.value })}
                    required
                  >
                    <option value="">Bitte wählen</option>
                    {serviceTypes.map((st) => (
                      <option key={st.id} value={st.id}>{st.name}</option>
                    ))}
                  </select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="svc-budget">Monatsbudget</Label>
                  <Input id="svc-budget" type="number" step="0.01" min="0" placeholder="0.00" value={form.monthly_budget} onChange={(e) => setForm({ ...form, monthly_budget: e.target.value })} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="svc-status">Status</Label>
                  <select
                    id="svc-status"
                    className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                    value={form.status}
                    onChange={(e) => setForm({ ...form, status: e.target.value })}
                  >
                    {Object.entries(STATUS_LABELS).map(([value, label]) => (
                      <option key={value} value={value}>{label}</option>
                    ))}
                  </select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="svc-start">Start-Datum</Label>
                  <Input id="svc-start" type="date" value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="svc-end">End-Datum</Label>
                  <Input id="svc-end" type="date" value={form.end_date} onChange={(e) => setForm({ ...form, end_date: e.target.value })} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="svc-link">Link</Label>
                  <Input id="svc-link" type="url" placeholder="https://..." value={form.link} onChange={(e) => setForm({ ...form, link: e.target.value })} />
                </div>
                <div className="md:col-span-3 space-y-2">
                  <Label htmlFor="svc-desc">Beschreibung</Label>
                  <textarea
                    id="svc-desc"
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    rows={2}
                    value={form.description}
                    onChange={(e) => setForm({ ...form, description: e.target.value })}
                  />
                </div>
              </div>
              <Button type="submit" disabled={loading}>{loading ? "..." : editingService ? "Speichern" : "Erstellen"}</Button>
            </form>
            {error && <p className="mt-2 text-sm text-destructive">{error}</p>}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="p-0">
          <table className="w-full">
            <thead>
              <tr className="border-b text-left text-sm text-muted-foreground">
                <th className="w-8 p-4"></th>
                <th className="p-4">Name</th>
                <th className="p-4">Typ</th>
                <th className="p-4">Status</th>
                <th className="p-4">Monatsbudget</th>
                <th className="p-4">Start</th>
                <th className="p-4">Ende</th>
                <th className="p-4">Link</th>
                <th className="p-4"></th>
              </tr>
            </thead>
            <tbody>
              {services.map((s) => {
                const isExpanded = expandedIds.has(s.id);
                return (
                  <Fragment key={s.id}>
                    <tr className="border-b hover:bg-muted/50">
                      <td className="p-4 text-center">
                        {s.description ? (
                          <button
                            className="text-muted-foreground hover:text-foreground text-xs"
                            onClick={() => {
                              setExpandedIds((prev) => {
                                const next = new Set(prev);
                                if (next.has(s.id)) next.delete(s.id); else next.add(s.id);
                                return next;
                              });
                            }}
                          >
                            {isExpanded ? "\u25B2" : "\u25BC"}
                          </button>
                        ) : null}
                      </td>
                      <td className="p-4 font-medium">{s.name}</td>
                      <td className="p-4 text-sm">{s.service_type_name}</td>
                      <td className="p-4">
                        <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_COLORS[s.status] || ""}`}>
                          {STATUS_LABELS[s.status] || s.status}
                        </span>
                      </td>
                      <td className="p-4 font-mono text-sm">
                        {Number(s.monthly_budget).toLocaleString("de-DE", { style: "currency", currency: "EUR" })}
                      </td>
                      <td className="p-4 text-sm">
                        {s.start_date ? new Date(s.start_date).toLocaleDateString("de-DE") : "\u2014"}
                      </td>
                      <td className="p-4 text-sm">
                        {s.end_date ? new Date(s.end_date).toLocaleDateString("de-DE") : "\u2014"}
                      </td>
                      <td className="p-4 text-sm">
                        {s.link ? (
                          <a href={s.link} target="_blank" rel="noopener noreferrer" className="text-primary underline underline-offset-4 hover:text-primary/80">
                            Öffnen
                          </a>
                        ) : "\u2014"}
                      </td>
                      <td className="p-4 text-right space-x-2">
                        <Button variant="ghost" size="sm" onClick={() => startEdit(s)}>
                          Bearbeiten
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => handleDelete(s.id)}>
                          Löschen
                        </Button>
                      </td>
                    </tr>
                    {isExpanded && s.description && (
                      <tr className="border-b bg-muted/30">
                        <td></td>
                        <td colSpan={8} className="px-4 py-3 text-sm text-muted-foreground whitespace-pre-wrap">
                          {s.description}
                        </td>
                      </tr>
                    )}
                  </Fragment>
                );
              })}
              {services.length === 0 && (
                <tr>
                  <td colSpan={9} className="p-4 text-center text-sm text-muted-foreground">
                    Keine Services vorhanden.
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
