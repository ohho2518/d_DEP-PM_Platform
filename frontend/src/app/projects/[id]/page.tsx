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
  type DeliverableResult,
  type Project,
  type RunSummary,
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

/** ข้อความสรุปหลังรอบรันจบ — อ่านจากผลจริงที่ backend ส่งมา */
function runNotice(run: RunSummary): string {
  if (run.status === "failed")
    return `❌ รอบรันล้มเหลว: ${run.error ?? "ไม่ทราบสาเหตุ"} (ผลงานที่ทำเสร็จก่อนหน้ายังอยู่)`;
  if (run.status === "cancelled")
    return `⏹ หยุดรอบรันแล้ว — ทำไป ${run.processed}/${run.total} งาน (ที่เสร็จแล้วยังอยู่ครบ กด Run ใหม่เพื่อทำต่อ · ยังไม่ส่งผลกลับเลขา)`;
  if (run.processed === 0) return "ไม่มี task สถานะ planned ให้รัน (ยืนยัน scope ก่อน)";

  const parts = Object.entries(run.counts)
    .map(([k, v]) => `${k}: ${v}`)
    .join(", ");
  // ค้าง = task ที่รอ dependency ซึ่ง escalated ไปแล้ว → ไม่มีวันได้รันในรอบนี้
  const stuck =
    run.total > run.processed ? ` · ค้าง ${run.total - run.processed} งาน (รองานข้างบน)` : "";
  // โปรเจกต์จากเลขา: backend รายงานกลับเข้า QC gate ให้อัตโนมัติเมื่องานจบครบ
  const ceo = run.ceo_report?.reported
    ? " · 📤 ส่งผลกลับเลขาเข้า QC gate แล้ว"
    : run.ceo_report && run.ceo_report.ready === false
      ? ` · (ยังไม่ส่งเลขา: ${run.ceo_report.detail})`
      : "";
  return `✅ เสร็จแล้ว — ${run.processed} tasks (${parts})${stuck}${ceo}`;
}

