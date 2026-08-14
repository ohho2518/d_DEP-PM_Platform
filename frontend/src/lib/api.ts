// API client บาง ๆ ครอบ fetch — ทุก endpoint ตรงกับ Blueprint §13
import type {
  AgentMessage,
  BootstrapRequest,
  BootstrapResult,
  BreakdownResponse,
  CeoInboxItem,
  CeoPullResult,
  CeoReport,
  CeoStatus,
  DeliverableResult,
  DeploymentList,
  DesignUploadResult,
  LlmSettings,
  LlmSettingsUpdate,
  Portfolio,
  Project,
  ProjectUsage,
  ProviderTestResult,
  RunSummary,
  Task,
  TaskList,
  TaskStatus,
} from "./types";

// พอร์ต 8500 — :8000 เป็นของ d_CEO ที่รันค้างตลอด (ดู AGENTS.md §Ecosystem)
const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8500";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
    cache: "no-store",
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  portfolio: () => request<Portfolio>("/api/portfolio"),

  createProject: (body: { name: string; type: "new" | "existing"; repo_url?: string }) =>
    request<Project>("/api/projects", { method: "POST", body: JSON.stringify(body) }),

  getProject: (projectId: string) => request<Project>(`/api/projects/${projectId}`),

  /** เปิดโปรเจกต์ใหม่ "ของจริง" — สร้างโฟลเดอร์ + เอกสาร + git แล้วลงบอร์ดในคราวเดียว (ADR-05) */
  bootstrapProject: (body: BootstrapRequest) =>
    request<BootstrapResult>("/api/projects/bootstrap", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  deleteProject: (projectId: string) =>
    request<unknown>(`/api/projects/${projectId}`, { method: "DELETE" }),

  /** โทเคนของโปรเจกต์ แยกตามผู้ให้บริการ (§5 ใบสั่งงาน 2026-08-06) */
  projectUsage: (projectId: string) =>
    request<ProjectUsage>(`/api/projects/${projectId}/usage`),

  /** อัปโหลดไฟล์ดีไซน์เข้า `_design_input/` แล้วได้ requirement กลับมาให้ตรวจก่อนส่ง PM (ADR-05 S3)
   *  ⚠️ multipart — **ห้ามตั้ง Content-Type เอง** ต้องให้ browser ใส่ boundary ให้ */
  uploadDesignFiles: async (projectId: string, files: File[], note = "") => {
    const form = new FormData();
    files.forEach((f) => form.append("files", f));
    form.append("note", note);
    const res = await fetch(`${BASE}/api/projects/${projectId}/design-files`, {
      method: "POST",
      body: form,
      cache: "no-store",
    });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}: ${await res.text()}`);
    return (await res.json()) as DesignUploadResult;
  },

  /** เขียนผลงานของ task ลงไฟล์จริงในโฟลเดอร์โปรเจกต์ — สำรองไฟล์เดิมให้อัตโนมัติ */
  writeDeliverable: (projectId: string, taskId: string, path: string) =>
    request<DeliverableResult>(`/api/projects/${projectId}/deliverables`, {
      method: "POST",
      body: JSON.stringify({ task_id: taskId, path }),
    }),

  listTasks: (projectId: string) =>
    request<TaskList>(`/api/projects/${projectId}/tasks?limit=200`),

  breakdown: (projectId: string, requirement: string) =>
    request<BreakdownResponse>(`/api/projects/${projectId}/breakdown`, {
      method: "POST",
      body: JSON.stringify({ requirement }),
    }),

  confirmScope: (projectId: string, taskIds: string[] = []) =>
    request<TaskList>(`/api/projects/${projectId}/confirm`, {
      method: "POST",
      body: JSON.stringify({ task_ids: taskIds }),
    }),

  scan: (projectId: string) =>
    request<unknown>(`/api/projects/${projectId}/scan`, { method: "POST" }),

  /** สั่งรัน → 202 ทันทีพร้อม run_id (งานจริงรันเบื้องหลัง) · 409 = โปรเจกต์นี้กำลังรันอยู่ */
  runOrchestrator: (projectId: string) =>
    request<RunSummary>(`/api/projects/${projectId}/run`, { method: "POST" }),

  /** ขอให้รอบรันหยุด — หยุดหลัง task ปัจจุบันจบ · 409 = รอบนี้จบไปแล้ว */
  cancelRun: (projectId: string) =>
    request<RunSummary>(`/api/projects/${projectId}/run/cancel`, { method: "POST" }),

  /** ความคืบหน้าของรอบรัน — ไม่ส่ง runId = รอบล่าสุด · 404 = ยังไม่เคยรันในโปรเซสนี้ */
  getRun: (projectId: string, runId?: string) =>
    request<RunSummary>(
      `/api/projects/${projectId}/run${runId ? `?run_id=${runId}` : ""}`,
    ),

  patchTask: (taskId: string, body: Partial<Pick<Task, "title" | "description">> & { status?: TaskStatus }) =>
    request<Task>(`/api/tasks/${taskId}`, { method: "PATCH", body: JSON.stringify(body) }),

  taskMessages: (taskId: string) =>
    request<{ data: AgentMessage[] }>(`/api/tasks/${taskId}/messages`),

  listDeployments: (projectId?: string) =>
    request<DeploymentList>(
      `/api/deployments?limit=100${projectId ? `&project_id=${projectId}` : ""}`,
    ),

  // --- d_CEO (เลขา) — DEP-PM รับงานในฐานะ Team Lead R&D ---------------------
  ceoStatus: () => request<CeoStatus>("/api/ceo/status"),

  ceoInbox: () => request<{ data: CeoInboxItem[]; total: number }>("/api/ceo/inbox"),

  ceoPull: (taskIds: string[] = []) =>
    request<{ pulled: CeoPullResult[]; count: number }>("/api/ceo/pull", {
      method: "POST",
      body: JSON.stringify({ task_ids: taskIds, breakdown: true }),
    }),

  ceoReport: (projectId: string) =>
    request<CeoReport>(`/api/ceo/report/${projectId}`, { method: "POST" }),

  // --- ผู้ให้บริการ AI (ใบสั่งงาน 2026-08-06 "รองรับ AI หลายเจ้า") ------------
  /** คีย์ที่ได้กลับมาเป็นแบบ mask เท่านั้น — backend ไม่เคยส่งคีย์เต็มออกมา */
  llmSettings: () => request<LlmSettings>("/api/settings/llm"),

  /** ไม่ส่ง key ของเจ้าไหน = ไม่แตะของเดิม · ส่งสตริงว่าง = ตั้งใจลบ */
  saveLlmSettings: (body: LlmSettingsUpdate) =>
    request<LlmSettings>("/api/settings/llm", {
      method: "PUT",
      body: JSON.stringify(body),
    }),

  /** ยิงจริงหนึ่งครั้งต่อเจ้า — ไม่ระบุ provider = ทดสอบทุกเจ้า */
  testLlmProvider: (provider?: string) =>
    request<{ results: ProviderTestResult[] }>("/api/settings/llm/test", {
      method: "POST",
      body: JSON.stringify({ provider: provider ?? null }),
    }),
};
