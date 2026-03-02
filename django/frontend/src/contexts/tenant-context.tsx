"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { getUserTenants } from "@/lib/auth";
import type { TenantSwitcherItem } from "@/types/tenant";

const TENANT_STORAGE_KEY = "current_tenant_id";

interface TenantContextValue {
  tenants: TenantSwitcherItem[];
  currentTenant: TenantSwitcherItem | null;
  currentTenantId: string | null;
  switchTenant: (tenantId: string) => void;
  loading: boolean;
  refetch: () => Promise<void>;
}

const TenantContext = createContext<TenantContextValue | null>(null);

export function TenantProvider({ children }: { children: React.ReactNode }) {
  const [tenants, setTenants] = useState<TenantSwitcherItem[]>([]);
  const [currentTenantId, setCurrentTenantId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem(TENANT_STORAGE_KEY);
    if (stored) setCurrentTenantId(stored);
  }, []);

  const fetchTenants = useCallback(async () => {
    try {
      const data = await getUserTenants();
      setTenants(data);
      const stored = localStorage.getItem(TENANT_STORAGE_KEY);
      if (data.length > 0 && !stored) {
        const id = data[0].id;
        setCurrentTenantId(id);
        localStorage.setItem(TENANT_STORAGE_KEY, id);
      }
    } catch {
      setTenants([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTenants();
  }, [fetchTenants]);

  const switchTenant = useCallback((tenantId: string) => {
    localStorage.setItem(TENANT_STORAGE_KEY, tenantId);
    window.location.reload();
  }, []);

  const currentTenant = tenants.find((t) => t.id === currentTenantId) || null;

  const value: TenantContextValue = {
    tenants, currentTenant, currentTenantId, switchTenant, loading, refetch: fetchTenants,
  };

  return <TenantContext value={value}>{children}</TenantContext>;
}

export function useTenantContext(): TenantContextValue {
  const ctx = useContext(TenantContext);
  if (!ctx) {
    throw new Error("useTenantContext must be used within a <TenantProvider>");
  }
  return ctx;
}
