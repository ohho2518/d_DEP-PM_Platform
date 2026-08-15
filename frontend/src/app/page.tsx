"use client";
// Portfolio View — โทนสีตาม ai-dev-team-complete.html + polling (ADR-04)
import Link from "next/link";
import { useState } from "react";
import { api } from "@/lib/api";
import { CeoInbox } from "@/components/CeoInbox";
import { NextAction, StageBar } from "@/components/StageBar";
import { usePolling } from "@/lib/usePolling";
import { STATUS_ORDER, type IdeaPreview, type ProjectKind, type TaskStatus } from "@/lib/types";

const STATUS_COLORS: Record<TaskStatus, string> = {
  backlog: "#c8cce0",
  planned: "var(--gemini)",
  assigned: "var(--claude)",
  in_progress: "var(--warn)",
  review: "#a06010",
  done: "var(--ok)",
  deployed: "var(--codex)",
  escalated: "var(--danger)",
};

/** ป้ายชนิดงาน — ต้องตรงกับ `constants.ProjectKind` ฝั่ง backend */
const KIND_LABEL: Record<ProjectKind, { text: string; color: string }> = {
  code: { text: "งานมีโค้ด", color: "var(--claude)" },
  doc: { text: "งานเอกสาร", color: "var(--codex)" },
  idea: { text: "💡 ไอเดีย", color: "var(--gemini)" },
};

const AGENT_COLOR: Record<string, string> = {
  anthropic: "var(--claude)",
  openai: "var(--codex)",
  google: "var(--gemini)",
};

