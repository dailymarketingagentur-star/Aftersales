"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useTenant } from "@/hooks/use-tenant";
import { apiFetch } from "@/lib/api";
import type { ActionSequence, ActionTemplate, SequenceStep } from "@/types/integration";

export default function SequenzDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { currentTenantId } = useTenant();
  const [sequence, setSequence] = useState<ActionSequence | null>(null);
  const [templates, setTemplates] = useState<ActionTemplate[]>([]);
  const [message, setMessage] = useState("");
  const [isError, setIsError] = useState(false);

  // New step form
  const [newTemplateId, setNewTemplateId] = useState("");
  const [newPosition, setNewPosition] = useState(1);
  const [newDelay, setNewDelay] = useState(0);
  const [addingStep, setAddingStep] = useState(false);

  function fetchSequence() {
    if (!currentTenantId || !id) return;
    apiFetch<ActionSequence>(`/api/v1/integrations/sequences/${id}/`, { tenantId: currentTenantId })
      .then((seq) => {
        setSequence(seq);
        setNewPosition(seq.steps.length + 1);
      })
      .catch(() => {});
  }

  useEffect(() => {
    fetchSequence();
    if (!currentTenantId) return;
    apiFetch<ActionTemplate[]>("/api/v1/integrations/templates/", { tenantId: currentTenantId })
      .then(setTemplates)
      .catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentTenantId, id]);

  async function handleAddStep(e: React.FormEvent) {
    e.preventDefault();
    if (!newTemplateId) return;
    setAddingStep(true);
    setMessage("");
    try {
      await apiFetch(`/api/v1/integrations/sequences/${id}/steps/`, {
        method: "POST",
        body: JSON.stringify({
          template: newTemplateId,
          position: newPosition,
          delay_seconds: newDelay,
        }),
        tenantId: currentTenantId!,
      });
      setMessage("Schritt hinzugefügt!");
      setIsError(false);
      setNewTemplateId("");
      setNewDelay(0);
      fetchSequence();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Fehler.");
      setIsError(true);
    } finally {
      setAddingStep(false);
    }
  }

  async function handleDeleteStep(stepId: string) {
    if (!confirm("Schritt wirklich entfernen?")) return;
    try {
      await apiFetch(`/api/v1/integrations/sequences/${id}/steps/${stepId}/`, {
        method: "DELETE",
        tenantId: currentTenantId!,
      });
      fetchSequence();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Fehler beim Löschen.");
      setIsError(true);
    }
  }

  async function handleDeleteSequence() {
    if (!confirm("Sequenz wirklich löschen?")) return;
    try {
      await apiFetch(`/api/v1/integrations/sequences/${id}/`, {
        method: "DELETE",
        tenantId: currentTenantId!,
      });
      router.push("/integrationen/jira/sequenzen");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Fehler beim Löschen.");
      setIsError(true);
    }
  }

  if (!sequence) return <p>Laden...</p>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{sequence.name}</h1>
        <div className="flex gap-2">
          <Link href="/integrationen/jira/sequenzen">
            <Button variant="outline" size="sm">Zurück</Button>
          </Link>
          <Button variant="destructive" size="sm" onClick={handleDeleteSequence}>Löschen</Button>
        </div>
      </div>

      {sequence.description && (
        <p className="text-muted-foreground">{sequence.description}</p>
      )}

      {/* Steps */}
      <Card>
        <CardHeader>
          <CardTitle>Schritte ({sequence.steps.length})</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {sequence.steps.length === 0 && (
            <p className="text-sm text-muted-foreground">Keine Schritte vorhanden.</p>
          )}
          {sequence.steps.map((step) => (
            <div key={step.id} className="flex items-center justify-between rounded-lg border p-3">
              <div className="text-sm">
                <span className="font-medium">Schritt {step.position}:</span>{" "}
                <span className="font-mono">{step.template_slug}</span>
                <span className="ml-2 text-muted-foreground">({step.template_name})</span>
                {step.delay_seconds > 0 && (
                  <span className="ml-2 text-muted-foreground">+{step.delay_seconds}s Verzögerung</span>
                )}
              </div>
              <Button variant="ghost" size="sm" onClick={() => handleDeleteStep(step.id)}>
                Entfernen
              </Button>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Add Step */}
      <Card>
        <CardHeader>
          <CardTitle>Schritt hinzufügen</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleAddStep} className="space-y-4">
            <div className="grid gap-4 md:grid-cols-3">
              <div>
                <Label htmlFor="template">Vorlage</Label>
                <select
                  id="template"
                  value={newTemplateId}
                  onChange={(e) => setNewTemplateId(e.target.value)}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  required
                >
                  <option value="">Vorlage wählen...</option>
                  {templates.map((tpl) => (
                    <option key={tpl.id} value={tpl.id}>
                      {tpl.name} ({tpl.slug})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <Label htmlFor="position">Position</Label>
                <Input
                  id="position"
                  type="number"
                  min={1}
                  value={newPosition}
                  onChange={(e) => setNewPosition(parseInt(e.target.value) || 1)}
                />
              </div>
              <div>
                <Label htmlFor="delay">Verzögerung (Sekunden)</Label>
                <Input
                  id="delay"
                  type="number"
                  min={0}
                  value={newDelay}
                  onChange={(e) => setNewDelay(parseInt(e.target.value) || 0)}
                />
              </div>
            </div>

            {message && (
              <p className={`text-sm ${isError ? "text-red-600" : "text-green-600"}`}>{message}</p>
            )}

            <Button type="submit" disabled={addingStep}>
              {addingStep ? "Hinzufügen..." : "Schritt hinzufügen"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
