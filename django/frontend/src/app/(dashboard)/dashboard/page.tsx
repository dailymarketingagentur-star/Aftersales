"use client";

import { useAuth } from "@/hooks/use-auth";
import { useTenant } from "@/hooks/use-tenant";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Building2, CreditCard, Users } from "lucide-react";

export default function DashboardPage() {
  const { user } = useAuth();
  const { currentTenant } = useTenant();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Willkommen zurück{user ? `, ${user.first_name}` : ""}.
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card className="border-t-4 border-t-primary">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Building2 className="h-5 w-5 text-primary" />
              Organisation
            </CardTitle>
            <CardDescription>Aktuelle Organisation</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{currentTenant?.name || "\u2014"}</p>
          </CardContent>
        </Card>
        <Card className="border-t-4 border-t-primary">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CreditCard className="h-5 w-5 text-primary" />
              Abonnement
            </CardTitle>
            <CardDescription>Aktueller Status</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{"\u2014"}</p>
          </CardContent>
        </Card>
        <Card className="border-t-4 border-t-primary">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5 text-primary" />
              Team
            </CardTitle>
            <CardDescription>Mitglieder</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{"\u2014"}</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
