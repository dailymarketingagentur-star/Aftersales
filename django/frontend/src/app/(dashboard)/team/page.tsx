"use client";

import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";
import { useTenant } from "@/hooks/use-tenant";
import type { Membership } from "@/types/user";

export default function TeamPage() {
  const { currentTenantId } = useTenant();
  const [members, setMembers] = useState<Membership[]>([]);
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("member");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const fetchMembers = useCallback(async () => {
    if (!currentTenantId) return;
    try {
      const data = await apiFetch<Membership[]>("/api/v1/members/", { tenantId: currentTenantId });
      setMembers(data);
    } catch {
      /* ignore */
    }
  }, [currentTenantId]);

  useEffect(() => {
    fetchMembers();
  }, [fetchMembers]);

  async function handleInvite(e: React.FormEvent) {
    e.preventDefault();
    if (!currentTenantId) return;
    setError("");
    setLoading(true);

    try {
      await apiFetch("/api/v1/members/invite/", {
        method: "POST",
        body: JSON.stringify({ email, role }),
        tenantId: currentTenantId,
      });
      setEmail("");
      fetchMembers();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Einladung fehlgeschlagen.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Team</h1>
        <p className="text-muted-foreground">Verwalten Sie Ihre Teammitglieder.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Mitglied einladen</CardTitle>
          <CardDescription>Laden Sie ein neues Teammitglied per E-Mail ein.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleInvite} className="flex gap-4 items-end">
            <div className="flex-1 space-y-2">
              <Label htmlFor="invite-email">E-Mail</Label>
              <Input id="invite-email" type="email" placeholder="kollege@example.com" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="invite-role">Rolle</Label>
              <select id="invite-role" className="h-10 rounded-md border border-input bg-background px-3 text-sm" value={role} onChange={(e) => setRole(e.target.value)}>
                <option value="member">Mitglied</option>
                <option value="admin">Admin</option>
              </select>
            </div>
            <Button type="submit" disabled={loading}>{loading ? "..." : "Einladen"}</Button>
          </form>
          {error && <p className="mt-2 text-sm text-destructive">{error}</p>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Mitglieder</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {members.map((m) => (
              <div key={m.id} className="flex items-center justify-between rounded-lg border p-3">
                <div>
                  <p className="font-medium">{m.user_name || m.user_email}</p>
                  <p className="text-sm text-muted-foreground">{m.user_email}</p>
                </div>
                <span className="rounded-full bg-secondary px-3 py-1 text-xs font-medium capitalize">{m.role}</span>
              </div>
            ))}
            {members.length === 0 && <p className="text-sm text-muted-foreground">Keine Mitglieder gefunden.</p>}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
