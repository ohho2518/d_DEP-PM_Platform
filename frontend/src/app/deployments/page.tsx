"use client";
// Deployments View — ประวัติ deploy ทุกโปรเจกต์ (ใหม่ล่าสุดก่อน) + polling (ADR-04)
import Link from "next/link";
import { api } from "@/lib/api";
import { usePolling } from "@/lib/usePolling";
import type { DeploymentStatus } from "@/lib/types";

const STATUS_COLORS: Record<DeploymentStatus, string> = {
  queued: "#c8cce0",
  running: "var(--warn)",
  success: "var(--ok)",
  failed: "var(--danger)",
};

export default function DeploymentsPage() {
  const { data, error } = usePolling(() => api.listDeployments());

  if (error)
    return (
      <p className="card p-4 text-sm" style={{ color: "var(--danger)" }}>
        เชื่อมต่อ backend ไม่ได้: {error} — ตรวจว่า uvicorn รันอยู่ที่ NEXT_PUBLIC_API_URL
      </p>
    );
  if (!data) return <p style={{ color: "var(--text2)" }}>กำลังโหลด…</p>;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Deployments</h1>
        <span className="text-xs" style={{ color: "var(--text3)" }}>
          ทั้งหมด {data.pagination.total} รายการ
        </span>
      </div>

      {data.data.length === 0 ? (
        <p
          className="rounded-[14px] border border-dashed p-8 text-center"
          style={{ borderColor: "var(--text3)", color: "var(--text3)" }}
        >
          ยังไม่มี deployment — จะเกิดเมื่อ task done (auto) หรือสั่ง deploy เอง
        </p>
      ) : (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr
                className="text-left text-[11px] uppercase tracking-wide"
                style={{ color: "var(--text3)" }}
              >
                <th className="px-4 py-3">สถานะ</th>
                <th className="px-4 py-3">โปรเจกต์</th>
                <th className="px-4 py-3">Task</th>
                <th className="px-4 py-3">Environment</th>
                <th className="px-4 py-3">Trigger</th>
                <th className="px-4 py-3">Commit</th>
                <th className="px-4 py-3">เวลา</th>
              </tr>
            </thead>
            <tbody>
              {data.data.map((d) => (
                <tr key={d.id} className="border-t" style={{ borderColor: "var(--border)" }}>
                  <td className="px-4 py-3">
                    <span
                      className="rounded-full px-2 py-0.5 text-[11px] font-medium text-white"
                      style={{ background: STATUS_COLORS[d.status] }}
                    >
                      {d.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <Link
                      href={`/projects/${d.project_id}`}
                      className="font-medium hover:opacity-70"
                    >
                      {d.project_name ?? d.project_id.slice(0, 8)}
                    </Link>
                  </td>
                  <td className="px-4 py-3" style={{ color: "var(--text2)" }}>
                    {d.task_title ?? "-"}
                  </td>
                  <td className="px-4 py-3">
                    <span className="chip">{d.environment ?? "-"}</span>
                  </td>
                  <td className="px-4 py-3" style={{ color: "var(--text2)" }}>
                    {d.triggered_by}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs" style={{ color: "var(--text2)" }}>
                    {d.commit_sha ? d.commit_sha.slice(0, 8) : "-"}
                  </td>
                  <td className="px-4 py-3 text-xs" style={{ color: "var(--text3)" }}>
                    {new Date(d.created_at).toLocaleString("th-TH")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
