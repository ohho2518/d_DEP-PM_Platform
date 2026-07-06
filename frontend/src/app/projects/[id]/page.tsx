"use client";
// Kanban Board + Agent Office (การ์ตูน agent แสดงสถานะจริง) + Task detail / Message Log
// โทนสีตาม ai-dev-team-complete.html
import { use, useState } from "react";
import AgentOffice from "@/components/AgentOffice";
import { api } from "@/lib/api";
import { usePolling } from "@/lib/usePolling";
import {
  ALLOWED_TRANSITIONS,
  STATUS_ORDER,
  type AgentMessage,
  type Task,
  type TaskStatus,
} from "@/lib/types";

const COLUMN_ACCENT: Record<TaskStatus, string> = {
  backlog: "var(--text3)",
  planned: "var(--gemini)",
  assigned: "var(--claude)",
  in_progress: "var(--warn)",
  review: "#a06010",
  done: "var(--ok)",
  deployed: "var(--codex)",
  escalated: "var(--danger)",
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
      <p className="card p-4 text-sm" style={{ color: "var(--danger)" }}>
        โหลดบอร์ดไม่ได้: {error}
      </p>
    );
  if (!data) return <p style={{ color: "var(--text2)" }}>กำลังโหลด…</p>;

  const byStatus = (s: TaskStatus) => data.data.filter((t) => t.status === s);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-bold">
          Kanban{" "}
          <span className="text-sm font-normal" style={{ color: "var(--text3)" }}>
            ({data.pagination.total} tasks)
          </span>
        </h1>
        <button onClick={runOrchestrator} disabled={running} className="btn-primary">
          {running ? "⚙ Agent กำลังทำงาน…" : "▶ Run Agents"}
        </button>
      </div>

      {/* ออฟฟิศจำลอง — agent เดินเมื่อกำลังทำงานจริง (สถานะจาก tasks ที่ poll ทุก 4 วิ) */}
      <AgentOffice tasks={data.data} />

      {notice && (
        <p className="card px-3 py-2 text-xs" style={{ color: "var(--text2)" }}>
          {notice}
        </p>
      )}

      <div className="flex gap-3 overflow-x-auto pb-4">
        {STATUS_ORDER.map((status) => (
          <div
            key={status}
            className="card w-60 shrink-0"
            style={{ borderTop: `3px solid ${COLUMN_ACCENT[status]}` }}
          >
            <div className="flex items-center justify-between px-3 py-2">
              <span
                className="text-[11px] font-bold uppercase tracking-wide"
                style={{ color: "var(--text2)" }}
              >
                {status.replace("_", " ")}
              </span>
              <span className="chip">{byStatus(status).length}</span>
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

      {selected && <TaskDetail task={selected} onClose={() => setSelected(null)} />}
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
    <div
      className="rounded-[10px] border p-2.5 text-sm"
      style={{ borderColor: "var(--border)", background: "#fafbff" }}
    >
      <button
        onClick={onSelect}
        className="block w-full text-left font-semibold hover:opacity-70"
        style={{ color: "var(--text)" }}
      >
        {task.title}
      </button>
      <div className="mt-1.5 flex flex-wrap items-center gap-1.5 text-[11px]">
        <span className="chip">{task.priority}</span>
        {task.assignee_type && (
          <span
            className="rounded-full px-2 py-0.5 text-white"
            style={{
              background: task.assignee_type === "agent" ? "var(--claude)" : "var(--gemini)",
            }}
          >
            {task.assignee_type === "agent" ? `🤖 ${task.agent_role ?? "agent"}` : "👤 human"}
          </span>
        )}
        {task.revision_count > 0 && (
          <span className="rounded-full px-2 py-0.5 text-white" style={{ background: "var(--danger)" }}>
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
              className="rounded border px-1.5 py-0.5 text-[11px]"
              style={{ borderColor: "var(--border)", color: "var(--text2)" }}
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
    <div className="fixed inset-0 z-20 flex justify-end bg-black/30" onClick={onClose}>
      <aside
        className="h-full w-full max-w-md overflow-y-auto border-l p-5"
        style={{ background: "var(--surface)", borderColor: "var(--border)" }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-start justify-between">
          <h2 className="pr-4 font-bold">{task.title}</h2>
          <button onClick={onClose} style={{ color: "var(--text3)" }}>✕</button>
        </div>

        <dl className="space-y-1 text-sm" style={{ color: "var(--text2)" }}>
          <div>status: <span className="font-semibold" style={{ color: "var(--text)" }}>{task.status}</span></div>
          <div>priority: {task.priority} · revisions: {task.revision_count}</div>
          {task.agent_role && <div>agent role: {task.agent_role}</div>}
          {task.description && <p className="pt-2" style={{ color: "var(--text)" }}>{task.description}</p>}
          {task.spec && (
            <p className="rounded-lg p-2 text-xs" style={{ background: "#f8f9ff" }}>
              spec: {task.spec}
            </p>
          )}
        </dl>

        <h3 className="mb-2 mt-6 text-xs font-bold uppercase tracking-wide" style={{ color: "var(--text2)" }}>
          Agent Conversation
        </h3>
        {!data ? (
          <p className="text-sm" style={{ color: "var(--text3)" }}>กำลังโหลด…</p>
        ) : data.data.length === 0 ? (
          <p className="text-sm" style={{ color: "var(--text3)" }}>
            ยังไม่มีข้อความ — กด “Run Agents” เพื่อเริ่มงาน
          </p>
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

const TYPE_ACCENT: Record<AgentMessage["message_type"], string> = {
  handoff: "var(--gemini)",
  result: "var(--text3)",
  review_comment: "var(--claude)",
  question: "var(--danger)",
};

function MessageBubble({ m }: { m: AgentMessage }) {
  return (
    <li
      className="rounded-lg border p-2.5 text-xs"
      style={{
        borderColor: "var(--border)",
        borderLeft: `3px solid ${TYPE_ACCENT[m.message_type]}`,
        background: "#fafbff",
      }}
    >
      <div className="mb-1 flex items-center justify-between text-[11px]" style={{ color: "var(--text3)" }}>
        <span>
          {m.from_agent_id ?? "?"} → {m.to_agent_id ?? "ทุกคน"} · {m.message_type}
        </span>
        <span>{new Date(m.created_at).toLocaleTimeString("th-TH")}</span>
      </div>
      <pre className="whitespace-pre-wrap break-words font-sans" style={{ color: "var(--text2)" }}>
        {JSON.stringify(m.payload, null, 2)}
      </pre>
    </li>
  );
}
