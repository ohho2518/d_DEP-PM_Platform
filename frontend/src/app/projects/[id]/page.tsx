"use client";
// Kanban Board ต่อโปรเจกต์ + Task detail / Message Log Viewer + Run orchestrator
// สถานะเปลี่ยนด้วยปุ่ม (เรียก PATCH /api/tasks/:id — backend บังคับ State Machine)
import { use, useState } from "react";
import { api } from "@/lib/api";
import { usePolling } from "@/lib/usePolling";
import {
  ALLOWED_TRANSITIONS,
  STATUS_ORDER,
  type AgentMessage,
  type Task,
  type TaskStatus,
} from "@/lib/types";

const COLUMN_TINT: Record<TaskStatus, string> = {
  backlog: "border-neutral-700",
  planned: "border-sky-800",
  assigned: "border-indigo-800",
  in_progress: "border-amber-700",
  review: "border-purple-800",
  done: "border-emerald-800",
  deployed: "border-teal-800",
  escalated: "border-rose-800",
};

export default function BoardPage({ params }: { params: Promise<{ id: string }> }) {
  const { id: projectId } = use(params);
  const { data, error, refresh } = usePolling(() => api.listTasks(projectId), 4000);

  const [selected, setSelected] = useState<Task | null>(null);
  const [running, setRunning] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  async function moveTask(task: Task, to: TaskStatus) {
    try {
      await api.patchTask(task.id, { status: to });
      await refresh();
    } catch (e) {
      setNotice(e instanceof Error ? e.message : String(e));
    }
  }

  async function runOrchestrator() {
    setRunning(true);
    setNotice(null);
    try {
      const summary = await api.runOrchestrator(projectId);
      const parts = Object.entries(summary.counts)
        .map(([k, v]) => `${k}: ${v}`)
        .join(", ");
      setNotice(
        summary.processed === 0
          ? "ไม่มี task สถานะ planned ให้รัน (ยืนยัน scope ก่อน)"
          : `Orchestrator เสร็จ — ${summary.processed} tasks (${parts})`,
      );
      await refresh();
    } catch (e) {
      setNotice(e instanceof Error ? e.message : String(e));
    } finally {
      setRunning(false);
    }
  }

  if (error)
    return (
      <p className="rounded border border-rose-800 bg-rose-950/40 p-4 text-sm text-rose-300">
        โหลดบอร์ดไม่ได้: {error}
      </p>
    );
  if (!data) return <p className="text-neutral-400">กำลังโหลด…</p>;

  const byStatus = (s: TaskStatus) => data.data.filter((t) => t.status === s);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold">
          Kanban <span className="text-sm text-neutral-500">({data.pagination.total} tasks)</span>
        </h1>
        <button
          onClick={runOrchestrator}
          disabled={running}
          className="rounded bg-emerald-600 px-3 py-1.5 text-sm font-medium hover:bg-emerald-500 disabled:opacity-50"
        >
          {running ? "Agent กำลังทำงาน…" : "▶ Run Agents"}
        </button>
      </div>

      {notice && (
        <p className="rounded border border-neutral-700 bg-neutral-900 p-2 text-xs text-neutral-300">
          {notice}
        </p>
      )}

      <div className="flex gap-3 overflow-x-auto pb-4">
        {STATUS_ORDER.map((status) => (
          <div
            key={status}
            className={`w-60 shrink-0 rounded-lg border-t-2 bg-neutral-900/60 ${COLUMN_TINT[status]}`}
          >
            <div className="flex items-center justify-between px-3 py-2">
              <span className="text-xs font-semibold uppercase tracking-wide text-neutral-400">
                {status.replace("_", " ")}
              </span>
              <span className="text-xs text-neutral-500">{byStatus(status).length}</span>
            </div>
            <div className="space-y-2 px-2 pb-2">
              {byStatus(status).map((t) => (
                <TaskCard
                  key={t.id}
                  task={t}
                  onSelect={() => setSelected(t)}
                  onMove={(to) => moveTask(t, to)}
                />
              ))}
            </div>
          </div>
        ))}
      </div>

      {selected && (
        <TaskDetail task={selected} onClose={() => setSelected(null)} />
      )}
    </div>
  );
}

