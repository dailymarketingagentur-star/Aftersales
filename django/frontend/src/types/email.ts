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
  inbound_parse_enabled: boolean;
  inbound_parse_domain: string;
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

export interface InboundEmail {
  id: string;
  from_email: string;
  from_name: string;
  to_email: string;
  subject: string;
  body_text: string;
  client: string | null;
  client_name: string | null;
  has_attachments: boolean;
  is_read: boolean;
  is_assigned: boolean;
  created_at: string;
}

export interface WhatsAppMessage {
  id: string;
  wa_message_id: string | null;
  direction: "inbound" | "outbound";
  from_number: string;
  to_number: string;
  body_text: string;
  message_type: "text" | "image" | "document" | "audio" | "video" | "template";
  status: "received" | "sent" | "delivered" | "read" | "failed";
  client: string | null;
  client_name: string | null;
  is_read: boolean;
  metadata: Record<string, unknown>;
  created_at: string;
}
