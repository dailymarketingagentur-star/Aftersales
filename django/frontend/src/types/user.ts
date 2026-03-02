export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  memberships: Membership[];
}

export interface Membership {
  id: string;
  user: string;
  user_email: string;
  user_name: string;
  tenant: string;
  tenant_name: string;
  tenant_slug: string;
  role: "owner" | "admin" | "member";
  is_active: boolean;
  created_at: string;
}
