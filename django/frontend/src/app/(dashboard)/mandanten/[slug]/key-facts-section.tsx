"use client";

import { useEffect, useState } from "react";
import { Pencil, Trash2, Info } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { apiFetch } from "@/lib/api";
import type { ClientKeyFact } from "@/types/client";

interface KeyFactsSectionProps {
  slug: string;
  tenantId: string;
}

export function KeyFactsSection({ slug, tenantId }: KeyFactsSectionProps) {
  const [keyFacts, setKeyFacts] = useState<ClientKeyFact[]>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [newLabel, setNewLabel] = useState("");
  const [newValue, setNewValue] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editLabel, setEditLabel] = useState("");
  const [editValue, setEditValue] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  function showSuccess(msg: string) {
    setSuccessMsg(msg);
    setTimeout(() => setSuccessMsg(""), 3000);
  }

  useEffect(() => {
    if (!tenantId || !slug) return;
    apiFetch<ClientKeyFact[]>(`/api/v1/clients/${slug}/key-facts/`, { tenantId })
      .then(setKeyFacts)
      .catch(() => {});
  }, [tenantId, slug]);

  async function handleAdd() {
    if (!newLabel.trim() || !newValue.trim()) return;
    setSaving(true);
    setError("");
    try {
      const result = await apiFetch<ClientKeyFact>(`/api/v1/clients/${slug}/key-facts/`, {
        method: "POST",
        body: JSON.stringify({
          label: newLabel.trim(),
          value: newValue.trim(),
          position: keyFacts.length,
        }),
        tenantId,
      });
      setKeyFacts((prev) => [...prev, result]);
      setNewLabel("");
      setNewValue("");
      setShowAdd(false);
      showSuccess(`"${result.label}" hinzugefügt.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Fehler beim Hinzufügen.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: string) {
    try {
      await apiFetch(`/api/v1/clients/${slug}/key-facts/${id}/`, {
        method: "DELETE",
        tenantId,
      });
      setKeyFacts((prev) => prev.filter((kf) => kf.id !== id));
      showSuccess("Key-Fact gelöscht.");
    } catch {
      /* ignore */
    }
  }

  function startEdit(kf: ClientKeyFact) {
    setEditingId(kf.id);
    setEditLabel(kf.label);
    setEditValue(kf.value);
  }

  async function handleEditSave(id: string) {
    if (!editLabel.trim() || !editValue.trim()) return;
    setSaving(true);
    try {
      const result = await apiFetch<ClientKeyFact>(`/api/v1/clients/${slug}/key-facts/${id}/`, {
        method: "PATCH",
        body: JSON.stringify({ label: editLabel.trim(), value: editValue.trim() }),
        tenantId,
      });
      setKeyFacts((prev) => prev.map((kf) => (kf.id === id ? result : kf)));
      setEditingId(null);
      showSuccess(`"${editLabel.trim()}" aktualisiert.`);
    } catch {
      /* ignore */
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Key-Facts</span>
          <Button variant="outline" size="sm" onClick={() => setShowAdd(!showAdd)}>
            {showAdd ? "Abbrechen" : "Hinzufügen"}
          </Button>
        </CardTitle>
        {successMsg && <p className="text-sm text-green-600">{successMsg}</p>}
      </CardHeader>
      <CardContent>
        <Alert className="mb-4">
          <Info className="h-4 w-4" />
          <AlertDescription>
            Key-Facts sind wichtige Informationen zu diesem Mandanten (z.B. bevorzugte
            Kommunikation, KPIs, Besonderheiten). Sie werden auch bei der
            Confluence-Synchronisation auf die Mandanten-Seite übertragen.
          </AlertDescription>
        </Alert>

        {keyFacts.length === 0 && !showAdd && (
          <p className="text-sm text-muted-foreground">
            Noch keine Key-Facts hinterlegt. Klicken Sie auf &quot;Hinzufügen&quot;, um wichtige Kunden-Infos zu erfassen.
          </p>
        )}

        <div className="space-y-2">
          {keyFacts.map((kf) => (
            <div key={kf.id} className="flex items-start justify-between gap-2 rounded-md border p-3 text-sm">
              {editingId === kf.id ? (
                <div className="flex-1 space-y-2">
                  <Input
                    value={editLabel}
                    onChange={(e) => setEditLabel(e.target.value)}
                    placeholder="Label"
                  />
                  <Input
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    placeholder="Wert"
                  />
                  <div className="flex gap-2">
                    <Button size="sm" disabled={saving} onClick={() => handleEditSave(kf.id)}>
                      Speichern
                    </Button>
                    <Button size="sm" variant="ghost" onClick={() => setEditingId(null)}>
                      Abbrechen
                    </Button>
                  </div>
                </div>
              ) : (
                <>
                  <div className="flex-1">
                    <span className="font-medium">{kf.label}:</span>{" "}
                    <span className="text-muted-foreground">{kf.value}</span>
                  </div>
                  <div className="flex gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 w-7 p-0"
                      title="Bearbeiten"
                      onClick={() => startEdit(kf)}
                    >
                      <Pencil className="h-3.5 w-3.5" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 w-7 p-0 hover:text-destructive"
                      title="Löschen"
                      onClick={() => handleDelete(kf.id)}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </>
              )}
            </div>
          ))}
        </div>

        {showAdd && (
          <div className="mt-3 space-y-2 rounded-md border p-3">
            <Input
              placeholder='z.B. "Bevorzugte Kommunikation"'
              value={newLabel}
              onChange={(e) => setNewLabel(e.target.value)}
            />
            <Input
              placeholder='z.B. "Telefonisch, nicht per Mail"'
              value={newValue}
              onChange={(e) => setNewValue(e.target.value)}
            />
            {error && <p className="text-sm text-destructive">{error}</p>}
            <Button size="sm" disabled={saving || !newLabel.trim() || !newValue.trim()} onClick={handleAdd}>
              {saving ? "..." : "Speichern"}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