export default function BoardPage({ params }: { params: Promise<{ id: string }> }) {
  const { id: projectId } = use(params);

  const [selected, setSelected] = useState<Task | null>(null);
  const [run, setRun] = useState<RunSummary | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [reporting, setReporting] = useState(false);

  const running = run?.status === "running";
  const runId = run?.run_id;

  // โหลดครั้งเดียว — ใช้รู้ว่าโปรเจกต์นี้มาจากเลขา (d_CEO) ไหม
  useEffect(() => {
    api.getProject(projectId).then(setProject).catch(() => setProject(null));
  }, [projectId]);

  // รอบรันอยู่ฝั่ง backend แล้ว (Phase 2) — เปิด/รีเฟรชหน้ากลางรอบก็เห็นความคืบหน้าต่อได้
  // 404 = โปรเจกต์นี้ยังไม่เคยรันในโปรเซสนี้
  useEffect(() => {
    api.getRun(projectId).then(setRun).catch(() => setRun(null));
  }, [projectId]);

  // ระหว่างรัน poll ถี่ขึ้น (2 วิ) เพื่อให้ progress/การ์ตูนสดกว่า
  const { data, error, refresh } = usePolling(
    () => api.listTasks(projectId),
    running ? 2000 : 4000,
  );

  // ถามความคืบหน้าของรอบรันจนกว่าจะจบ แล้วค่อยสรุปผลครั้งเดียว
  useEffect(() => {
    if (!running || !runId) return;
    const id = setInterval(async () => {
      try {
        const latest = await api.getRun(projectId, runId);
        setRun(latest);
        if (latest.status !== "running") {
          setNotice(runNotice(latest));
          void refresh();
        }
      } catch {
        // เน็ตสะดุด/backend รีสตาร์ต — ลองใหม่รอบหน้า ไม่ต้องรบกวนผู้ใช้
      }
    }, 2000);
    return () => clearInterval(id);
  }, [running, runId, projectId, refresh]);

  async function moveTask(task: Task, to: TaskStatus) {
    try {
      await api.patchTask(task.id, { status: to });
      await refresh();
    } catch (e) {
      setNotice(e instanceof Error ? e.message : String(e));
    }
  }

  async function runOrchestrator() {
    setNotice(null);
    try {
      // 202 ทันที — งานจริงรันเบื้องหลัง แล้ว useEffect ข้างบนตามความคืบหน้าต่อเอง
      setRun(await api.runOrchestrator(projectId));
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      if (msg.startsWith("409")) {
        // มีรอบรันค้างอยู่ (เช่นเปิดไว้อีกแท็บ) — ดึงรอบนั้นมาแสดงแทนการขึ้น error ดิบ
        setNotice("โปรเจกต์นี้กำลังรันอยู่แล้ว — แสดงความคืบหน้าของรอบที่ค้างอยู่");
        api.getRun(projectId).then(setRun).catch(() => undefined);
        return;
      }
      setNotice(msg);
    }
  }

  async function cancelRun() {
    setNotice("⏹ ขอหยุดแล้ว — รอ task ที่กำลังทำอยู่ให้จบก่อน (ไม่ตัดกลางคันเพื่อไม่ให้งานค้างสถานะ)");
    try {
      setRun(await api.cancelRun(projectId));
    } catch (e) {
      setNotice(e instanceof Error ? e.message : String(e));
    }
  }

  async function reportToCeo() {
    setReporting(true);
    setNotice(null);
    try {
      const result = await api.ceoReport(projectId);
      setNotice(
        result.reported
          ? "📤 ส่งผลงานเข้า QC gate ของเลขาแล้ว (สถานะ qc_review — QC เป็นคนเคาะต่อ)"
          : `ยังไม่ได้ส่ง: ${result.detail}`,
      );
    } catch (e) {
      setNotice(e instanceof Error ? e.message : String(e));
    } finally {
      setReporting(false);
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
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="flex items-center gap-2 text-lg font-bold">
          Kanban{" "}
          <span className="text-sm font-normal" style={{ color: "var(--text3)" }}>
            ({data.pagination.total} tasks)
          </span>
          {project?.ceo_task_id && (
            <span className="chip" title={`d_CEO task ${project.ceo_task_id}`}>
              📥 งานจากเลขา
            </span>
          )}
        </h1>
        <div className="flex gap-2">
          {project?.ceo_task_id && (
            <button onClick={reportToCeo} disabled={reporting || running} className="btn-ghost">
              {reporting ? "กำลังส่ง…" : "📤 ส่งผลกลับเลขา"}
            </button>
          )}
          {running && (
            <button
              onClick={cancelRun}
              disabled={run?.cancel_requested}
              className="btn-ghost"
              title="หยุดหลัง task ที่กำลังทำอยู่จบ — ไม่ตัดกลางคัน"
            >
              {run?.cancel_requested ? "⏹ กำลังหยุด…" : "⏹ หยุดรอบรัน"}
            </button>
          )}
          <button onClick={runOrchestrator} disabled={running} className="btn-primary">
            {running ? "⚙ Agent กำลังทำงาน…" : "▶ Run Agents"}
          </button>
        </div>
      </div>

      {/* ไฟล์ดีไซน์ → requirement → PM แตกงาน (ADR-05 S3) — เฉพาะโปรเจกต์ที่มีโฟลเดอร์จริง */}
      {project?.local_path && (
        <DesignFilesPanel projectId={projectId} folder={project.local_path} onDone={refresh} />
      )}

      {/* ออฟฟิศจำลอง — agent เดินเมื่อกำลังทำงานจริง (สถานะจาก tasks ที่ poll ทุก 4 วิ) */}
      <AgentOffice tasks={data.data} />

      {running && run && <RunProgress run={run} tasks={data.data} />}

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

      {selected && (
        <TaskDetail
          task={selected}
          projectId={projectId}
          canWriteFiles={Boolean(project?.local_path)}
          onClose={() => setSelected(null)}
        />
      )}
    </div>
  );
}

/** อัปโหลดไฟล์ดีไซน์ → ได้ requirement → ส่งให้ PM แตกงาน (ADR-05 S3)
 *  ขั้นอัปโหลด **ไม่เรียก AI** — คนได้อ่านข้อความที่ระบบดึงมาก่อนตัดสินใจส่งต่อ */
function DesignFilesPanel({
  projectId,
  folder,
  onDone,
}: {
  projectId: string;
  folder: string;
  onDone: () => void;
}) {
  const [files, setFiles] = useState<FileList | null>(null);
  const [note, setNote] = useState("");
  const [requirement, setRequirement] = useState<string | null>(null);
  const [saved, setSaved] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);

  async function upload() {
    if (!files?.length) return;
    setBusy(true);
    setError(null);
    try {
      const res = await api.uploadDesignFiles(projectId, Array.from(files), note);
      setSaved(res.saved);
      setRequirement(res.requirement);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function sendToPm() {
    if (!requirement) return;
    setBusy(true);
    setError(null);
    try {
      await api.breakdown(projectId, requirement);
      setRequirement(null);
      setSaved([]);
      onDone();
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card p-4">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between text-sm font-semibold"
      >
        <span>📎 ไฟล์ดีไซน์ → ให้ PM แตกงาน</span>
        <span style={{ color: "var(--text3)" }}>{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <div className="mt-3 space-y-3">
          <p className="font-mono text-[11px]" style={{ color: "var(--text3)" }}>
            เก็บไว้ที่ {folder}\_design_input\ (git ไม่เก็บโฟลเดอร์นี้)
          </p>

          <input
            type="file"
            multiple
            onChange={(e) => setFiles(e.target.files)}
            className="block w-full text-sm"
          />
          <input
            className="input"
            placeholder="โน้ตถึง PM (ไม่บังคับ) — เช่น รอบนี้เอาแค่ 3 หน้าจอแรก"
            value={note}
            onChange={(e) => setNote(e.target.value)}
          />

          <div className="flex flex-wrap items-center gap-2">
            <button className="btn-ghost" onClick={upload} disabled={busy || !files?.length}>
              {busy ? "กำลังอ่านไฟล์…" : "อัปโหลด + อ่านเนื้อหา"}
            </button>
            {requirement && (
              <button className="btn-primary" onClick={sendToPm} disabled={busy}>
                ส่งให้ PM แตกงาน ({requirement.length.toLocaleString()} ตัวอักษร)
              </button>
            )}
          </div>

          {error && (
            <p className="text-sm" style={{ color: "var(--danger)" }}>
              {error}
            </p>
          )}

          {saved.length > 0 && (
            <p className="text-xs" style={{ color: "var(--text2)" }}>
              บันทึกแล้ว: {saved.join(" · ")}
            </p>
          )}

          {requirement && (
            <details open>
              <summary className="cursor-pointer text-sm" style={{ color: "var(--text2)" }}>
                ข้อความที่ระบบอ่านได้ (ตรวจก่อนส่ง)
              </summary>
              <pre
                className="mt-2 max-h-64 overflow-auto rounded-[10px] p-2 text-[11px]"
                style={{ background: "var(--bg)", color: "var(--text2)" }}
              >
                {requirement}
              </pre>
            </details>
          )}
        </div>
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

/** เขียนผลงานของ task ลงไฟล์จริงในโฟลเดอร์โปรเจกต์ (ADR-05 S3)
 *  agent เขียนไฟล์เองไม่ได้ — ขั้นนี้คนกดเอง · ระบบสำรองไฟล์เดิมก่อนทับให้เสมอ */
function WriteToFile({ task, projectId }: { task: Task; projectId: string }) {
  const [path, setPath] = useState("docs/PROJECT_OVERVIEW.md");
  const [result, setResult] = useState<DeliverableResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function write() {
    setBusy(true);
    setError(null);
    try {
      setResult(await api.writeDeliverable(projectId, task.id, path));
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mt-4 border-t pt-3" style={{ borderColor: "var(--border)" }}>
      <p className="mb-2 text-sm font-semibold">เขียนผลงานลงไฟล์</p>
      <div className="flex gap-2">
        <input
          className="input font-mono text-xs"
          value={path}
          onChange={(e) => setPath(e.target.value)}
          placeholder="docs/PROJECT_OVERVIEW.md"
        />
        <button className="btn-ghost whitespace-nowrap" onClick={write} disabled={busy}>
          {busy ? "กำลังเขียน…" : "เขียน"}
        </button>
      </div>
      <p className="mt-1 text-[11px]" style={{ color: "var(--text3)" }}>
        เขียนได้เฉพาะใต้โฟลเดอร์ของโปรเจกต์ · สำรองไฟล์เดิมให้ก่อนทับ · ไม่ commit ให้
      </p>
      {error && (
        <p className="mt-2 text-xs" style={{ color: "var(--danger)" }}>
          {error}
        </p>
      )}
      {result && (
        <p className="mt-2 text-xs" style={{ color: "var(--ok)" }}>
          ✅ เขียนแล้ว {result.bytes.toLocaleString()} ไบต์ → {result.path}
          {result.backup && ` · สำรองของเดิมไว้ที่ ${result.backup}`}
        </p>
      )}
    </div>
  );
}

function TaskDetail({
  task,
  projectId,
  canWriteFiles,
  onClose,
}: {
  task: Task;
  projectId: string;
  canWriteFiles: boolean;
  onClose: () => void;
}) {
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
          {(task.tokens_input > 0 || task.tokens_output > 0) && (
            <div>
              tokens: {task.tokens_input.toLocaleString()} in ·{" "}
              {task.tokens_output.toLocaleString()} out
              {/* แยกตามผู้ให้บริการ — งานเดียวมีได้หลายเจ้า (dev กับ reviewer คนละค่ายได้) */}
              {task.token_usage &&
                Object.entries(task.token_usage).map(([provider, u]) => (
                  <div key={provider} className="pl-3 text-xs" style={{ color: "var(--text3)" }}>
                    ↳ {provider}
                    {u.model ? ` (${u.model})` : ""}: {(u.input ?? 0).toLocaleString()} in ·{" "}
                    {(u.output ?? 0).toLocaleString()} out · {u.calls ?? 0} ครั้ง
                  </div>
                ))}
            </div>
          )}
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

        {canWriteFiles && <WriteToFile task={task} projectId={projectId} />}
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

/** Progress ของรอบ Run Agents — ตัวเลขมาจาก `GET /run` ของ backend (Phase 2)
 *  ส่วนชื่องานที่กำลังทำอ่านจาก task ที่ poll สด เพราะ backend รายงานเป็นราย task ที่ "จบแล้ว" */
function RunProgress({ run, tasks }: { run: RunSummary; tasks: Task[] }) {
  // ticker 1 วิ ให้เวลาที่แสดงเดินสด ไม่ต้องรอรอบ poll
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);

  const total = run.total;
  const finished = run.processed;
  const pct = total ? Math.min(100, Math.round((finished / total) * 100)) : 0;
  const elapsedSec = Math.max(0, (now - new Date(run.started_at).getTime()) / 1000);

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
