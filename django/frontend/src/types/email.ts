export interface EmailProviderConnection {
  id: string;
  provider_type: "smtp" | "sendgrid";
  label: string;
  is_active: boolean;
  smtp_host: string;
  smtp_port: number;
  smtp_username: string;
  smtp_use_tls: boolean;
  from_email: string;
  from_name: string;
  last_tested_at: string | null;
  last_test_success: boolean | null;
  last_test_message: string;
  created_at: string;
  updated_at: string;
}

export interface EmailTemplate {
  id: string;
  tenant: string | null;
  slug: string;
  name: string;
  subject: string;
  body_html: string;
  body_text: string;
  variables: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ConnectionTestResult {
  success: boolean;
  message: string;
}
