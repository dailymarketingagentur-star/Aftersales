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
import type { EmailTemplate } from "@/types/email";

export default function VorlageDetailPage() {
  const { currentTenantId } = useTenant();
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [template, setTemplate] = useState<EmailTemplate | null>(null);
  const [name, setName] = useState("");
  const [subject, setSubject] = useState("");
  const [bodyHtml, setBodyHtml] = useState("");
  const [bodyText, setBodyText] = useState("");
  const [variables, setVariables] = useState("");
  const [isActive, setIsActive] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [isError, setIsError] = useState(false);
  const [loading, setLoading] = useState(true);

  const isSystem = template !== null && template.tenant === null;

  useEffect(() => {
    if (!currentTenantId || !params.id) return;
    apiFetch<EmailTemplate>(`/api/v1/emails/templates/${params.id}/`, { tenantId: currentTenantId })
      .then((tpl) => {
        setTemplate(tpl);
        setName(tpl.name);
        setSubject(tpl.subject);
        setBodyHtml(tpl.body_html);
        setBodyText(tpl.body_text);
        setVariables(tpl.variables.join(", "));
        setIsActive(tpl.is_active);
      })
      .catch(() => setTemplate(null))
      .finally(() => setLoading(false));
  }, [currentTenantId, params.id]);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setMessage("");
    try {
      const varList = variables
        .split(",")
        .map((v) => v.trim())
        .filter(Boolean);
      await apiFetch(`/api/v1/emails/templates/${params.id}/`, {
        method: "PATCH",
        body: JSON.stringify({
          name,
          subject,
          body_html: bodyHtml,
          body_text: bodyText,
          variables: varList,
          is_active: isActive,
        }),
        tenantId: currentTenantId!,
      });
      setMessage("Vorlage gespeichert!");
      setIsError(false);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Fehler beim Speichern.");
      setIsError(true);
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!confirm("Vorlage wirklich deaktivieren?")) return;
    try {
      await apiFetch(`/api/v1/emails/templates/${params.id}/`, {
        method: "DELETE",
        tenantId: currentTenantId!,
      });
      router.push("/integrationen/email/vorlagen");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Fehler beim Löschen.");
      setIsError(true);
    }
  }

  if (loading) {
    return <p className="text-muted-foreground">Lade Vorlage...</p>;
  }

  if (!template) {
    return <p className="text-red-600">Vorlage nicht gefunden.</p>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">
          Vorlage bearbeiten
          {isSystem && (
            <span className="ml-3 rounded bg-blue-100 px-2 py-0.5 text-sm font-normal text-blue-700">System</span>
          )}
        </h1>
        <Link href="/integrationen/email/vorlagen">
          <Button variant="outline" size="sm">Zurück</Button>
        </Link>
      </div>

      {isSystem && (
        <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
          <p className="text-sm text-blue-800">
            System-Vorlagen können nur angesehen, aber nicht bearbeitet werden. Erstelle eine eigene Vorlage mit dem gleichen Slug, um sie zu überschreiben.
          </p>
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>
            <span className="font-mono text-sm text-muted-foreground">{template.slug}</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSave} className="space-y-4">
            <div>
              <Label htmlFor="name">Name</Label>
              <Input id="name" value={name} onChange={(e) => setName(e.target.value)} disabled={isSystem} required />
            </div>
            <div>
              <Label htmlFor="subject">Betreff</Label>
              <Input id="subject" value={subject} onChange={(e) => setSubject(e.target.value)} disabled={isSystem} required />
            </div>
            <div>
              <Label htmlFor="bodyHtml">HTML-Body</Label>
              <textarea
                id="bodyHtml"
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono min-h-[200px]"
                value={bodyHtml}
                onChange={(e) => setBodyHtml(e.target.value)}
                disabled={isSystem}
                required
              />
            </div>
            <div>
              <Label htmlFor="bodyText">Text-Body</Label>
              <textarea
                id="bodyText"
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono min-h-[100px]"
                value={bodyText}
                onChange={(e) => setBodyText(e.target.value)}
                disabled={isSystem}
              />
            </div>
            <div>
              <Label htmlFor="variables">Variablen (kommagetrennt)</Label>
              <Input id="variables" value={variables} onChange={(e) => setVariables(e.target.value)} disabled={isSystem} />
            </div>
            <div className="flex items-center gap-2">
              <input
                id="isActive"
                type="checkbox"
                checked={isActive}
                onChange={(e) => setIsActive(e.target.checked)}
                disabled={isSystem}
                className="h-4 w-4 rounded border-gray-300"
              />
              <Label htmlFor="isActive">Aktiv</Label>
            </div>

            {message && (
              <p className={`text-sm ${isError ? "text-red-600" : "text-green-600"}`}>{message}</p>
            )}

            {!isSystem && (
              <div className="flex gap-2">
                <Button type="submit" disabled={saving}>
                  {saving ? "Speichern..." : "Speichern"}
                </Button>
                <Button type="button" variant="destructive" onClick={handleDelete}>
                  Deaktivieren
                </Button>
              </div>
            )}
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
