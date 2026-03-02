"use client";

import { useCallback, useEffect, useState } from "react";
import { useTenant } from "@/hooks/use-tenant";
import { apiFetch } from "@/lib/api";
import type { CopyConfigResult, CopySourceTenant } from "@/types/integration";

const TYPE_LABELS: Record<string, string> = {
  email_provider: "E-Mail-Provider (SMTP / SendGrid)",
  jira_connection: "Jira-Verbindung",
  action_templates: "Jira-Aktionsvorlagen",
};

export function CopyConfigButton() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50"
      >
        Von Mandant kopieren
      </button>
      {open && <CopyConfigDialog onClose={() => setOpen(false)} />}
    </>
  );
}

function CopyConfigDialog({ onClose }: { onClose: () => void }) {
  const { currentTenantId } = useTenant();
  const [sources, setSources] = useState<CopySourceTenant[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedTenant, setSelectedTenant] = useState("");
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [overwrite, setOverwrite] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<CopyConfigResult | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!currentTenantId) return;
    apiFetch<CopySourceTenant[]>("/api/v1/integrations/copy-config/sources/", {
      tenantId: currentTenantId,
    })
      .then((data) => {
        setSources(data);
        if (data.length > 0) {
          setSelectedTenant(data[0].tenant_id);
          setSelectedTypes(data[0].available_types);
        }
      })
      .catch(() => setError("Fehler beim Laden der Quell-Mandanten."))
      .finally(() => setLoading(false));
  }, [currentTenantId]);

  // Update selected types when tenant changes
  const handleTenantChange = useCallback(
    (tenantId: string) => {
      setSelectedTenant(tenantId);
      const source = sources?.find((s) => s.tenant_id === tenantId);
      if (source) setSelectedTypes(source.available_types);
    },
    [sources]
  );

  const availableTypes = sources?.find((s) => s.tenant_id === selectedTenant)?.available_types ?? [];

  function toggleType(type: string) {
    setSelectedTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    );
  }

  async function handleSubmit() {
    if (!currentTenantId || !selectedTenant || selectedTypes.length === 0) return;
    setSubmitting(true);
    setError("");
    try {
      const data = await apiFetch<CopyConfigResult>("/api/v1/integrations/copy-config/", {
        method: "POST",
        body: JSON.stringify({
          source_tenant_id: selectedTenant,
          types: selectedTypes,
          overwrite,
        }),
        tenantId: currentTenantId,
      });
      setResult(data);
      setTimeout(() => window.location.reload(), 1500);
    } catch {
      setError("Fehler beim Kopieren der Konfiguration.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="mx-4 w-full max-w-lg rounded-lg bg-white p-6 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Konfiguration von Mandant kopieren</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            ✕
          </button>
        </div>

        {loading && <p className="text-sm text-gray-500">Lade Quell-Mandanten…</p>}

        {!loading && error && !result && (
          <p className="text-sm text-red-600">{error}</p>
        )}

        {!loading && sources !== null && sources.length === 0 && (
          <p className="text-sm text-gray-500">
            Keine anderen Mandanten mit Konfigurationen gefunden.
          </p>
        )}

        {!loading && sources !== null && sources.length > 0 && !result && (
          <div className="space-y-4">
            {/* Tenant select */}
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Quell-Mandant
              </label>
              <select
                value={selectedTenant}
                onChange={(e) => handleTenantChange(e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              >
                {sources.map((s) => (
                  <option key={s.tenant_id} value={s.tenant_id}>
                    {s.tenant_name}
                  </option>
                ))}
              </select>
            </div>

            {/* Type checkboxes */}
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Zu kopierende Konfigurationen
              </label>
              <div className="space-y-2">
                {availableTypes.map((type) => (
                  <label key={type} className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={selectedTypes.includes(type)}
                      onChange={() => toggleType(type)}
                      className="rounded border-gray-300"
                    />
                    {TYPE_LABELS[type] ?? type}
                  </label>
                ))}
              </div>
            </div>

            {/* Overwrite checkbox */}
            <div>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={overwrite}
                  onChange={(e) => setOverwrite(e.target.checked)}
                  className="rounded border-gray-300"
                />
                Bestehende Konfigurationen überschreiben
              </label>
              {overwrite && (
                <p className="mt-1 text-xs text-yellow-600">
                  Bestehende Konfigurationen gleichen Typs werden gelöscht und durch die kopierten
                  ersetzt.
                </p>
              )}
            </div>

            {error && <p className="text-sm text-red-600">{error}</p>}

            {/* Actions */}
            <div className="flex justify-end gap-2">
              <button
                onClick={onClose}
                className="rounded-md border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
              >
                Abbrechen
              </button>
              <button
                onClick={handleSubmit}
                disabled={submitting || selectedTypes.length === 0}
                className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {submitting ? "Kopiere…" : "Kopieren"}
              </button>
            </div>
          </div>
        )}

        {/* Result */}
        {result && (
          <div className="space-y-3">
            {result.copied.length > 0 && (
              <div>
                <p className="text-sm font-medium text-green-700">Kopiert:</p>
                <ul className="ml-4 list-disc text-sm text-green-600">
                  {result.copied.map((item, i) => (
                    <li key={i}>{item}</li>
                  ))}
                </ul>
              </div>
            )}
            {result.skipped.length > 0 && (
              <div>
                <p className="text-sm font-medium text-gray-600">Übersprungen:</p>
                <ul className="ml-4 list-disc text-sm text-gray-500">
                  {result.skipped.map((item, i) => (
                    <li key={i}>{item}</li>
                  ))}
                </ul>
              </div>
            )}
            {result.errors.length > 0 && (
              <div>
                <p className="text-sm font-medium text-red-700">Fehler:</p>
                <ul className="ml-4 list-disc text-sm text-red-600">
                  {result.errors.map((item, i) => (
                    <li key={i}>{item}</li>
                  ))}
                </ul>
              </div>
            )}
            <p className="text-xs text-gray-400">Seite wird neu geladen…</p>
          </div>
        )}
      </div>
    </div>
  );
}
