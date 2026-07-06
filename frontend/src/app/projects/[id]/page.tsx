"use client";
// Kanban Board + Agent Office (การ์ตูน agent แสดงสถานะจริง) + Task detail / Message Log
// โทนสีตาม ai-dev-team-complete.html
import { use, useEffect, useState } from "react";
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

// สถานะที่ถือว่า "จบแล้ว" สำหรับการคำนวณ progress ของรอบ run
const FINISHED: ReadonlySet<TaskStatus> = new Set(["done", "deployed", "escalated"]);

interface RunStats {
  startedAt: number;
  totalPlanned: number;     // จำนวน task ที่จะถูกประมวลผลรอบนี้
  baselineFinished: number; // task ที่จบอยู่แล้วก่อนเริ่ม (ไม่นับใน progress)
}

export default function BoardPage({ params }: { params: Promise<{ id: string }> }) {
  const { id: projectId } = use(params);

  const [selected, setSelected] = useState<Task | null>(null);
  const [running, setRunning] = useState(false);
  const [runStats, setRunStats] = useState<RunStats | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  // ระหว่างรัน poll ถี่ขึ้น (2 วิ) เพื่อให้ progress/การ์ตูนสดกว่า
  const { data, error, refresh } = usePolling(
    () => api.listTasks(projectId),
    running ? 2000 : 4000,
  );

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
    // baseline สำหรับ progress: นับจาก snapshot ล่าสุดก่อนเริ่ม
    const tasks = data?.data ?? [];
    setRunStats({
      startedAt: Date.now(),
      totalPlanned: tasks.filter((t) => t.status === "planned").length,
      baselineFinished: tasks.filter((t) => FINISHED.has(t.status)).length,
    });
    try {
      const summary = await api.runOrchestrator(projectId);
      const parts = Object.entries(summary.counts)
        .map(([k, v]) => `${k}: ${v}`)
        .join(", ");
      setNotice(
        summary.processed === 0
          ? "ไม่มี task สถานะ planned ให้รัน (ยืนยัน scope ก่อน)"
          : `✅ เสร็จแล้ว — ${summary.processed} tasks (${parts})`,
      );
      await refresh();
    } catch (e) {
      setNotice(e instanceof Error ? e.message : String(e));
    } finally {
      setRunning(false);
      setRunStats(null);
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

      {running && runStats && <RunProgress stats={runStats} tasks={data.data} />}

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

const PHASE_LABEL: Record<string, string> = {
  assigned: "กำลังมอบหมายงาน",
  in_progress: "agent กำลังเขียนงาน",
  review: "reviewer กำลังตรวจ",
};

function fmtDuration(sec: number): string {
  if (sec < 60) return `${Math.max(1, Math.round(sec))} วิ`;
  const m = Math.floor(sec / 60);
  const s = Math.round(sec % 60);
  return s ? `${m} นาที ${s} วิ` : `${m} นาที`;
}

/** Progress ของรอบ Run Agents — คำนวณจาก task ที่ poll สด (backend เป็น synchronous
 *  จึงไม่มี progress endpoint ตรง ๆ; ใช้จำนวน task ที่จบเทียบ baseline แทน) */
function RunProgress({ stats, tasks }: { stats: RunStats; tasks: Task[] }) {
  // ticker 1 วิ ให้เวลาที่แสดงเดินสด ไม่ต้องรอรอบ poll
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);

  const total = stats.totalPlanned;
  const finished = Math.max(
    0,
    tasks.filter((t) => FINISHED.has(t.status)).length - stats.baselineFinished,
  );
  const pct = total ? Math.min(100, Math.round((finished / total) * 100)) : 0;
  const elapsedSec = (now - stats.startedAt) / 1000;

  // งานที่กำลัง active ตอนนี้ (orchestrator ทำทีละ task)
  const active = tasks.find((t) =>
    t.status === "assigned" || t.status === "in_progress" || t.status === "review",
  );

  // คาดการณ์เวลา: เฉลี่ยต่อ task ที่จบแล้ว × ที่เหลือ (แสดงได้หลังจบ task แรก)
  let etaText = "กำลังประเมิน… (จะแม่นขึ้นหลังจบงานแรก)";
  if (total > 0 && finished > 0 && finished < total) {
    const eta = (elapsedSec / finished) * (total - finished);
    etaText = `เหลือประมาณ ${fmtDuration(eta)}`;
  } else if (finished >= total && total > 0) {
    etaText = "กำลังสรุปผล…";
  }

  return (
    <div className="card p-3">
      <div className="mb-1.5 flex items-center justify-between text-xs">
        <span className="font-semibold" style={{ color: "var(--text)" }}>
          ⚙ กำลังรัน: {finished}/{total} งาน
          <span className="ml-2 font-normal" style={{ color: "var(--text2)" }}>
            {active
              ? `${PHASE_LABEL[active.status] ?? active.status} — “${active.title}”${
                  active.revision_count > 0 ? ` (แก้รอบที่ ${active.revision_count})` : ""
                }`
              : "กำลังเตรียมงานถัดไป…"}
          </span>
        </span>
        <span style={{ color: "var(--text3)" }}>
          ใช้ไป {fmtDuration(elapsedSec)} · {etaText}
        </span>
      </div>
      <div className="h-2.5 overflow-hidden rounded-full" style={{ background: "#f0f1f8" }}>
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{
            width: `${Math.max(pct, 4)}%`,
            background: "linear-gradient(90deg, var(--claude), var(--gemini))",
          }}
        />
      </div>
      <div className="mt-1 text-right text-[11px] font-semibold" style={{ color: "var(--claude)" }}>
        {pct}%
      </div>
    </div>
  );
}
