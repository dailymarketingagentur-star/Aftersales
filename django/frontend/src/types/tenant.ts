export interface Tenant {
  id: string;
  name: string;
  slug: string;
  is_active: boolean;
  settings: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface TenantSwitcherItem {
  id: string;
  name: string;
  slug: string;
  role: string;
}
