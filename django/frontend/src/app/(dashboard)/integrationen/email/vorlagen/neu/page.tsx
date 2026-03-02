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

export default function NeueVorlagePage() {
  const { currentTenantId } = useTenant();
  const router = useRouter();
  const [slug, setSlug] = useState("");
  const [name, setName] = useState("");
  const [subject, setSubject] = useState("");
  const [bodyHtml, setBodyHtml] = useState("");
  const [bodyText, setBodyText] = useState("");
  const [variables, setVariables] = useState("");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [isError, setIsError] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setMessage("");
    try {
      const varList = variables
        .split(",")
        .map((v) => v.trim())
        .filter(Boolean);
      await apiFetch("/api/v1/emails/templates/", {
        method: "POST",
        body: JSON.stringify({
          slug,
          name,
          subject,
          body_html: bodyHtml,
          body_text: bodyText,
          variables: varList,
        }),
        tenantId: currentTenantId!,
      });
      router.push("/integrationen/email/vorlagen");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Fehler beim Erstellen.");
      setIsError(true);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Neue E-Mail-Vorlage</h1>
        <Link href="/integrationen/email/vorlagen">
          <Button variant="outline" size="sm">Zurück</Button>
        </Link>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Vorlage erstellen</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Label htmlFor="slug">Slug</Label>
                <Input id="slug" placeholder="willkommens-email" value={slug} onChange={(e) => setSlug(e.target.value)} required />
              </div>
              <div>
                <Label htmlFor="name">Name</Label>
                <Input id="name" placeholder="Willkommens-E-Mail" value={name} onChange={(e) => setName(e.target.value)} required />
              </div>
            </div>
            <div>
              <Label htmlFor="subject">Betreff</Label>
              <Input
                id="subject"
                placeholder="Willkommen bei {{FIRMENNAME}}, {{KUNDENNAME}}!"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                required
              />
            </div>
            <div>
              <Label htmlFor="bodyHtml">HTML-Body</Label>
              <textarea
                id="bodyHtml"
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono min-h-[200px]"
                placeholder="<p>Hallo {{KUNDENNAME}},</p>"
                value={bodyHtml}
                onChange={(e) => setBodyHtml(e.target.value)}
                required
              />
            </div>
            <div>
              <Label htmlFor="bodyText">Text-Body (optional)</Label>
              <textarea
                id="bodyText"
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono min-h-[100px]"
                placeholder="Hallo {{KUNDENNAME}},&#10;..."
                value={bodyText}
                onChange={(e) => setBodyText(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="variables">Variablen (kommagetrennt)</Label>
              <Input
                id="variables"
                placeholder="KUNDENNAME, FIRMENNAME, PROJEKTNAME"
                value={variables}
                onChange={(e) => setVariables(e.target.value)}
              />
              <p className="mt-1 text-xs text-muted-foreground">
                Verwende {"{{VARIABLENNAME}}"} im Betreff und Body.
              </p>
            </div>

            {message && (
              <p className={`text-sm ${isError ? "text-red-600" : "text-green-600"}`}>{message}</p>
            )}

            <Button type="submit" disabled={saving}>
              {saving ? "Erstelle..." : "Vorlage erstellen"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
