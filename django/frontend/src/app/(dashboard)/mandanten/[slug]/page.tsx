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
import { CallButton } from "@/components/twilio/call-button";
import { AudioSettingsPanel } from "@/components/twilio/audio-settings";
import { IntegrationSection } from "./integration-section";
import { KeyFactsSection } from "./key-facts-section";
import { NPSSection } from "./nps-section";
import { TaskSection } from "./task-section";
import { TimelineSection } from "./timeline-section";

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
    contact_email: "",
    contact_phone: "",
    website: "",
    start_date: "",
    cloud_storage_url: "",
    status: "onboarding",
    health_score: 100,
    notes: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchClient = useCallback(async () => {
    if (!currentTenantId || !slug) return;
    try {
      const data = await apiFetch<Client>(`/api/v1/clients/${slug}/`, { tenantId: currentTenantId });
      setClient(data);
      setForm({
        name: data.name,
        contact_first_name: data.contact_first_name,
        contact_last_name: data.contact_last_name,
        contact_email: data.contact_email,
        contact_phone: data.contact_phone,
        website: data.website,
        start_date: data.start_date || "",
        cloud_storage_url: data.cloud_storage_url,
        status: data.status,
        health_score: data.health_score,
        notes: data.notes,
      });
    } catch {
      /* ignore */
    }
  }, [currentTenantId, slug]);

  useEffect(() => {
    fetchClient();
  }, [fetchClient]);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (!currentTenantId || !slug) return;
    setError("");
    setLoading(true);
    try {
      const payload = {
        ...form,
        start_date: form.start_date || null,
        health_score: Number(form.health_score),
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
        </div>
        <div className="flex gap-2">
          <Link href={`/mandanten/${slug}/services`}>
            <Button variant="outline">Services</Button>
          </Link>
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
                <div className="space-y-2">
                  <Label htmlFor="cemail">E-Mail</Label>
                  <Input id="cemail" type="email" value={form.contact_email} onChange={(e) => setForm({ ...form, contact_email: e.target.value })} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="cphone">Telefon</Label>
                  <Input id="cphone" value={form.contact_phone} onChange={(e) => setForm({ ...form, contact_phone: e.target.value })} />
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
                <div className="space-y-2">
                  <Label htmlFor="health_score">Health Score</Label>
                  <Input id="health_score" type="number" min={0} max={100} value={form.health_score} onChange={(e) => setForm({ ...form, health_score: Number(e.target.value) })} />
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
                <dt className="text-muted-foreground">E-Mail</dt>
                <dd>{client.contact_email || "\u2014"}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Telefon</dt>
                <dd>
                  {client.contact_phone ? (
                    <>
                      <CallButton
                        phoneNumber={client.contact_phone}
                        contactName={`${client.contact_first_name} ${client.contact_last_name}`}
                      />
                      <AudioSettingsPanel />
                    </>
                  ) : "\u2014"}
                </dd>
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
                <dd>{client.health_score}</dd>
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
          <KeyFactsSection slug={slug} tenantId={currentTenantId} />
          <IntegrationSection slug={slug} tenantId={currentTenantId} clientName={client.name} />
          <NPSSection slug={slug} tenantId={currentTenantId} clientId={client.id} />
          <TaskSection slug={slug} tenantId={currentTenantId} />
          <TimelineSection slug={slug} tenantId={currentTenantId} />
        </>
      )}
    </div>
  );
}
