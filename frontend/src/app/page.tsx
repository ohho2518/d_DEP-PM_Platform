"use client";
// Portfolio View — โทนสีตาม ai-dev-team-complete.html + polling (ADR-04)
import Link from "next/link";
import { api } from "@/lib/api";
import { usePolling } from "@/lib/usePolling";
import { STATUS_ORDER, type TaskStatus } from "@/lib/types";

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

const AGENT_COLOR: Record<string, string> = {
  anthropic: "var(--claude)",
  openai: "var(--codex)",
  google: "var(--gemini)",
};

export default function PortfolioPage() {
  const { data, error } = usePolling(api.portfolio);

  if (error)
    return (
      <p className="card p-4 text-sm" style={{ color: "var(--danger)" }}>
        เชื่อมต่อ backend ไม่ได้: {error} — ตรวจว่า uvicorn รันอยู่ที่ NEXT_PUBLIC_API_URL
      </p>
    );
  if (!data) return <p style={{ color: "var(--text2)" }}>กำลังโหลด…</p>;

  return (
    <div className="space-y-8">
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
                <div className="flex items-start justify-between">
                  <h2 className="font-semibold">{p.name}</h2>
                  <span className="chip">{p.type}</span>
                </div>
                <p className="mt-1 text-xs" style={{ color: "var(--text3)" }}>
                  {p.total_tasks} tasks · status: {p.status}
                </p>

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
