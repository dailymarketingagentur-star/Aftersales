"use client";

import { useState } from "react";
import Link from "next/link";
import { resendVerificationEmail } from "@/lib/auth";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function VerifyEmailPage() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [message, setMessage] = useState("");

  async function handleResend(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim()) return;

    setStatus("loading");
    setMessage("");

    try {
      await resendVerificationEmail(email);
      setStatus("success");
      setMessage("Bestätigungs-E-Mail wurde erneut gesendet.");
    } catch (err) {
      setStatus("error");
      setMessage(
        err instanceof Error ? err.message : "Fehler beim Senden der E-Mail."
      );
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle>E-Mail bestätigen</CardTitle>
          <CardDescription>
            Wir haben Ihnen eine Bestätigungs-E-Mail gesendet.
            Bitte klicken Sie auf den Link in der E-Mail, um Ihr Konto zu aktivieren.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-center text-sm text-muted-foreground">
            Keine E-Mail erhalten? Prüfen Sie Ihren Spam-Ordner oder fordern Sie eine neue an:
          </p>
          <form onSubmit={handleResend} className="space-y-3">
            <input
              type="email"
              placeholder="Ihre E-Mail-Adresse"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            />
            <Button type="submit" className="w-full" disabled={status === "loading"}>
              {status === "loading" ? "Wird gesendet..." : "Erneut senden"}
            </Button>
          </form>
          {message && (
            <p
              className={`text-center text-sm ${
                status === "success" ? "text-green-600" : "text-red-600"
              }`}
            >
              {message}
            </p>
          )}
          <p className="text-center text-sm">
            <Link href="/login" className="text-primary underline underline-offset-4 hover:text-primary/80">
              Zurück zur Anmeldung
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
