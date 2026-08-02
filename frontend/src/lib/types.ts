// Types สะท้อน Pydantic schemas ฝั่ง backend (backend/app/schemas + constants)

export type TaskStatus =
  | "backlog"
  | "planned"
  | "assigned"
  | "in_progress"
  | "review"
  | "done"
  | "deployed"
  | "escalated";

export type Priority = "P0" | "P1" | "P2" | "P3";

export interface Task {
  id: string;
  project_id: string;
  title: string;
  description: string | null;
  status: TaskStatus;
  assignee_type: "human" | "agent" | null;
  assignee_id: string | null;
  agent_role: string | null;
  priority: Priority;
  depends_on: string[];
  spec: string | null;
  estimate_points: number | null;
  revision_count: number;
  tokens_input: number;
  tokens_output: number;
  created_at: string;
  updated_at: string;
}

export interface Project {
  id: string;
  name: string;
  type: "new" | "existing";
  repo_url: string | null;
  status: string;
  /** task ใน d_CEO ที่ถูก delegate ลงมาเป็นโปรเจกต์นี้ (null = สร้างเองในระบบ) */
  ceo_task_id: string | null;
  created_at: string;
}

export interface TaskList {
  data: Task[];
  pagination: { total: number; limit: number; offset: number };
}

export interface AgentMessage {
  id: string;
  from_agent_id: string | null;
  to_agent_id: string | null;
  message_type: "handoff" | "question" | "result" | "review_comment";
  payload: Record<string, unknown>;
  created_at: string;
}

export interface PortfolioProject {
  id: string;
  name: string;
  type: string;
  status: string;
  task_counts: Partial<Record<TaskStatus, number>>;
  total_tasks: number;
  last_deployment: {
    id: string;
    status: string;
    environment: string | null;
    created_at: string;
  } | null;
}

export interface Portfolio {
  projects: PortfolioProject[];
  agents: { id: string; name: string; role: string; mode: string; status: string }[];
}

export interface RunSummary {
  project_id: string;
  processed: number;
  counts: Record<string, number>;
  /** รายงานกลับ d_CEO อัตโนมัติหลังงานจบ (null = โปรเจกต์นี้ไม่ได้มาจากเลขา) */
  ceo_report: CeoReport | null;
  outcomes: { task_id: string; title: string; final_status: string; revisions: number }[];
}

// --- d_CEO integration (Phase 1) — DEP-PM = Team Lead R&D ---------------------

export interface CeoStatus {
  enabled: boolean;
  online: boolean;
  team_name: string;
  base_url?: string;
  team_id?: string | null;
  waiting?: number;
  detail?: string;
}

export interface CeoInboxItem {
  id: string;
  input_text: string;
  status: string;
  /** ISO 8601 **UTC** — ต้องแปลงเป็น Asia/Bangkok ตอนแสดงผล */
  created_at: string;
}

export interface CeoPullResult {
  ceo_task_id: string;
  project_id: string;
  name: string;
  task_count: number;
  breakdown_source: "agent" | "fallback" | null;
  acknowledged: boolean;
  detail: string;
}

export interface CeoReport {
  ready: boolean;
  reported: boolean;
  status_sent: string | null;
  detail: string;
  counts?: Record<string, number>;
  output?: string | null;
}

export interface BreakdownResponse {
  source: "agent" | "fallback";
  tasks: Task[];
}

export type DeploymentStatus = "queued" | "running" | "success" | "failed";

export interface DeploymentItem {
  id: string;
  project_id: string;
  task_id: string | null;
  triggered_by: string;
  status: DeploymentStatus;
  environment: string | null;
  commit_sha: string | null;
  created_at: string;
  project_name: string | null;
  task_title: string | null;
}

export interface DeploymentList {
  data: DeploymentItem[];
  pagination: { total: number; limit: number; offset: number };
}

// State Machine ฝั่ง UI — ต้องตรงกับ backend/app/orchestrator/state_machine.py
export const ALLOWED_TRANSITIONS: Record<TaskStatus, TaskStatus[]> = {
  backlog: ["planned"],
  planned: ["assigned"],
  assigned: ["in_progress"],
  in_progress: ["review"],
  review: ["done", "in_progress", "escalated"],
  done: ["deployed"],
  escalated: ["in_progress"],
  deployed: [],
};

export const STATUS_ORDER: TaskStatus[] = [
  "backlog",
  "planned",
  "assigned",
  "in_progress",
  "review",
  "done",
  "deployed",
  "escalated",
];
