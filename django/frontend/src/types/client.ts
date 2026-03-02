export interface ServiceType {
  id: string;
  name: string;
  slug: string;
  is_default: boolean;
  position: number;
  created_at: string;
  updated_at: string;
}

export interface Client {
  id: string;
  name: string;
  slug: string;
  contact_first_name: string;
  contact_last_name: string;
  contact_email: string;
  contact_phone: string;
  website: string;
  cloud_storage_url: string;
  start_date: string | null;
  monthly_volume: string;
  tier: "bronze" | "silber" | "gold" | "platin";
  status: "active" | "onboarding" | "paused" | "churned";
  health_score: number;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface Service {
  id: string;
  client: string;
  service_type: string;
  service_type_name: string;
  name: string;
  status: "active" | "paused" | "completed" | "cancelled";
  start_date: string | null;
  end_date: string | null;
  monthly_budget: string;
  link: string;
  description: string;
  created_at: string;
  updated_at: string;
}

export interface CashflowMonth {
  month: string;
  label: string;
  total: string;
}

export interface ClientKeyFact {
  id: string;
  label: string;
  value: string;
  position: number;
  created_at: string;
  updated_at: string;
}
