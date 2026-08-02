// API client บาง ๆ ครอบ fetch — ทุก endpoint ตรงกับ Blueprint §13
import type {
  AgentMessage,
  BreakdownResponse,
  CeoInboxItem,
  CeoPullResult,
  CeoReport,
  CeoStatus,
  DeploymentList,
  Portfolio,
  Project,
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

  runOrchestrator: (projectId: string) =>
    request<RunSummary>(`/api/projects/${projectId}/run`, { method: "POST" }),

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
};
