"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";
import { useTenant } from "@/hooks/use-tenant";
import type { Client } from "@/types/client";

const STATUS_LABELS: Record<string, string> = {
  active: "Aktiv",
  onboarding: "Onboarding",
  paused: "Pausiert",
  churned: "Churned",
};

const STATUS_COLORS: Record<string, string> = {
  active: "bg-green-100 text-green-800",
  onboarding: "bg-blue-100 text-blue-800",
  paused: "bg-yellow-100 text-yellow-800",
  churned: "bg-red-100 text-red-800",
};

const TIER_COLORS: Record<string, string> = {
  bronze: "bg-orange-100 text-orange-800",
  silber: "bg-gray-100 text-gray-800",
  gold: "bg-yellow-100 text-yellow-800",
  platin: "bg-purple-100 text-purple-800",
};

function healthColor(score: number): string {
  if (score >= 24) return "text-green-600";
  if (score >= 18) return "text-yellow-600";
  return "text-red-600";
}

export default function MandantenPage() {
  const { currentTenantId } = useTenant();
  const [clients, setClients] = useState<Client[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchClients = useCallback(async () => {
    if (!currentTenantId) return;
    try {
      const data = await apiFetch<Client[]>("/api/v1/clients/", { tenantId: currentTenantId });
      setClients(data);
    } catch {
      /* ignore */
    }
  }, [currentTenantId]);

  useEffect(() => {
    fetchClients();
  }, [fetchClients]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!currentTenantId) return;
    setError("");
    setLoading(true);
    try {
      await apiFetch("/api/v1/clients/", {
        method: "POST",
        body: JSON.stringify({ name, contact_email: contactEmail }),
        tenantId: currentTenantId,
      });
      setName("");
      setContactEmail("");
      setShowForm(false);
      fetchClients();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Fehler beim Erstellen.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Mandanten</h1>
          <p className="text-muted-foreground">Verwalten Sie Ihre Kunden und deren Dienstleistungen.</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}>
          {showForm ? "Abbrechen" : "Neuer Mandant"}
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Neuen Mandanten anlegen</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="flex gap-4 items-end">
              <div className="flex-1 space-y-2">
                <Label htmlFor="client-name">Name</Label>
                <Input id="client-name" placeholder="Firmenname" value={name} onChange={(e) => setName(e.target.value)} required />
              </div>
              <div className="flex-1 space-y-2">
                <Label htmlFor="client-email">Kontakt-E-Mail</Label>
                <Input id="client-email" type="email" placeholder="info@firma.de" value={contactEmail} onChange={(e) => setContactEmail(e.target.value)} />
              </div>
              <Button type="submit" disabled={loading}>{loading ? "..." : "Erstellen"}</Button>
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
                <th className="p-4">Name</th>
                <th className="p-4">Status</th>
                <th className="p-4">Tier</th>
                <th className="p-4">Monatsvolumen</th>
                <th className="p-4">Health</th>
              </tr>
            </thead>
            <tbody>
              {clients.map((c) => (
                <tr key={c.id} className="border-b last:border-0 hover:bg-muted/50">
                  <td className="p-4">
                    <Link href={`/mandanten/${c.slug}`} className="font-medium hover:underline">
                      {c.name}
                    </Link>
                  </td>
                  <td className="p-4">
                    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_COLORS[c.status] || ""}`}>
                      {STATUS_LABELS[c.status] || c.status}
                    </span>
                  </td>
                  <td className="p-4">
                    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${TIER_COLORS[c.tier] || ""}`}>
                      {c.tier}
                    </span>
                  </td>
                  <td className="p-4 font-mono text-sm">
                    {Number(c.monthly_volume).toLocaleString("de-DE", { style: "currency", currency: "EUR" })}
                  </td>
                  <td className="p-4">
                    <span className={`font-semibold ${healthColor(c.health_score)}`}>
                      {c.health_score}/35
                    </span>
                  </td>
                </tr>
              ))}
              {clients.length === 0 && (
                <tr>
                  <td colSpan={5} className="p-4 text-center text-sm text-muted-foreground">
                    Keine Mandanten vorhanden.
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
