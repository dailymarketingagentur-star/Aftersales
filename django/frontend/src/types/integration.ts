export interface JiraConnection {
  id: string;
  label: string;
  jira_url: string;
  jira_email: string;
  config: Record<string, string>;
  is_active: boolean;
  last_tested_at: string | null;
  last_test_success: boolean | null;
  created_at: string;
  updated_at: string;
}

export type TargetType = "jira" | "webhook";
export type AuthType = "none" | "bearer" | "basic" | "api_key";

export interface ActionTemplate {
  id: string;
  slug: string;
  name: string;
  description: string;
  target_type: TargetType;
  method: "GET" | "POST" | "PUT" | "DELETE";
  endpoint: string;
  webhook_url: string;
  auth_type: AuthType;
  body_json: Record<string, unknown>;
  headers_json: Record<string, unknown>;
  variables: string[];
  output_mapping: Record<string, string>;
  is_active: boolean;
  is_system: boolean;
  created_at: string;
  updated_at: string;
}

export interface SequenceStep {
  id: string;
  template: string;
  template_name: string;
  template_slug: string;
  position: number;
  delay_seconds: number;
  is_active: boolean;
}

export interface ActionSequence {
  id: string;
  slug: string;
  name: string;
  description: string;
  is_active: boolean;
  steps: SequenceStep[];
  step_count: number;
  created_at: string;
  updated_at: string;
}

export interface StepLog {
  id: string;
  position: number;
  template: string;
  template_slug: string;
  method: string;
  url: string;
  request_body: Record<string, unknown>;
  request_headers: Record<string, unknown>;
  status_code: number | null;
  response_body: Record<string, unknown>;
  response_headers: Record<string, unknown>;
  status: "success" | "failed" | "skipped";
  error_message: string;
  extracted_outputs: Record<string, unknown>;
  duration_ms: number | null;
  created_at: string;
}

export interface ActionExecution {
  id: string;
  sequence: string | null;
  sequence_slug: string;
  template: string | null;
  template_slug: string;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  input_context: Record<string, unknown>;
  accumulated_context: Record<string, unknown>;
  current_step: number;
  error_message: string;
  triggered_by: string | null;
  triggered_by_email: string;
  entity_type: string;
  entity_id: string;
  celery_task_id: string;
  idempotency_key: string;
  step_logs: StepLog[];
  created_at: string;
  updated_at: string;
}

export interface ActionExecutionListItem {
  id: string;
  sequence_slug: string;
  template_slug: string;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  current_step: number;
  error_message: string;
  triggered_by_email: string;
  entity_type: string;
  entity_id: string;
  created_at: string;
}

export interface ConnectionTestResult {
  success: boolean;
  message: string;
}

// ---------------------------------------------------------------------------
// Integration Types (Registry-based)
// ---------------------------------------------------------------------------
export interface IntegrationFieldDef {
  key: string;
  label: string;
  field_type: "url" | "text";
}

export interface IntegrationType {
  key: string;
  label: string;
  description: string;
  icon: string;
  fields: IntegrationFieldDef[];
  is_enabled: boolean;
}

export interface ClientIntegrationData {
  id: string;
  integration_type: string;
  data: Record<string, string>;
  fields_def: IntegrationFieldDef[];
  created_at: string;
  updated_at: string;
}

// ---------------------------------------------------------------------------
// Twilio
// ---------------------------------------------------------------------------
export interface TwilioConnection {
  id: string;
  label: string;
  account_sid: string;
  twiml_app_sid: string;
  phone_number: string;
  is_active: boolean;
  last_tested_at: string | null;
  last_test_success: boolean | null;
  created_at: string;
  updated_at: string;
}

export interface TwilioAccessToken {
  token: string;
  identity: string;
  phone_number: string;
}

// ---------------------------------------------------------------------------
// WhatsApp
// ---------------------------------------------------------------------------
export interface WhatsAppConnection {
  id: string;
  label: string;
  phone_number_id: string;
  business_account_id: string;
  webhook_verify_token: string;
  display_phone_number: string;
  is_active: boolean;
  last_tested_at: string | null;
  last_test_success: boolean | null;
  created_at: string;
  updated_at: string;
}

// ---------------------------------------------------------------------------
// Config Copy
// ---------------------------------------------------------------------------
export interface CopySourceTenant {
  tenant_id: string;
  tenant_name: string;
  available_types: string[];
}

export interface CopyConfigResult {
  copied: string[];
  skipped: string[];
  errors: string[];
}