function TaskCard({
  task,
  onSelect,
  onMove,
}: {
  task: Task;
  onSelect: () => void;
  onMove: (to: TaskStatus) => void;
}) {
  const nexts = ALLOWED_TRANSITIONS[task.status];
  return (
    <div className="rounded border border-neutral-800 bg-neutral-950 p-2.5 text-sm">
      <button onClick={onSelect} className="block w-full text-left font-medium hover:text-emerald-400">
        {task.title}
      </button>
      <div className="mt-1.5 flex flex-wrap items-center gap-1.5 text-[11px]">
        <span className="rounded bg-neutral-800 px-1.5 py-0.5 text-neutral-400">{task.priority}</span>
        {task.assignee_type && (
          <span
            className={`rounded-full px-2 py-0.5 ${
              task.assignee_type === "agent"
                ? "bg-emerald-900/60 text-emerald-300"
                : "bg-sky-900/60 text-sky-300"
            }`}
          >
            {task.assignee_type === "agent" ? `🤖 ${task.agent_role ?? "agent"}` : "👤 human"}
          </span>
        )}
        {task.revision_count > 0 && (
          <span className="rounded bg-rose-900/50 px-1.5 py-0.5 text-rose-300">
            rev {task.revision_count}
          </span>
        )}
      </div>
      {nexts.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {nexts.map((to) => (
            <button
              key={to}
              onClick={() => onMove(to)}
              className="rounded border border-neutral-700 px-1.5 py-0.5 text-[11px] text-neutral-400 hover:border-emerald-600 hover:text-emerald-300"
            >
              → {to.replace("_", " ")}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function TaskDetail({ task, onClose }: { task: Task; onClose: () => void }) {
  const { data } = usePolling(() => api.taskMessages(task.id), 5000);

  return (
    <div className="fixed inset-0 z-20 flex justify-end bg-black/50" onClick={onClose}>
      <aside
        className="h-full w-full max-w-md overflow-y-auto border-l border-neutral-800 bg-neutral-950 p-5"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-start justify-between">
          <h2 className="pr-4 font-semibold">{task.title}</h2>
          <button onClick={onClose} className="text-neutral-500 hover:text-neutral-200">
            ✕
          </button>
        </div>

        <dl className="space-y-1 text-sm text-neutral-400">
          <div>status: <span className="text-neutral-200">{task.status}</span></div>
          <div>priority: {task.priority} · revisions: {task.revision_count}</div>
          {task.agent_role && <div>agent role: {task.agent_role}</div>}
          {task.description && <p className="pt-2 text-neutral-300">{task.description}</p>}
          {task.spec && (
            <p className="rounded bg-neutral-900 p-2 text-xs text-neutral-400">spec: {task.spec}</p>
          )}
        </dl>

        <h3 className="mb-2 mt-6 text-sm font-semibold uppercase tracking-wide text-neutral-400">
          Agent Conversation
        </h3>
        {!data ? (
          <p className="text-sm text-neutral-500">กำลังโหลด…</p>
        ) : data.data.length === 0 ? (
          <p className="text-sm text-neutral-500">ยังไม่มีข้อความ — กด “Run Agents” เพื่อเริ่มงาน</p>
        ) : (
          <ol className="space-y-2">
            {data.data.map((m) => (
              <MessageBubble key={m.id} m={m} />
            ))}
          </ol>
        )}
      </aside>
    </div>
  );
}

const TYPE_STYLE: Record<AgentMessage["message_type"], string> = {
  handoff: "border-sky-800",
  result: "border-neutral-700",
  review_comment: "border-purple-800",
  question: "border-rose-800",
};

function MessageBubble({ m }: { m: AgentMessage }) {
  return (
    <li className={`rounded border-l-2 bg-neutral-900 p-2.5 text-xs ${TYPE_STYLE[m.message_type]}`}>
      <div className="mb-1 flex items-center justify-between text-[11px] text-neutral-500">
        <span>
          {m.from_agent_id ?? "?"} → {m.to_agent_id ?? "ทุกคน"} · {m.message_type}
        </span>
        <span>{new Date(m.created_at).toLocaleTimeString("th-TH")}</span>
      </div>
      <pre className="whitespace-pre-wrap break-words font-sans text-neutral-300">
        {JSON.stringify(m.payload, null, 2)}
      </pre>
    </li>
  );
}
