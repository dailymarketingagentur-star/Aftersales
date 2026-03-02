export interface NPSDashboard {
  score: number;
  total: number;
  promoters: number;
  passives: number;
  detractors: number;
  promoter_pct: number;
  passive_pct: number;
  detractor_pct: number;
  surveys_sent: number;
  surveys_responded: number;
  response_rate: number;
}

export interface NPSTrendPoint {
  month: string;
  score: number;
  total: number;
}

export interface NPSResponse {
  id: string;
  survey: string;
  client: string;
  client_name: string;
  client_slug: string;
  score: number;
  segment: "promoter" | "passive" | "detractor";
  comment: string;
  responded_at: string;
  created_at: string;
  updated_at: string;
}

export interface NPSSurvey {
  id: string;
  campaign: string | null;
  client: string;
  client_name: string;
  client_slug: string;
  token: string;
  status: "pending" | "responded" | "expired";
  sent_at: string | null;
  expires_at: string | null;
  has_response: boolean;
  created_at: string;
  updated_at: string;
}

export interface NPSCampaign {
  id: string;
  name: string;
  slug: string;
  trigger_type: "day_offset" | "quarterly" | "manual";
  day_offset: number;
  repeat_interval_days: number;
  is_active: boolean;
  email_template: string | null;
  email_template_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface TestimonialRequest {
  id: string;
  nps_response: string | null;
  client: string;
  client_name: string;
  client_slug: string;
  request_type: "google_review" | "video" | "written" | "draft_approve";
  status: "requested" | "accepted" | "received" | "published" | "declined";
  content: string;
  platform_url: string;
  requested_at: string;
  received_at: string | null;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface ClientNPSData {
  responses: NPSResponse[];
  surveys: NPSSurvey[];
  testimonials: TestimonialRequest[];
}
