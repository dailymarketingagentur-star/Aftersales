"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { register } from "@/lib/auth";

export function RegisterForm() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    email: "",
    first_name: "",
    last_name: "",
    password1: "",
    password2: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function updateField(field: string, value: string) {
    setFormData((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    if (formData.password1 !== formData.password2) {
      setError("Passwörter stimmen nicht überein.");
      return;
    }

    setLoading(true);
    try {
      await register(formData);
      router.push("/verify-email");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registrierung fehlgeschlagen.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="first_name">Vorname</Label>
          <Input id="first_name" value={formData.first_name} onChange={(e) => updateField("first_name", e.target.value)} required />
        </div>
        <div className="space-y-2">
          <Label htmlFor="last_name">Nachname</Label>
          <Input id="last_name" value={formData.last_name} onChange={(e) => updateField("last_name", e.target.value)} required />
        </div>
      </div>
      <div className="space-y-2">
        <Label htmlFor="email">E-Mail</Label>
        <Input id="email" type="email" placeholder="name@example.com" value={formData.email} onChange={(e) => updateField("email", e.target.value)} required />
      </div>
      <div className="space-y-2">
        <Label htmlFor="password1">Passwort</Label>
        <Input id="password1" type="password" value={formData.password1} onChange={(e) => updateField("password1", e.target.value)} required />
      </div>
      <div className="space-y-2">
        <Label htmlFor="password2">Passwort bestätigen</Label>
        <Input id="password2" type="password" value={formData.password2} onChange={(e) => updateField("password2", e.target.value)} required />
      </div>
      {error && <p className="text-sm text-destructive">{error}</p>}
      <Button type="submit" className="w-full" disabled={loading}>
        {loading ? "Registrieren..." : "Registrieren"}
      </Button>
    </form>
  );
}
