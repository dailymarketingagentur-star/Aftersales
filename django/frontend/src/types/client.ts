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
  churn_warning_count: number;
  last_health_assessment_at: string | null;
  last_churn_assessment_at: string | null;
  notes: string;
  phone_numbers: ClientPhoneNumber[];
  email_addresses: ClientEmailAddress[];
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

export interface ClientPhoneNumber {
  id: string;
  label: string;
  number: string;
  position: number;
  created_at: string;
  updated_at: string;
}

export interface ClientEmailAddress {
  id: string;
  label: string;
  email: string;
  position: number;
  created_at: string;
  updated_at: string;
}

export interface HealthScoreAssessment {
  id: string;
  result_satisfaction: number;
  communication: number;
  engagement: number;
  relationship: number;
  payment_behavior: number;
  growth_potential: number;
  referral_readiness: number;
  total_score: number;
  status_label: string;
  notes: string;
  assessed_by: string | null;
  assessed_by_email: string | null;
  created_at: string;
}

export interface ChurnWarningAssessment {
  id: string;
  slower_responses: boolean;
  missed_checkins: boolean;
  decreased_usage: boolean;
  contract_inquiries: boolean;
  new_decision_maker: boolean;
  budget_cuts_mentioned: boolean;
  competitor_mentions: boolean;
  critical_feedback: boolean;
  delayed_payments: boolean;
  fewer_approvals: boolean;
  active_signals: number;
  notes: string;
  assessed_by: string | null;
  assessed_by_email: string | null;
  created_at: string;
}
