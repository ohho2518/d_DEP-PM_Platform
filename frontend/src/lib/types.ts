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
  /** โทเคนแยกตามผู้ให้บริการ · null/ว่าง = งานที่ทำก่อน 2026-08-14 (แยกที่มาไม่ได้) */
  token_usage: Record<string, ProviderTokenEntry> | null;
  created_at: string;
  updated_at: string;
}

export interface ProviderTokenEntry {
  input?: number;
  output?: number;
  calls?: number;
  model?: string;
}

export interface Project {
  id: string;
  name: string;
  type: "new" | "existing";
  repo_url: string | null;
  status: string;
  /** task ใน d_CEO ที่ถูก delegate ลงมาเป็นโปรเจกต์นี้ (null = สร้างเองในระบบ) */
  ceo_task_id: string | null;
  /** โฟลเดอร์จริงบนดิสก์ (ตั้งตอน bootstrap — ADR-05) */
  local_path: string | null;
  /** ชนิดงาน — ของเดิมทั้งหมดเป็น "code" */
  kind: ProjectKind;
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

/** ชนิดงาน — ตัดสินว่าเส้นทาง 6 ขั้นเปิดขั้นไหนบ้าง · backend: `constants.ProjectKind` */
export type ProjectKind = "code" | "doc" | "idea";

/** ขั้นบนเส้นทางงาน · backend: `constants.ProjectStage` (คำนวณสด ไม่ได้เก็บใน DB) */
export type ProjectStage = "idea" | "structure" | "plan" | "build" | "ship" | "market";

/** ลำดับ + สีประจำขั้น — ใช้ร่วมกันทุกหน้า ห้ามนิยามซ้ำที่อื่น */
export const STAGE_COLOR: Record<ProjectStage, string> = {
  idea: "var(--gemini)",
  structure: "#6f7cf5",
  plan: "var(--claude)",
  build: "var(--warn)",
  ship: "var(--ok)",
  market: "#e8508d",
};

export interface StageItem {
  stage: ProjectStage;
  /** ชื่อที่คนอ่าน — ขั้นเดียวกันเรียกต่างกันได้ตามชนิดงาน (doc: "ส่งมอบ") */
  label: string;
  state: "done" | "current" | "todo";
}

export interface ProjectStages {
  kind: ProjectKind;
  /** null = เดินครบเส้นแล้ว */
  current: ProjectStage | null;
  stages: StageItem[];
  /** ประโยคเดียวที่บอกว่าต้องทำอะไรต่อ */
  next_action: string;
  ready_to_promote: boolean;
  open_tasks: number;
  total_tasks: number;
}

export interface PromoteRequest {
  kind: "code" | "doc";
  /** ใส่ = สร้างโฟลเดอร์จริงให้ในคราวเดียว · ไม่ใส่ = เปลี่ยนชนิดงานอย่างเดียว */
  target?: string;
  purpose?: string;
  stack?: string;
  is_python?: boolean;
  relation?: string;
}

export interface PromoteResult {
  project: Project;
  target: string;
  created: string[];
  steps: string[];
}

export interface IdeaSource {
  name: string;
  source_root: string;
  files: string[];
  is_folder: boolean;
  updated: string;
}

export interface IdeaPreview {
  roots: string[];
  found: number;
  already_on_board: number;
  /** เฉพาะที่ยังไม่อยู่บนบอร์ด */
  items: IdeaSource[];
}

export interface PortfolioProject {
  id: string;
  name: string;
  type: string;
  kind: ProjectKind;
  status: string;
  /** เส้นทางของโปรเจกต์นี้ — หน้ารวมใช้บอกว่า "ติดอยู่ตรงไหน" */
  pipeline: ProjectStages;
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

/** สถานะของ **รอบรัน** (คนละชุดกับ TaskStatus) — backend: `constants.RunStatus` */
export type RunState = "running" | "succeeded" | "failed" | "cancelled";

/** รอบรัน orchestrator — Phase 2 เป็นงานเบื้องหลัง: `POST /run` คืนตัวนี้ทันที (202)
 *  แล้วถามความคืบหน้าต่อที่ `GET /run` (ค่าเดิมของ run เดียวกัน อัปเดตไปเรื่อย ๆ) */
export interface RunSummary {
  run_id: string;
  project_id: string;
  status: RunState;
  /** task ที่ planned ตอนเริ่มรอบ = เป้าของ progress (processed < total ตอนจบได้ —
   *  ตัวที่รอ dependency ที่ escalated จะค้าง planned ทั้งรอบ) */
  total: number;
  processed: number;
  counts: Record<string, number>;
  /** รายงานกลับ d_CEO อัตโนมัติหลังงานจบ (null = โปรเจกต์นี้ไม่ได้มาจากเลขา) */
  ceo_report: CeoReport | null;
  /** เหตุที่รอบรันล้ม (status = "failed" เท่านั้น) */
  error: string | null;
  /** รอบจบเรียบร้อย (succeeded) แต่ **หยุดก่อนงานหมด** — ตอนนี้มีเหตุเดียวคือถึงเพดาน
   *  ค่าใช้จ่าย · งานที่เหลือยังค้าง planned กด Run ใหม่ได้ทันทีที่ขยับเพดาน */
  stopped_reason: string | null;
  /** ผู้ใช้กดยกเลิกแล้ว — รอ task ปัจจุบันจบก่อนถึงจะหยุดจริง */
  cancel_requested: boolean;
  /** ISO 8601 **UTC** */
  started_at: string;
  finished_at: string | null;
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

// --- เปิดโปรเจกต์ใหม่ "ของจริง" (ADR-05) -------------------------------------
// ต้องตรงกับ backend/app/schemas/project.py
export type ProjectRelation =
  | "general"
  | "product"
  | "service"
  | "middleware"
  | "eco-team"
  | "eco-core";

export interface BootstrapRequest {
  name: string;
  /** โฟลเดอร์ปลายทาง — ต้องอยู่ใต้ SCAFFOLD_ALLOWED_ROOT ของ backend */
  target: string;
  purpose?: string;
  stack?: string;
  is_python?: boolean;
  relation?: ProjectRelation;
  team?: string;
  dual_ps?: boolean;
}

export interface DesignUploadResult {
  saved: string[];
  /** ข้อความที่ประกอบจากไฟล์ทั้งหมด — ส่งต่อ /breakdown ได้เลย */
  requirement: string;
  requirement_chars: number;
}

export interface DeliverableResult {
  path: string;
  bytes: number;
  /** ที่อยู่สำเนาไฟล์เดิม (null = ยังไม่เคยมีไฟล์นี้) */
  backup: string | null;
  task_id: string;
}

export interface BootstrapResult {
  project: Project;
  target: string;
  created: string[];
  steps: string[];
  first_task_id: string;
}

// --- ผู้ให้บริการ AI (ใบสั่งงาน 2026-08-06) ---------------------------------
// ต้องตรงกับ backend/app/schemas/settings.py
export interface ProviderStatus {
  name: string;
  model: string;
  key_set: boolean;
  /** เช่น "sk-…4f2a" — backend **ไม่เคย** ส่งคีย์เต็มออกมา */
  key_masked: string;
  /** ราคาต่อ 1 ล้านโทเคน (USD) ที่ใช้ประมาณการค่าใช้จ่าย — อ่านอย่างเดียว แก้ที่ .env */
  price_in: number;
  price_out: number;
}

export interface ProjectUsage {
  project_id: string;
  totals: { input: number; output: number; calls: number };
  by_provider: {
    provider: string;
    model: string;
    input: number;
    output: number;
    calls: number;
    tasks: number;
    /** **ประมาณการ** จากราคาที่ตั้งไว้ใน .env ไม่ใช่บิลจริง */
    cost_usd: number;
  }[];
  /** โทเคนที่นับรวมไว้แต่ระบุเจ้าไม่ได้ — งานก่อน 2026-08-14 */
  untracked: { input: number; output: number; calls: number };
  budget: {
    spent_usd: number;
    /** 0 = ไม่ได้ตั้งเพดาน */
    limit_usd: number;
    action: BudgetAction;
    over: boolean;
    /** true = มีโทเคนที่ระบุเจ้าไม่ได้ ⇒ ของจริงสูงกว่าตัวเลขนี้ */
    excludes_untracked: boolean;
  };
}

/** เกินเพดานแล้วทำอะไร — backend: `config.llm_budget_action` */
export type BudgetAction = "warn" | "stop";

export interface LlmSettings {
  /** ตัวหลัก */
  provider: string;
  /** ลำดับสำรอง — ว่าง = ไม่มีตัวสำรอง (ล้มแล้วหยุด) */
  fallbacks: string[];
  providers: ProviderStatus[];
  /** เพดานค่าใช้จ่าย **ต่อโปรเจกต์** (USD) · 0 = ไม่จำกัด */
  budget_usd: number;
  budget_action: BudgetAction;
}

export interface LlmSettingsUpdate {
  provider?: string;
  fallbacks?: string[];
  /** ชื่อเจ้า -> คีย์ใหม่ · **ไม่ส่ง = ไม่แตะของเดิม · ส่งค่าว่าง = ลบ** */
  keys?: Record<string, string>;
  models?: Record<string, string>;
  budget_usd?: number;
  budget_action?: BudgetAction;
}

/** ชนิดปัญหาเมื่อทดสอบไม่ผ่าน — ตรงกับตารางแยก error ใน providers.py */
export type ProviderTestKind = "account" | "temporary" | "request" | "unknown";

export interface ProviderTestResult {
  provider: string;
  ok: boolean;
  model: string;
  latency_ms: number;
  kind: ProviderTestKind | null;
  detail: string;
}

// State Machine ฝั่ง UI — ต้องตรงกับ backend/app/orchestrator/state_machine.py
export const ALLOWED_TRANSITIONS: Record<TaskStatus, TaskStatus[]> = {
  backlog: ["planned"],
  planned: ["assigned"],
  assigned: ["in_progress"],
  // in_progress → escalated = เครื่องมือใช้ไม่ได้กลางคัน (AI ล่มทุกเจ้า) ไม่ใช่ "งานไม่ผ่าน"
  in_progress: ["review", "escalated"],
  review: ["done", "in_progress", "escalated"],
  done: ["deployed"],
  escalated: ["in_progress", "planned"],
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
