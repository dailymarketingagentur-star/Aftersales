export type ActionType =
  | "email"
  | "email_sequence"
  | "package"
  | "phone"
  | "meeting"
  | "document"
  | "jira_project"
  | "jira_ticket"
  | "webhook"
  | "manual";

export type TriggerMode = "manual" | "auto_on_due";

export type TaskPriority = "low" | "medium" | "high" | "critical";

export type TaskStatus = "open" | "in_progress" | "completed" | "skipped";

export interface Subtask {
  id: string;
  title: string;
  is_done: boolean;
  position: number;
  created_at: string;
  updated_at: string;
}

export interface EmailTemplateSummary {
  id: string;
  slug: string;
  name: string;
  subject: string;
}

export interface EmailPreview {
  template_slug: string;
  template_name: string;
  subject: string;
  body_html: string;
  recipient_email: string;
}

export interface Task {
  id: string;
  client: string;
  template: string | null;
  template_name: string | null;
  title: string;
  description: string;
  action_type: ActionType;
  phase: number;
  priority: TaskPriority;
  status: TaskStatus;
  due_date: string | null;
  assigned_to: string | null;
  assigned_to_email: string | null;
  completed_at: string | null;
  completed_by: string | null;
  completed_by_email: string | null;
  email_template: string | null;
  email_templates_detail: EmailTemplateSummary[];
  action_template_slug: string | null;
  action_sequence_slug: string | null;
  action_template_id: string | null;
  action_sequence_id: string | null;
  email_sequence_slug: string | null;
  email_sequence_id: string | null;
  notes: string;
  group_label: string;
  source_list_id: string | null;
  source_list_name: string | null;
  trigger_mode: TriggerMode | null;
  effective_trigger_mode: TriggerMode;
  auto_trigger_error: string;
  auto_trigger_attempted_at: string | null;
  subtasks: Subtask[];
  created_at: string;
  updated_at: string;
}

export interface TaskTemplate {
  id: string;
  slug: string;
  name: string;
  description: string;
  action_type: ActionType;
  phase: number;
  day_offset: number;
  priority: TaskPriority;
  email_template: string | null;
  default_subtasks: string[];
  is_active: boolean;
  trigger_mode: TriggerMode;
  is_system: boolean;
  email_templates_detail: EmailTemplateSummary[];
  action_template_slug: string | null;
  action_sequence_slug: string | null;
  action_template_id: string | null;
  action_sequence_id: string | null;
  email_sequence_slug: string | null;
  email_sequence_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface TaskListItem {
  id: string;
  task_template: string;
  template_name: string;
  template_slug: string;
  action_type: ActionType;
  phase: number;
  template_day_offset: number;
  priority: TaskPriority;
  position: number;
  group_label: string;
  group_position: number;
  day_offset: number | null;
}

export interface TaskList {
  id: string;
  slug: string;
  name: string;
  description: string;
  is_active: boolean;
  is_system: boolean;
  default_for_service_type: string | null;
  default_for_service_type_name: string | null;
  items: TaskListItem[];
  item_count: number;
  created_at: string;
  updated_at: string;
}

export interface JiraTemplateSummary {
  id: string;
  slug: string;
  name: string;
}

export interface TaskListUsageClient {
  slug: string;
  name: string;
}

export type ActivityType =
  | "comment"
  | "task_created"
  | "task_completed"
  | "task_skipped"
  | "status_changed"
  | "email_sent"
  | "jira_executed"
  | "webhook_executed"
  | "nps_sent"
  | "nps_received"
  | "auto_trigger_success"
  | "auto_trigger_failed"
  | "list_removed";

export interface ClientActivity {
  id: string;
  client: string;
  task: string | null;
  task_title: string | null;
  activity_type: ActivityType;
  content: string;
  author: string | null;
  author_email: string | null;
  created_at: string;
}