export default function PortfolioPage() {
  const { data, error, refresh } = usePolling(api.portfolio);

  if (error)
    return (
      <p className="card p-4 text-sm" style={{ color: "var(--danger)" }}>
        เชื่อมต่อ backend ไม่ได้: {error} — ตรวจว่า uvicorn รันอยู่ที่ NEXT_PUBLIC_API_URL
      </p>
    );
  if (!data) return <p style={{ color: "var(--text2)" }}>กำลังโหลด…</p>;

  return (
    <div className="space-y-8">
      <CeoInbox />

      <IdeaInbox onImported={refresh} />

      <section>
        <div className="mb-4 flex items-center justify-between">
          <h1 className="text-xl font-bold">Portfolio</h1>
          <Link href="/projects/new" className="btn-primary">+ New Project</Link>
        </div>

        {data.projects.length === 0 ? (
          <p
            className="rounded-[14px] border border-dashed p-8 text-center"
            style={{ borderColor: "var(--text3)", color: "var(--text3)" }}
          >
            ยังไม่มีโปรเจกต์ — เริ่มจาก “New Project”
          </p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data.projects.map((p) => (
              <Link key={p.id} href={`/projects/${p.id}`} className="card p-4 transition hover:shadow-md">
                <div className="flex items-start justify-between gap-2">
                  <h2 className="font-semibold">{p.name}</h2>
                  <span className="chip" style={{ color: KIND_LABEL[p.kind].color }}>
                    {KIND_LABEL[p.kind].text}
                  </span>
                </div>

                {/* เส้นทางของโปรเจกต์ — เห็นจากหน้ารวมว่าติดอยู่ขั้นไหน ไม่ต้องเปิดเข้าไปทีละอัน */}
                <div className="mt-3 space-y-1.5">
                  <StageBar pipeline={p.pipeline} compact />
                  <NextAction pipeline={p.pipeline} />
                </div>

                {p.total_tasks > 0 && (
                  <div className="mt-3 flex h-2 overflow-hidden rounded-full" style={{ background: "#f0f1f8" }}>
                    {STATUS_ORDER.map((s) => {
                      const n = p.task_counts[s] ?? 0;
                      if (!n) return null;
                      return (
                        <div
                          key={s}
                          style={{ width: `${(n / p.total_tasks) * 100}%`, background: STATUS_COLORS[s] }}
                          title={`${s}: ${n}`}
                        />
                      );
                    })}
                  </div>
                )}

                <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-[11px]" style={{ color: "var(--text2)" }}>
                  {STATUS_ORDER.filter((s) => p.task_counts[s]).map((s) => (
                    <span key={s}>{s}: {p.task_counts[s]}</span>
                  ))}
                </div>

                <p className="mt-3 text-xs" style={{ color: "var(--text3)" }}>
                  deploy ล่าสุด:{" "}
                  {p.last_deployment
                    ? `${p.last_deployment.status} (${p.last_deployment.environment ?? "-"})`
                    : "ยังไม่มี"}
                </p>
              </Link>
            ))}
          </div>
        )}
      </section>

      <section>
        <h2 className="mb-3 text-xs font-bold uppercase tracking-wide" style={{ color: "var(--text2)" }}>
          AI Dev Team
        </h2>
        <div className="flex flex-wrap gap-3">
          {data.agents.map((a) => (
            <div key={a.id} className="card flex items-center gap-2 rounded-full px-3 py-1.5 text-sm">
              <span
                className={`status-dot ${a.status === "working" ? "dot-busy" : "dot-idle"}`}
              />
              <span className="font-medium">{a.name}</span>
              <span
                className="rounded-full px-2 py-0.5 text-[10px] text-white"
                style={{ background: AGENT_COLOR[a.role === "pm" ? "anthropic" : a.role] ?? "var(--claude)" }}
              >
                {a.role} · {a.mode}
              </span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

/** ไอเดียเก่าที่ยังกองอยู่ในดิสก์ — ดึงขึ้นบอร์ดได้ (มติผู้ใช้ 2026-08-15)
 *  ซ่อนตัวเองเมื่อไม่มีอะไรใหม่ให้ดึง — ไม่รบกวนหน้าจอในวันปกติ */
function IdeaInbox({ onImported }: { onImported: () => void }) {
  const [preview, setPreview] = useState<IdeaPreview | null>(null);
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState<string | null>(null);

  async function look() {
    setBusy(true);
    try {
      setPreview(await api.ideaPreview());
      setOpen(true);
    } catch {
      setPreview(null);
    } finally {
      setBusy(false);
    }
  }

  async function pull() {
    setBusy(true);
    try {
      const created = await api.importIdeas();
      setDone(`ดึงขึ้นบอร์ดแล้ว ${created.length} ไอเดีย`);
      setOpen(false);
      setPreview(null);
      onImported();
    } catch (e) {
      setDone(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card flex flex-col gap-2 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-sm font-semibold">💡 ไอเดียที่เก็บไว้ในเครื่อง</span>
        <button className="btn-ghost" onClick={look} disabled={busy}>
          {busy ? "กำลังดู…" : "ดูว่ามีอะไรบ้าง"}
        </button>
      </div>

      {done && (
        <p className="text-xs" style={{ color: "var(--ok)" }}>{done}</p>
      )}

      {open && preview && (
        <div className="space-y-2">
          <p className="text-xs" style={{ color: "var(--text2)" }}>
            เจอ {preview.found} เรื่อง · อยู่บนบอร์ดแล้ว {preview.already_on_board} ·
            ยังไม่ได้ดึง <b>{preview.items.length}</b>
          </p>
          <p className="font-mono text-[10.5px]" style={{ color: "var(--text3)" }}>
            {preview.roots.join(" · ")}
          </p>
          {preview.items.length > 0 && (
            <>
              <ul className="max-h-48 space-y-1 overflow-y-auto text-xs" style={{ color: "var(--text2)" }}>
                {preview.items.map((i) => (
                  <li key={`${i.source_root}/${i.name}`} className="flex items-center gap-2">
                    <span>{i.is_folder ? "📁" : "📄"}</span>
                    <span className="truncate">{i.name}</span>
                    <span className="chip">{i.updated || "—"}</span>
                  </li>
                ))}
              </ul>
              <div className="flex items-center gap-3">
                <button className="btn-primary" onClick={pull} disabled={busy}>
                  ดึงขึ้นบอร์ดทั้งหมด
                </button>
                <span className="text-[11px]" style={{ color: "var(--text3)" }}>
                  ไฟล์ต้นทางไม่ถูกย้าย/แก้/ลบ · ยิงซ้ำได้ ของเดิมถูกข้าม
                </span>
              </div>
            </>
          )}
        </div>
      )}
    </section>
  );
}
