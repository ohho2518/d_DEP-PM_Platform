// API client บาง ๆ ครอบ fetch — ทุก endpoint ตรงกับ Blueprint §13
import type {
  AgentMessage,
  BreakdownResponse,
  Portfolio,
  Project,
  RunSummary,
  Task,
  TaskList,
  TaskStatus,
} from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

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
};
