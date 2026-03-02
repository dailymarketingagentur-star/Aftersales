"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useTenant } from "@/hooks/use-tenant";
import { apiFetch } from "@/lib/api";

export default function NeueSequenzPage() {
  const router = useRouter();
  const { currentTenantId } = useTenant();
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [description, setDescription] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      const seq = await apiFetch<{ id: string }>("/api/v1/integrations/sequences/", {
        method: "POST",
        body: JSON.stringify({ name, slug, description }),
        tenantId: currentTenantId!,
      });
      router.push(`/integrationen/jira/sequenzen/${seq.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Fehler beim Erstellen.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Neue Sequenz</h1>
        <Link href="/integrationen/jira/sequenzen">
          <Button variant="outline" size="sm">Zurück</Button>
        </Link>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Sequenz erstellen</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleCreate} className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Label htmlFor="name">Name</Label>
                <Input id="name" value={name} onChange={(e) => setName(e.target.value)} required />
              </div>
              <div>
                <Label htmlFor="slug">Slug</Label>
                <Input id="slug" value={slug} onChange={(e) => setSlug(e.target.value)} required placeholder="meine-sequenz" />
              </div>
            </div>
            <div>
              <Label htmlFor="description">Beschreibung</Label>
              <Input id="description" value={description} onChange={(e) => setDescription(e.target.value)} />
            </div>

            {error && <p className="text-sm text-red-600">{error}</p>}

            <Button type="submit" disabled={saving}>
              {saving ? "Erstellen..." : "Sequenz erstellen"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <p className="text-sm text-muted-foreground">
        Nach dem Erstellen können Sie auf der Detailseite Schritte hinzufügen.
      </p>
    </div>
  );
}
