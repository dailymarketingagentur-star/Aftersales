"use client";

import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";
import { useTenant } from "@/hooks/use-tenant";
import type { NPSCampaign } from "@/types/nps";

const TRIGGER_LABELS: Record<string, string> = {
  day_offset: "Tag nach Start",
  quarterly: "Quartalsweise",
  manual: "Manuell",
};

export default function KampagnenPage() {
  const { currentTenantId } = useTenant();
  const [campaigns, setCampaigns] = useState<NPSCampaign[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    trigger_type: "day_offset",
    day_offset: 90,
    repeat_interval_days: 90,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchCampaigns = useCallback(async () => {
    if (!currentTenantId) return;
    try {
      const data = await apiFetch<NPSCampaign[]>("/api/v1/nps/campaigns/", { tenantId: currentTenantId });
      setCampaigns(data);
    } catch {
      /* ignore */
    }
  }, [currentTenantId]);

  useEffect(() => {
    fetchCampaigns();
  }, [fetchCampaigns]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!currentTenantId) return;
    setError("");
    setLoading(true);
    try {
      await apiFetch("/api/v1/nps/campaigns/", {
        method: "POST",
        body: JSON.stringify(formData),
        tenantId: currentTenantId,
      });
      setFormData({ name: "", trigger_type: "day_offset", day_offset: 90, repeat_interval_days: 90 });
      setShowForm(false);
      fetchCampaigns();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Fehler beim Erstellen.");
    } finally {
      setLoading(false);
    }
  }

  async function toggleActive(campaign: NPSCampaign) {
    if (!currentTenantId) return;
    try {
      await apiFetch(`/api/v1/nps/campaigns/${campaign.id}/`, {
        method: "PATCH",
        body: JSON.stringify({ is_active: !campaign.is_active }),
        tenantId: currentTenantId,
      });
      fetchCampaigns();
    } catch {
      /* ignore */
    }
  }

  async function handleDelete(id: string) {
    if (!currentTenantId || !confirm("Kampagne wirklich loeschen?")) return;
    try {
      await apiFetch(`/api/v1/nps/campaigns/${id}/`, {
        method: "DELETE",
        tenantId: currentTenantId,
      });
      fetchCampaigns();
    } catch {
      /* ignore */
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">NPS-Kampagnen</h1>
          <p className="text-muted-foreground">Automatisierte NPS-Umfragen konfigurieren.</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}>{showForm ? "Abbrechen" : "Neue Kampagne"}</Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Neue Kampagne</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Name</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="z.B. 90-Tage NPS"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="trigger">Trigger</Label>
                  <select
                    id="trigger"
                    className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                    value={formData.trigger_type}
                    onChange={(e) => setFormData({ ...formData, trigger_type: e.target.value })}
                  >
                    <option value="day_offset">Tag nach Start</option>
                    <option value="quarterly">Quartalsweise</option>
                    <option value="manual">Manuell</option>
                  </select>
                </div>
                {formData.trigger_type === "day_offset" && (
                  <div className="space-y-2">
                    <Label htmlFor="day_offset">Tag nach Client-Start</Label>
                    <Input
                      id="day_offset"
                      type="number"
                      min={1}
                      value={formData.day_offset}
                      onChange={(e) => setFormData({ ...formData, day_offset: Number(e.target.value) })}
                    />
                  </div>
                )}
                <div className="space-y-2">
                  <Label htmlFor="repeat">Wiederholung (Tage, 0 = einmalig)</Label>
                  <Input
                    id="repeat"
                    type="number"
                    min={0}
                    value={formData.repeat_interval_days}
                    onChange={(e) => setFormData({ ...formData, repeat_interval_days: Number(e.target.value) })}
                  />
                </div>
              </div>
              {error && <p className="text-sm text-destructive">{error}</p>}
              <Button type="submit" disabled={loading}>{loading ? "..." : "Erstellen"}</Button>
            </form>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="pt-6">
          {campaigns.length === 0 ? (
            <p className="text-sm text-muted-foreground">Noch keine Kampagnen erstellt.</p>
          ) : (
            <div className="space-y-0 divide-y">
              {campaigns.map((c) => (
                <div key={c.id} className="py-4 first:pt-0 last:pb-0 flex items-center gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm">{c.name}</span>
                      <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                        c.is_active ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-600"
                      }`}>
                        {c.is_active ? "Aktiv" : "Inaktiv"}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      {TRIGGER_LABELS[c.trigger_type]}
                      {c.trigger_type === "day_offset" && ` (Tag ${c.day_offset})`}
                      {c.repeat_interval_days > 0 ? ` · Alle ${c.repeat_interval_days} Tage` : " · Einmalig"}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={() => toggleActive(c)}>
                      {c.is_active ? "Deaktivieren" : "Aktivieren"}
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => handleDelete(c.id)}>
                      Loeschen
                    </Button>
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
