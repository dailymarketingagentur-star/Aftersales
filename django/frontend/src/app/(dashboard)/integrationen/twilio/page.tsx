"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useTenant } from "@/hooks/use-tenant";
import { apiFetch } from "@/lib/api";
import type { TwilioConnection } from "@/types/integration";

export default function TwilioPage() {
  const { currentTenantId } = useTenant();
  const [connection, setConnection] = useState<TwilioConnection | null>(null);

  useEffect(() => {
    if (!currentTenantId) return;
    apiFetch<TwilioConnection>("/api/v1/integrations/twilio/connection/", {
      tenantId: currentTenantId,
    })
      .then(setConnection)
      .catch(() => setConnection(null));
  }, [currentTenantId]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Twilio Telefonie</h1>
        <Link href="/integrationen">
          <Button variant="outline" size="sm">
            Zurück
          </Button>
        </Link>
      </div>

      {connection && connection.last_test_success === false && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <div className="flex items-start gap-3">
            <span className="mt-0.5 text-lg text-red-600">&#9888;</span>
            <div>
              <p className="font-medium text-red-800">
                Twilio-Verbindung fehlgeschlagen
              </p>
              <p className="mt-1 text-sm text-red-700">
                Der letzte Verbindungstest war nicht erfolgreich. Deine
                Zugangsdaten sind möglicherweise ungültig.
              </p>
              <div className="mt-3">
                <Link href="/integrationen/twilio/verbindung">
                  <Button size="sm" variant="destructive">
                    Zugangsdaten prüfen
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            Verbindungsstatus
            <span
              className={`inline-block h-3 w-3 rounded-full ${
                !connection
                  ? "bg-gray-300"
                  : connection.last_test_success === false
                    ? "bg-red-500"
                    : "bg-green-500"
              }`}
            />
          </CardTitle>
        </CardHeader>
        <CardContent>
          {connection ? (
            <div className="space-y-1 text-sm">
              <p>
                <span className="font-medium">Account SID:</span>{" "}
                {connection.account_sid}
              </p>
              <p>
                <span className="font-medium">Telefonnummer:</span>{" "}
                {connection.phone_number}
              </p>
              {connection.last_tested_at && (
                <p>
                  <span className="font-medium">Letzter Test:</span>{" "}
                  {new Date(connection.last_tested_at).toLocaleString("de-DE")}
                  {" — "}
                  <span
                    className={
                      connection.last_test_success === false
                        ? "font-medium text-red-600"
                        : "text-green-600"
                    }
                  >
                    {connection.last_test_success
                      ? "Erfolgreich"
                      : "Fehlgeschlagen"}
                  </span>
                </p>
              )}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              Keine Verbindung konfiguriert.
            </p>
          )}
          <div className="mt-4">
            <Link href="/integrationen/twilio/verbindung">
              <Button variant="outline" size="sm">
                {connection
                  ? "Verbindung bearbeiten"
                  : "Verbindung einrichten"}
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Hinweis zur Einrichtung</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          <p>
            Für die Browser-Telefonie muss in der Twilio-Console Folgendes
            eingerichtet sein:
          </p>
          <ol className="list-inside list-decimal space-y-1">
            <li>
              Eine <strong>Telefonnummer</strong> kaufen oder bestehende
              verwenden
            </li>
            <li>
              Eine <strong>TwiML App</strong> erstellen mit Voice URL →{" "}
              <code className="rounded bg-muted px-1 py-0.5">
                https://&lt;domain&gt;/api/v1/integrations/twilio/twiml/voice/
              </code>
            </li>
            <li>
              Die <strong>TwiML App SID</strong> (beginnt mit AP) hier
              hinterlegen
            </li>
          </ol>
        </CardContent>
      </Card>
    </div>
  );
}
