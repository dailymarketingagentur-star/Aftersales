"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";
import { useTenant } from "@/hooks/use-tenant";
import type { Client } from "@/types/client";
import type { InboundEmail, WhatsAppMessage } from "@/types/email";
import { ContactInfoSection } from "./contact-info-section";
import { IntegrationSection } from "./integration-section";
import { KeyFactsSection } from "./key-facts-section";
import { NPSSection } from "./nps-section";
import { ScoreOverviewSection } from "./score-overview-section";
import { TaskSection } from "./task-section";

const STATUS_OPTIONS = [
  { value: "active", label: "Aktiv" },
  { value: "onboarding", label: "Onboarding" },
  { value: "paused", label: "Pausiert" },
  { value: "churned", label: "Churned" },
];

const TIER_LABELS: Record<string, string> = {
  bronze: "Bronze",
  silber: "Silber",
  gold: "Gold",
  platin: "Platin",
};

export default function MandantDetailPage() {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;
  const { currentTenantId } = useTenant();

  const [client, setClient] = useState<Client | null>(null);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({
    name: "",
    contact_first_name: "",
    contact_last_name: "",
    website: "",
    start_date: "",
    cloud_storage_url: "",
    status: "onboarding",
    notes: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [unreadMessageCount, setUnreadMessageCount] = useState(0);

  const fetchClient = useCallback(async () => {
    if (!currentTenantId || !slug) return;
    try {
      const data = await apiFetch<Client>(`/api/v1/clients/${slug}/`, { tenantId: currentTenantId });
      setClient(data);
      setForm({
        name: data.name,
        contact_first_name: data.contact_first_name,
        contact_last_name: data.contact_last_name,
        website: data.website,
        start_date: data.start_date || "",
        cloud_storage_url: data.cloud_storage_url,
        status: data.status,
        notes: data.notes,
      });
    } catch {
      /* ignore */
    }
  }, [currentTenantId, slug]);

  useEffect(() => {
    fetchClient();
  }, [fetchClient]);

  // Fetch unread message count for badge (emails + WhatsApp, client-specific + unassigned)
  useEffect(() => {
    if (!currentTenantId || !client) return;
    Promise.all([
      apiFetch<{ count: number; results: InboundEmail[] }>(
        `/api/v1/emails/inbound/?client=${client.id}`, { tenantId: currentTenantId }
      ),
      apiFetch<{ count: number; results: InboundEmail[] }>(
        "/api/v1/emails/inbound/?assigned=false", { tenantId: currentTenantId }
      ),
      apiFetch<{ count: number; results: WhatsAppMessage[] }>(
        `/api/v1/emails/whatsapp/?client=${client.id}`, { tenantId: currentTenantId }
      ).catch(() => ({ count: 0, results: [] as WhatsAppMessage[] })),
    ])
      .then(([clientEmails, unassignedEmails, waData]) => {
        const allEmails = [...clientEmails.results, ...unassignedEmails.results];
        const unreadEmails = allEmails.filter((e) => !e.is_read).length;
        const unreadWa = waData.results.filter((w) => !w.is_read).length;
        setUnreadMessageCount(unreadEmails + unreadWa);
      })
      .catch(() => setUnreadMessageCount(0));
  }, [currentTenantId, client]);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (!currentTenantId || !slug) return;
    setError("");
    setLoading(true);
    try {
      const payload = {
        ...form,
        start_date: form.start_date || null,
      };
      await apiFetch(`/api/v1/clients/${slug}/`, {
        method: "PATCH",
        body: JSON.stringify(payload),
        tenantId: currentTenantId,
      });
      setEditing(false);
      fetchClient();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Fehler beim Speichern.");
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete() {
    if (!currentTenantId || !slug) return;
    if (!confirm("Mandant wirklich als churned markieren?")) return;
    try {
      await apiFetch(`/api/v1/clients/${slug}/`, {
        method: "DELETE",
        tenantId: currentTenantId,
      });
      router.push("/mandanten");
    } catch {
      /* ignore */
    }
  }

  if (!client) {
    return <p className="text-muted-foreground">Laden...</p>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{client.name}</h1>
          <p className="text-muted-foreground">
            {TIER_LABELS[client.tier] || client.tier} &middot; Monatsvolumen{" "}
            {Number(client.monthly_volume).toLocaleString("de-DE", { style: "currency", currency: "EUR" })}
          </p>
          <div className="mt-2 flex gap-2">
            <Link href={`/mandanten/${slug}/services`}>
              <Button className="bg-blue-600 hover:bg-blue-700 text-white">Services</Button>
            </Link>
            <Link href={`/integrationen/nachrichten/posteingang?client=${client.id}&slug=${slug}`}>
              <Button className="relative bg-blue-600 hover:bg-blue-700 text-white">
                Posteingang
                {unreadMessageCount > 0 && (
                  <span className="absolute -right-2 -top-2 inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-red-500 px-1.5 text-xs font-bold text-white animate-pulse">
                    {unreadMessageCount}
                  </span>
                )}
              </Button>
            </Link>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setEditing(!editing)}>
            {editing ? "Abbrechen" : "Bearbeiten"}
          </Button>
          <Button variant="destructive" onClick={handleDelete}>
            Löschen
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Stammdaten</CardTitle>
          <CardDescription>Kontaktdaten und Vertragsinformationen</CardDescription>
        </CardHeader>
        <CardContent>
          {editing ? (
            <form onSubmit={handleSave} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Firmenname</Label>
                  <Input id="name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="status">Status</Label>
                  <select
                    id="status"
                    className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                    value={form.status}
                    onChange={(e) => setForm({ ...form, status: e.target.value })}
                  >
                    {STATUS_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="cfn">Vorname</Label>
                  <Input id="cfn" value={form.contact_first_name} onChange={(e) => setForm({ ...form, contact_first_name: e.target.value })} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="cln">Nachname</Label>
                  <Input id="cln" value={form.contact_last_name} onChange={(e) => setForm({ ...form, contact_last_name: e.target.value })} />
                </div>
                <div className="col-span-2 space-y-2">
                  <Label htmlFor="website">Website</Label>
                  <Input id="website" type="url" value={form.website} onChange={(e) => setForm({ ...form, website: e.target.value })} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="start_date">Kunde seit</Label>
                  <Input id="start_date" type="date" value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} />
                </div>
                <div className="col-span-2 space-y-2">
                  <Label htmlFor="cloud_storage_url">Cloud-Speicher</Label>
                  <Input id="cloud_storage_url" type="text" placeholder="https://drive.google.com/..." value={form.cloud_storage_url} onChange={(e) => setForm({ ...form, cloud_storage_url: e.target.value })} />
                </div>
                <div className="col-span-2 space-y-2">
                  <Label htmlFor="notes">Notizen</Label>
                  <textarea
                    id="notes"
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    rows={3}
                    value={form.notes}
                    onChange={(e) => setForm({ ...form, notes: e.target.value })}
                  />
                </div>
              </div>
              {error && <p className="text-sm text-destructive">{error}</p>}
              <Button type="submit" disabled={loading}>{loading ? "..." : "Speichern"}</Button>
            </form>
          ) : (
            <dl className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <dt className="text-muted-foreground">Kontakt</dt>
                <dd>{client.contact_first_name} {client.contact_last_name}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Website</dt>
                <dd>
                  {client.website ? (
                    <a href={client.website} target="_blank" rel="noopener noreferrer" className="text-primary underline underline-offset-4 hover:text-primary/80">
                      {client.website}
                    </a>
                  ) : "\u2014"}
                </dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Kunde seit</dt>
                <dd>{client.start_date ? new Date(client.start_date).toLocaleDateString("de-DE") : "\u2014"}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Cloud-Speicher</dt>
                <dd>
                  {client.cloud_storage_url ? (
                    <a href={client.cloud_storage_url} target="_blank" rel="noopener noreferrer" className="text-primary underline underline-offset-4 hover:text-primary/80">
                      {client.cloud_storage_url}
                    </a>
                  ) : "\u2014"}
                </dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Status</dt>
                <dd className="capitalize">{STATUS_OPTIONS.find((o) => o.value === client.status)?.label || client.status}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Health Score</dt>
                <dd>
                  <span className={`font-semibold ${
                    client.health_score >= 24 ? "text-green-600" :
                    client.health_score >= 18 ? "text-yellow-600" :
                    "text-red-600"
                  }`}>
                    {client.health_score}/35
                  </span>
                  <span className="ml-1 text-xs text-muted-foreground">
                    ({client.health_score >= 30 ? "Exzellent" :
                      client.health_score >= 24 ? "Gut" :
                      client.health_score >= 18 ? "Neutral" :
                      client.health_score >= 12 ? "Risiko" : "Kritisch"})
                  </span>
                </dd>
              </div>
              {client.notes && (
                <div className="col-span-2">
                  <dt className="text-muted-foreground">Notizen</dt>
                  <dd className="whitespace-pre-wrap">{client.notes}</dd>
                </div>
              )}
            </dl>
          )}
        </CardContent>
      </Card>

      {currentTenantId && (
        <>
          <ContactInfoSection
            slug={slug}
            tenantId={currentTenantId}
            contactName={`${client.contact_first_name} ${client.contact_last_name}`}
          />
          <KeyFactsSection slug={slug} tenantId={currentTenantId} />
          <IntegrationSection slug={slug} tenantId={currentTenantId} clientName={client.name} />
          <NPSSection slug={slug} tenantId={currentTenantId} clientId={client.id} />
          <ScoreOverviewSection
            slug={slug}
            tenantId={currentTenantId}
            healthScore={client.health_score}
            churnWarningCount={client.churn_warning_count}
            lastHealthAt={client.last_health_assessment_at}
            lastChurnAt={client.last_churn_assessment_at}
          />
          <TaskSection slug={slug} tenantId={currentTenantId} />
          <div className="flex justify-end">
            <Link href={`/mandanten/${slug}/aktivitaeten`}>
              <Button variant="outline">Aktivitäten anzeigen &rarr;</Button>
            </Link>
          </div>
        </>
      )}
    </div>
  );
}
