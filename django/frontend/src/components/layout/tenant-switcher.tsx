"use client";

import { useTenant } from "@/hooks/use-tenant";

export function TenantSwitcher() {
  const { tenants, currentTenant, switchTenant } = useTenant();

  return (
    <div className="flex items-center gap-2">
      {tenants.length <= 1 ? (
        currentTenant ? (
          <span className="text-sm font-medium">{currentTenant.name}</span>
        ) : null
      ) : (
        <select
          className="h-9 rounded-md border border-input bg-background px-3 text-sm"
          value={currentTenant?.id || ""}
          onChange={(e) => switchTenant(e.target.value)}
        >
          {tenants.map((t) => (
            <option key={t.id} value={t.id}>
              {t.name}
            </option>
          ))}
        </select>
      )}
    </div>
  );
}
