"use client";

import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";
import { useTenant } from "@/hooks/use-tenant";
import type { SubscriptionStatus } from "@/types/api";

export default function BillingPage() {
  const { currentTenantId } = useTenant();
  const [subscription, setSubscription] = useState<SubscriptionStatus | null>(null);

  const fetchStatus = useCallback(async () => {
    if (!currentTenantId) return;
    try {
      const data = await apiFetch<SubscriptionStatus>("/api/v1/billing/status/", { tenantId: currentTenantId });
      setSubscription(data);
    } catch {
      /* ignore */
    }
  }, [currentTenantId]);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  async function handleCheckout() {
    if (!currentTenantId) return;
    try {
      const data = await apiFetch<{ checkout_url: string }>("/api/v1/billing/checkout/", {
        method: "POST",
        body: JSON.stringify({
          price_id: "price_xxx", // Replace with actual Stripe Price ID
          success_url: `${window.location.origin}/billing?success=true`,
          cancel_url: `${window.location.origin}/billing?canceled=true`,
        }),
        tenantId: currentTenantId,
      });
      window.location.href = data.checkout_url;
    } catch {
      /* ignore */
    }
  }

  async function handlePortal() {
    if (!currentTenantId) return;
    try {
      const data = await apiFetch<{ portal_url: string }>("/api/v1/billing/portal/", {
        method: "POST",
        body: JSON.stringify({ return_url: `${window.location.origin}/billing` }),
        tenantId: currentTenantId,
      });
      window.location.href = data.portal_url;
    } catch {
      /* ignore */
    }
  }

  const statusLabels: Record<string, string> = {
    active: "Aktiv",
    trialing: "Testphase",
    past_due: "Überfällig",
    canceled: "Gekündigt",
    incomplete: "Unvollständig",
    none: "Kein Abonnement",
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Abrechnung</h1>
        <p className="text-muted-foreground">Verwalten Sie Ihr Abonnement.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Aktueller Plan</CardTitle>
          <CardDescription>Ihr aktueller Abonnement-Status</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-2xl font-bold">
                {subscription ? statusLabels[subscription.status] || subscription.status : "Laden..."}
              </p>
              {subscription?.plan_name && (
                <p className="text-sm text-muted-foreground">{subscription.plan_name}</p>
              )}
              {subscription?.current_period_end && (
                <p className="text-sm text-muted-foreground">
                  Nächste Abrechnung: {new Date(subscription.current_period_end).toLocaleDateString("de-DE")}
                </p>
              )}
            </div>
          </div>
          <div className="flex gap-4">
            {subscription?.is_active ? (
              <Button variant="outline" onClick={handlePortal}>Abonnement verwalten</Button>
            ) : (
              <Button onClick={handleCheckout}>Upgrade</Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
