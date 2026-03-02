"use client";

import { useTenantContext } from "@/contexts/tenant-context";

export function useTenant() {
  return useTenantContext();
}
