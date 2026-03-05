"use client";

import { useEffect, useState } from "react";
import { Pencil, Trash2, Phone, Mail } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";
import { CallButton } from "@/components/twilio/call-button";
import { AudioSettingsPanel } from "@/components/twilio/audio-settings";
import type { ClientPhoneNumber, ClientEmailAddress } from "@/types/client";

interface ContactInfoSectionProps {
  slug: string;
  tenantId: string;
  contactName: string;
}

export function ContactInfoSection({ slug, tenantId, contactName }: ContactInfoSectionProps) {
  // --- Phone numbers state ---
  const [phones, setPhones] = useState<ClientPhoneNumber[]>([]);
  const [showAddPhone, setShowAddPhone] = useState(false);
  const [newPhoneLabel, setNewPhoneLabel] = useState("");
  const [newPhoneNumber, setNewPhoneNumber] = useState("");
  const [editingPhoneId, setEditingPhoneId] = useState<string | null>(null);
  const [editPhoneLabel, setEditPhoneLabel] = useState("");
  const [editPhoneNumber, setEditPhoneNumber] = useState("");

  // --- Email addresses state ---
  const [emails, setEmails] = useState<ClientEmailAddress[]>([]);
  const [showAddEmail, setShowAddEmail] = useState(false);
  const [newEmailLabel, setNewEmailLabel] = useState("");
  const [newEmailAddress, setNewEmailAddress] = useState("");
  const [editingEmailId, setEditingEmailId] = useState<string | null>(null);
  const [editEmailLabel, setEditEmailLabel] = useState("");
  const [editEmailAddress, setEditEmailAddress] = useState("");

  // --- Shared state ---
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  function showSuccess(msg: string) {
    setSuccessMsg(msg);
    setTimeout(() => setSuccessMsg(""), 3000);
  }

  // --- Fetch data ---
  useEffect(() => {
    if (!tenantId || !slug) return;
    apiFetch<ClientPhoneNumber[]>(`/api/v1/clients/${slug}/phone-numbers/`, { tenantId })
      .then(setPhones)
      .catch(() => {});
    apiFetch<ClientEmailAddress[]>(`/api/v1/clients/${slug}/email-addresses/`, { tenantId })
      .then(setEmails)
      .catch(() => {});
  }, [tenantId, slug]);

  // --- Phone CRUD ---
  async function handleAddPhone() {
    if (!newPhoneNumber.trim()) return;
    setSaving(true);
    setError("");
    try {
      const result = await apiFetch<ClientPhoneNumber>(`/api/v1/clients/${slug}/phone-numbers/`, {
        method: "POST",
        body: JSON.stringify({
          label: newPhoneLabel.trim(),
          number: newPhoneNumber.trim(),
          position: phones.length,
        }),
        tenantId,
      });
      setPhones((prev) => [...prev, result]);
      setNewPhoneLabel("");
      setNewPhoneNumber("");
      setShowAddPhone(false);
      showSuccess("Telefonnummer hinzugefügt.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Fehler beim Hinzufügen.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDeletePhone(id: string) {
    try {
      await apiFetch(`/api/v1/clients/${slug}/phone-numbers/${id}/`, {
        method: "DELETE",
        tenantId,
      });
      setPhones((prev) => prev.filter((p) => p.id !== id));
      showSuccess("Telefonnummer gelöscht.");
    } catch {
      /* ignore */
    }
  }

  function startEditPhone(p: ClientPhoneNumber) {
    setEditingPhoneId(p.id);
    setEditPhoneLabel(p.label);
    setEditPhoneNumber(p.number);
  }

  async function handleEditPhoneSave(id: string) {
    if (!editPhoneNumber.trim()) return;
    setSaving(true);
    try {
      const result = await apiFetch<ClientPhoneNumber>(`/api/v1/clients/${slug}/phone-numbers/${id}/`, {
        method: "PATCH",
        body: JSON.stringify({ label: editPhoneLabel.trim(), number: editPhoneNumber.trim() }),
        tenantId,
      });
      setPhones((prev) => prev.map((p) => (p.id === id ? result : p)));
      setEditingPhoneId(null);
      showSuccess("Telefonnummer aktualisiert.");
    } catch {
      /* ignore */
    } finally {
      setSaving(false);
    }
  }

  // --- Email CRUD ---
  async function handleAddEmail() {
    if (!newEmailAddress.trim()) return;
    setSaving(true);
    setError("");
    try {
      const result = await apiFetch<ClientEmailAddress>(`/api/v1/clients/${slug}/email-addresses/`, {
        method: "POST",
        body: JSON.stringify({
          label: newEmailLabel.trim(),
          email: newEmailAddress.trim(),
          position: emails.length,
        }),
        tenantId,
      });
      setEmails((prev) => [...prev, result]);
      setNewEmailLabel("");
      setNewEmailAddress("");
      setShowAddEmail(false);
      showSuccess("E-Mail-Adresse hinzugefügt.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Fehler beim Hinzufügen.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDeleteEmail(id: string) {
    try {
      await apiFetch(`/api/v1/clients/${slug}/email-addresses/${id}/`, {
        method: "DELETE",
        tenantId,
      });
      setEmails((prev) => prev.filter((e) => e.id !== id));
      showSuccess("E-Mail-Adresse gelöscht.");
    } catch {
      /* ignore */
    }
  }

  function startEditEmail(e: ClientEmailAddress) {
    setEditingEmailId(e.id);
    setEditEmailLabel(e.label);
    setEditEmailAddress(e.email);
  }

  async function handleEditEmailSave(id: string) {
    if (!editEmailAddress.trim()) return;
    setSaving(true);
    try {
      const result = await apiFetch<ClientEmailAddress>(`/api/v1/clients/${slug}/email-addresses/${id}/`, {
        method: "PATCH",
        body: JSON.stringify({ label: editEmailLabel.trim(), email: editEmailAddress.trim() }),
        tenantId,
      });
      setEmails((prev) => prev.map((e) => (e.id === id ? result : e)));
      setEditingEmailId(null);
      showSuccess("E-Mail-Adresse aktualisiert.");
    } catch {
      /* ignore */
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Kontaktdaten</CardTitle>
        {successMsg && <p className="text-sm text-green-600">{successMsg}</p>}
        {error && <p className="text-sm text-destructive">{error}</p>}
      </CardHeader>
      <CardContent className="space-y-6">
        {/* --- Telefonnummern --- */}
        <div>
          <div className="mb-2 flex items-center justify-between">
            <h3 className="flex items-center gap-2 text-sm font-medium">
              <Phone className="h-4 w-4" /> Telefonnummern
            </h3>
            <Button variant="outline" size="sm" onClick={() => setShowAddPhone(!showAddPhone)}>
              {showAddPhone ? "Abbrechen" : "Hinzufügen"}
            </Button>
          </div>

          {phones.length === 0 && !showAddPhone && (
            <p className="text-sm text-muted-foreground">Keine Telefonnummern hinterlegt.</p>
          )}

          <div className="space-y-2">
            {phones.map((p) => (
              <div key={p.id} className="flex items-center justify-between gap-2 rounded-md border p-3 text-sm">
                {editingPhoneId === p.id ? (
                  <div className="flex-1 space-y-2">
                    <Input
                      value={editPhoneLabel}
                      onChange={(e) => setEditPhoneLabel(e.target.value)}
                      placeholder="Label (optional)"
                    />
                    <Input
                      value={editPhoneNumber}
                      onChange={(e) => setEditPhoneNumber(e.target.value)}
                      placeholder="Telefonnummer"
                    />
                    <div className="flex gap-2">
                      <Button size="sm" disabled={saving} onClick={() => handleEditPhoneSave(p.id)}>
                        Speichern
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => setEditingPhoneId(null)}>
                        Abbrechen
                      </Button>
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="flex-1">
                      {p.label && <span className="font-medium">{p.label}: </span>}
                      <span className="text-muted-foreground">{p.number}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <CallButton phoneNumber={p.number} contactName={contactName} />
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 w-7 p-0"
                        title="Bearbeiten"
                        onClick={() => startEditPhone(p)}
                      >
                        <Pencil className="h-3.5 w-3.5" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 w-7 p-0 hover:text-destructive"
                        title="Löschen"
                        onClick={() => handleDeletePhone(p.id)}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>

          {showAddPhone && (
            <div className="mt-3 space-y-2 rounded-md border p-3">
              <Input
                placeholder='Label (optional, z.B. "Büro", "Mobil")'
                value={newPhoneLabel}
                onChange={(e) => setNewPhoneLabel(e.target.value)}
              />
              <Input
                placeholder="Telefonnummer"
                value={newPhoneNumber}
                onChange={(e) => setNewPhoneNumber(e.target.value)}
              />
              <Button size="sm" disabled={saving || !newPhoneNumber.trim()} onClick={handleAddPhone}>
                {saving ? "..." : "Speichern"}
              </Button>
            </div>
          )}

          {phones.length > 0 && <AudioSettingsPanel />}
        </div>

        {/* --- E-Mail-Adressen --- */}
        <div>
          <div className="mb-2 flex items-center justify-between">
            <h3 className="flex items-center gap-2 text-sm font-medium">
              <Mail className="h-4 w-4" /> E-Mail-Adressen
            </h3>
            <Button variant="outline" size="sm" onClick={() => setShowAddEmail(!showAddEmail)}>
              {showAddEmail ? "Abbrechen" : "Hinzufügen"}
            </Button>
          </div>

          {emails.length === 0 && !showAddEmail && (
            <p className="text-sm text-muted-foreground">Keine E-Mail-Adressen hinterlegt.</p>
          )}

          <div className="space-y-2">
            {emails.map((em) => (
              <div key={em.id} className="flex items-center justify-between gap-2 rounded-md border p-3 text-sm">
                {editingEmailId === em.id ? (
                  <div className="flex-1 space-y-2">
                    <Input
                      value={editEmailLabel}
                      onChange={(e) => setEditEmailLabel(e.target.value)}
                      placeholder="Label (optional)"
                    />
                    <Input
                      type="email"
                      value={editEmailAddress}
                      onChange={(e) => setEditEmailAddress(e.target.value)}
                      placeholder="E-Mail-Adresse"
                    />
                    <div className="flex gap-2">
                      <Button size="sm" disabled={saving} onClick={() => handleEditEmailSave(em.id)}>
                        Speichern
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => setEditingEmailId(null)}>
                        Abbrechen
                      </Button>
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="flex-1">
                      {em.label && <span className="font-medium">{em.label}: </span>}
                      <a
                        href={`mailto:${em.email}`}
                        className="text-primary underline underline-offset-4 hover:text-primary/80"
                      >
                        {em.email}
                      </a>
                    </div>
                    <div className="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 w-7 p-0"
                        title="Bearbeiten"
                        onClick={() => startEditEmail(em)}
                      >
                        <Pencil className="h-3.5 w-3.5" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 w-7 p-0 hover:text-destructive"
                        title="Löschen"
                        onClick={() => handleDeleteEmail(em.id)}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>

          {showAddEmail && (
            <div className="mt-3 space-y-2 rounded-md border p-3">
              <Input
                placeholder='Label (optional, z.B. "Buchhaltung", "Geschäftsführung")'
                value={newEmailLabel}
                onChange={(e) => setNewEmailLabel(e.target.value)}
              />
              <Input
                type="email"
                placeholder="E-Mail-Adresse"
                value={newEmailAddress}
                onChange={(e) => setNewEmailAddress(e.target.value)}
              />
              <Button size="sm" disabled={saving || !newEmailAddress.trim()} onClick={handleAddEmail}>
                {saving ? "..." : "Speichern"}
              </Button>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
