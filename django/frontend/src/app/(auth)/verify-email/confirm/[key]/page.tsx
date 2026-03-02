"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { verifyEmail } from "@/lib/auth";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function ConfirmEmailPage() {
  const params = useParams<{ key: string }>();
  const router = useRouter();
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    if (!params.key) return;

    verifyEmail(decodeURIComponent(params.key))
      .then(() => {
        setStatus("success");
        setTimeout(() => router.push("/login"), 3000);
      })
      .catch((err) => {
        setStatus("error");
        setErrorMessage(
          err instanceof Error ? err.message : "Der Bestätigungslink ist ungültig oder abgelaufen."
        );
      });
  }, [params.key, router]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <Card className="w-full max-w-md">
        {status === "loading" && (
          <>
            <CardHeader className="text-center">
              <CardTitle>E-Mail wird bestätigt...</CardTitle>
              <CardDescription>Bitte warten Sie einen Moment.</CardDescription>
            </CardHeader>
          </>
        )}

        {status === "success" && (
          <>
            <CardHeader className="text-center">
              <CardTitle>E-Mail bestätigt</CardTitle>
              <CardDescription>
                Ihre E-Mail-Adresse wurde erfolgreich bestätigt.
                Sie werden in Kürze zur Anmeldung weitergeleitet.
              </CardDescription>
            </CardHeader>
            <CardContent className="text-center">
              <Link href="/login" className="text-primary underline underline-offset-4 hover:text-primary/80">
                Jetzt anmelden
              </Link>
            </CardContent>
          </>
        )}

        {status === "error" && (
          <>
            <CardHeader className="text-center">
              <CardTitle>Bestätigung fehlgeschlagen</CardTitle>
              <CardDescription>{errorMessage}</CardDescription>
            </CardHeader>
            <CardContent className="text-center">
              <Button asChild>
                <Link href="/verify-email">Neue Bestätigungs-E-Mail anfordern</Link>
              </Button>
            </CardContent>
          </>
        )}
      </Card>
    </div>
  );
}
