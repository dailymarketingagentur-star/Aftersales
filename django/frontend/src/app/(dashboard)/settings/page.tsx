"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";
import { useTenant } from "@/hooks/use-tenant";
import type { Tenant } from "@/types/tenant";

export default function SettingsPage() {
  const { tenants, currentTenantId, switchTenant, loading, refetch } = useTenant();
  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [name, setName] = useState("");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [isError, setIsError] = useState(false);
  const [loadError, setLoadError] = useState("");

  useEffect(() => {
    if (!currentTenantId) return;
    setLoadError("");
    apiFetch<Tenant>(`/api/v1/tenants/${currentTenantId}/`, { tenantId: currentTenantId })
      .then((data) => {
        setTenant(data);
        setName(data.name);
      })
      .catch((err) => {
        setLoadError(err instanceof Error ? err.message : "Organisation konnte nicht geladen werden.");
      });
  }, [currentTenantId]);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (!currentTenantId) {
      setMessage("Keine Organisation ausgewählt. Bitte laden Sie die Seite neu.");
      setIsError(true);
      return;
    }
    setSaving(true);
    setMessage("");
    setIsError(false);

    try {
      await apiFetch(`/api/v1/tenants/${currentTenantId}/`, {
        method: "PATCH",
        body: JSON.stringify({ name }),
        tenantId: currentTenantId,
      });
      setMessage("Gespeichert!");
      setIsError(false);
      refetch();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Fehler beim Speichern.");
      setIsError(true);
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Einstellungen</h1>
          <p className="text-muted-foreground">Verwalten Sie Ihre Organisationseinstellungen.</p>
        </div>
        <p className="text-muted-foreground">Laden...</p>
      </div>
    );
  }

  if (!currentTenantId) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Einstellungen</h1>
          <p className="text-muted-foreground">Verwalten Sie Ihre Organisationseinstellungen.</p>
        </div>
        <Card>
          <CardHeader>
            <CardTitle>Keine Organisation vorhanden</CardTitle>
            <CardDescription>
              Erstellen Sie eine Organisation, um mit den Einstellungen zu beginnen.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild>
              <Link href="/create-org">Neue Organisation erstellen</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Einstellungen</h1>
        <p className="text-muted-foreground">Verwalten Sie Ihre Organisationseinstellungen.</p>
      </div>

      {loadError && <p className="text-sm text-destructive">{loadError}</p>}

      <Card>
        <CardHeader>
          <CardTitle>Organisation</CardTitle>
          <CardDescription>Allgemeine Informationen zu Ihrer Organisation</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSave} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="org-name">Name</Label>
              <Input id="org-name" value={name} onChange={(e) => setName(e.target.value)} required />
            </div>
            {tenant && (
              <div className="space-y-2">
                <Label>Slug</Label>
                <p className="text-sm text-muted-foreground">{tenant.slug}</p>
              </div>
            )}
            {message && <p className={`text-sm ${isError ? "text-destructive" : "text-green-600"}`}>{message}</p>}
            <Button type="submit" disabled={saving}>{saving ? "Speichern..." : "Speichern"}</Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Organisationen</CardTitle>
          <CardDescription>Wechseln Sie zwischen Ihren Organisationen oder erstellen Sie eine neue.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {tenants.length > 0 && (
            <div className="space-y-2">
              {tenants.map((t) => (
                <div key={t.id} className="flex items-center justify-between rounded-md border p-3">
                  <div>
                    <p className="text-sm font-medium">{t.name}</p>
                    <p className="text-xs text-muted-foreground">{t.slug}</p>
                  </div>
                  {t.id === currentTenantId ? (
                    <span className="text-xs text-muted-foreground">Aktiv</span>
                  ) : (
                    <Button variant="outline" size="sm" onClick={() => switchTenant(t.id)}>
                      Wechseln
                    </Button>
                  )}
                </div>
              ))}
            </div>
          )}
          <Button variant="outline" asChild>
            <Link href="/create-org">Neue Organisation erstellen</Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
