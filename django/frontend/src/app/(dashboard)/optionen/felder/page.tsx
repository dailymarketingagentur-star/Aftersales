"use client";

import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";
import { useTenant } from "@/hooks/use-tenant";
import type { ServiceType } from "@/types/client";

export default function FelderPage() {
  const { currentTenantId } = useTenant();
  const [serviceTypes, setServiceTypes] = useState<ServiceType[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [position, setPosition] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [editPosition, setEditPosition] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

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
    fetchServiceTypes();
  }, [fetchServiceTypes]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!currentTenantId) return;
    setError("");
    setLoading(true);
    try {
      await apiFetch("/api/v1/service-types/", {
        method: "POST",
        body: JSON.stringify({ name, position: position ? Number(position) : 0 }),
        tenantId: currentTenantId,
      });
      setName("");
      setPosition("");
      setShowForm(false);
      fetchServiceTypes();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Fehler beim Erstellen.");
    } finally {
      setLoading(false);
    }
  }

  async function handleUpdate(id: string) {
    if (!currentTenantId) return;
    try {
      await apiFetch(`/api/v1/service-types/${id}/`, {
        method: "PATCH",
        body: JSON.stringify({ name: editName, position: editPosition ? Number(editPosition) : 0 }),
        tenantId: currentTenantId,
      });
      setEditingId(null);
      fetchServiceTypes();
    } catch {
      /* ignore */
    }
  }

  async function handleDelete(id: string) {
    if (!currentTenantId) return;
    if (!confirm("Service-Typ wirklich löschen?")) return;
    try {
      await apiFetch(`/api/v1/service-types/${id}/`, {
        method: "DELETE",
        tenantId: currentTenantId,
      });
      fetchServiceTypes();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Löschen fehlgeschlagen. Wird der Typ noch verwendet?");
    }
  }

  function startEdit(st: ServiceType) {
    setEditingId(st.id);
    setEditName(st.name);
    setEditPosition(String(st.position));
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Service-Typen</h1>
          <p className="text-muted-foreground">Verwalten Sie die verfügbaren Dienstleistungstypen.</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}>
          {showForm ? "Abbrechen" : "Neuer Typ"}
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Neuen Service-Typ anlegen</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="flex gap-4 items-end">
              <div className="flex-1 space-y-2">
                <Label htmlFor="st-name">Name</Label>
                <Input id="st-name" placeholder="z.B. TikTok Ads" value={name} onChange={(e) => setName(e.target.value)} required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="st-pos">Position</Label>
                <Input id="st-pos" type="number" min="0" placeholder="0" value={position} onChange={(e) => setPosition(e.target.value)} />
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
                <th className="p-4">Position</th>
                <th className="p-4">Name</th>
                <th className="p-4">Slug</th>
                <th className="p-4">Standard</th>
                <th className="p-4"></th>
              </tr>
            </thead>
            <tbody>
              {serviceTypes.map((st) => (
                <tr key={st.id} className="border-b last:border-0 hover:bg-muted/50">
                  {editingId === st.id ? (
                    <>
                      <td className="p-4">
                        <Input type="number" min="0" className="w-20" value={editPosition} onChange={(e) => setEditPosition(e.target.value)} />
                      </td>
                      <td className="p-4">
                        <Input value={editName} onChange={(e) => setEditName(e.target.value)} />
                      </td>
                      <td className="p-4 text-sm text-muted-foreground">{st.slug}</td>
                      <td className="p-4 text-sm">{st.is_default ? "Ja" : "Nein"}</td>
                      <td className="p-4 text-right space-x-2">
                        <Button size="sm" onClick={() => handleUpdate(st.id)}>Speichern</Button>
                        <Button size="sm" variant="ghost" onClick={() => setEditingId(null)}>Abbrechen</Button>
                      </td>
                    </>
                  ) : (
                    <>
                      <td className="p-4 text-sm">{st.position}</td>
                      <td className="p-4 font-medium">{st.name}</td>
                      <td className="p-4 text-sm text-muted-foreground">{st.slug}</td>
                      <td className="p-4 text-sm">{st.is_default ? "Ja" : "Nein"}</td>
                      <td className="p-4 text-right space-x-2">
                        <Button size="sm" variant="ghost" onClick={() => startEdit(st)}>Bearbeiten</Button>
                        <Button size="sm" variant="ghost" onClick={() => handleDelete(st.id)}>Löschen</Button>
                      </td>
                    </>
                  )}
                </tr>
              ))}
              {serviceTypes.length === 0 && (
                <tr>
                  <td colSpan={5} className="p-4 text-center text-sm text-muted-foreground">
                    Keine Service-Typen vorhanden.
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
