"use client";
// Portfolio View — ภาพรวมทุกโปรเจกต์ (GET /api/portfolio) + polling (ADR-04)
import Link from "next/link";
import { api } from "@/lib/api";
import { usePolling } from "@/lib/usePolling";
import { STATUS_ORDER, type TaskStatus } from "@/lib/types";

const STATUS_COLORS: Record<TaskStatus, string> = {
  backlog: "bg-neutral-600",
  planned: "bg-sky-600",
  assigned: "bg-indigo-600",
  in_progress: "bg-amber-500",
  review: "bg-purple-500",
  done: "bg-emerald-600",
  deployed: "bg-teal-500",
  escalated: "bg-rose-600",
};

export default function PortfolioPage() {
  const { data, error } = usePolling(api.portfolio);

  if (error)
    return (
      <p className="rounded border border-rose-800 bg-rose-950/40 p-4 text-sm text-rose-300">
        เชื่อมต่อ backend ไม่ได้: {error} — ตรวจว่า uvicorn รันอยู่ที่ NEXT_PUBLIC_API_URL
      </p>
    );
  if (!data) return <p className="text-neutral-400">กำลังโหลด…</p>;

  return (
    <div className="space-y-8">
      <section>
        <div className="mb-4 flex items-center justify-between">
          <h1 className="text-xl font-semibold">Portfolio</h1>
          <Link
            href="/projects/new"
            className="rounded bg-emerald-600 px-3 py-1.5 text-sm font-medium hover:bg-emerald-500"
          >
            + New Project
          </Link>
        </div>

        {data.projects.length === 0 ? (
          <p className="rounded border border-dashed border-neutral-700 p-8 text-center text-neutral-500">
            ยังไม่มีโปรเจกต์ — เริ่มจาก “New Project”
          </p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data.projects.map((p) => (
              <Link
                key={p.id}
                href={`/projects/${p.id}`}
                className="rounded-lg border border-neutral-800 bg-neutral-900 p-4 transition hover:border-emerald-700"
              >
                <div className="flex items-start justify-between">
                  <h2 className="font-medium">{p.name}</h2>
                  <span className="rounded bg-neutral-800 px-2 py-0.5 text-xs text-neutral-400">
                    {p.type}
                  </span>
                </div>
                <p className="mt-1 text-xs text-neutral-500">
                  {p.total_tasks} tasks · status: {p.status}
                </p>

                {/* แถบสัดส่วน task ต่อสถานะ */}
                {p.total_tasks > 0 && (
                  <div className="mt-3 flex h-2 overflow-hidden rounded-full bg-neutral-800">
                    {STATUS_ORDER.map((s) => {
                      const n = p.task_counts[s] ?? 0;
                      if (!n) return null;
                      return (
                        <div
                          key={s}
                          className={STATUS_COLORS[s]}
                          style={{ width: `${(n / p.total_tasks) * 100}%` }}
                          title={`${s}: ${n}`}
                        />
                      );
                    })}
                  </div>
                )}

                <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-neutral-400">
                  {STATUS_ORDER.filter((s) => p.task_counts[s]).map((s) => (
                    <span key={s}>
                      {s}: {p.task_counts[s]}
                    </span>
                  ))}
                </div>

                <p className="mt-3 text-xs text-neutral-500">
                  deploy ล่าสุด:{" "}
                  {p.last_deployment
                    ? `${p.last_deployment.status} (${p.last_deployment.environment ?? "-"})`
                    : "ยังไม่มี (Sprint 4)"}
                </p>
              </Link>
            ))}
          </div>
        )}
      </section>

      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-neutral-400">
          Agents
        </h2>
        <div className="flex flex-wrap gap-3">
          {data.agents.map((a) => (
            <div
              key={a.id}
              className="flex items-center gap-2 rounded-full border border-neutral-800 bg-neutral-900 px-3 py-1.5 text-sm"
            >
              <span
                className={`h-2 w-2 rounded-full ${
                  a.status === "working"
                    ? "bg-amber-400"
                    : a.status === "error"
                      ? "bg-rose-500"
                      : "bg-emerald-500"
                }`}
              />
              {a.name}
              <span className="text-xs text-neutral-500">
                {a.role} · {a.mode}
              </span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
