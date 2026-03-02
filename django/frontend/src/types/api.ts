export interface ApiResponse<T> {
  results: T[];
  next: string | null;
  previous: string | null;
}

export interface SubscriptionStatus {
  id: string;
  status: "active" | "trialing" | "past_due" | "canceled" | "incomplete" | "none";
  plan_name: string;
  current_period_end: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}
