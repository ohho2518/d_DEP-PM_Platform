"use client";
// งานที่เลขา (d_CEO) delegate มาให้ทีม R&D — DEP-PM รับงานที่นี่ (AGENTS.md §3.1)
// manual pull โดยตั้งใจ: ผู้ใช้กดเอง ตามหลัก "ยืนยันก่อนทำ" ของ ecosystem
import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { CeoInboxItem, CeoStatus } from "@/lib/types";

/** d_CEO คืนเวลาเป็น UTC — ต้องแปลงเป็นเวลาไทยตอนแสดงผล (contract §1) */
function bangkokTime(iso: string): string {
  if (!iso) return "-";
  const utc = iso.endsWith("Z") || iso.includes("+") ? iso : `${iso}Z`;
  const parsed = new Date(utc);
  if (Number.isNaN(parsed.getTime())) return iso;
  return parsed.toLocaleString("th-TH", { timeZone: "Asia/Bangkok", dateStyle: "short", timeStyle: "short" });
}

export function CeoInbox() {
  const router = useRouter();
  const [status, setStatus] = useState<CeoStatus | null>(null);
  const [items, setItems] = useState<CeoInboxItem[]>([]);
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const s = await api.ceoStatus();
      setStatus(s);
      setItems(s.enabled && s.online ? (await api.ceoInbox()).data : []);
    } catch (err) {
      setNote(err instanceof Error ? err.message : String(err));
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function pull(taskIds: string[] = []) {
    setBusy(true);
    setNote(null);
    try {
      const result = await api.ceoPull(taskIds);
      if (result.count === 0) {
        setNote("ไม่มีงานใหม่ให้ดึง");
      } else {
        const failed = result.pulled.filter((p) => !p.acknowledged);
        setNote(
          `รับงาน ${result.count} รายการ (แตกเป็น ${result.pulled.reduce((n, p) => n + p.task_count, 0)} task)` +
            (failed.length ? ` — แจ้งกลับ d_CEO ไม่สำเร็จ ${failed.length} รายการ` : ""),
        );
        if (result.count === 1) router.push(`/projects/${result.pulled[0].project_id}`);
      }
      await refresh();
    } catch (err) {
      setNote(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  // ยังไม่ตั้งค่าเชื่อม d_CEO = ไม่ต้องรบกวนหน้าจอเลย
  if (!status?.enabled) return null;

  return (
    <section className="card p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className={`status-dot ${status.online ? "dot-idle" : "dot-busy"}`} />
          <h2 className="font-semibold">📥 งานจากเลขา</h2>
          <span className="chip">{status.team_name}</span>
        </div>
        <button
          className="btn-primary"
          disabled={busy || !status.online || items.length === 0}
          onClick={() => void pull()}
        >
          {busy ? "กำลังรับงาน…" : `ดึงงานทั้งหมด (${items.length})`}
        </button>
      </div>

      {!status.online && (
        <p className="mt-2 text-xs" style={{ color: "var(--text3)" }}>
          🧠 สมองออฟไลน์ — d_CEO ที่ {status.base_url ?? "127.0.0.1:8000"} ไม่ตอบ
          (ระบบยังใช้งานส่วนอื่นได้ตามปกติ)
        </p>
      )}

      {status.online && items.length === 0 && (
        <p className="mt-2 text-xs" style={{ color: "var(--text3)" }}>
          ไม่มีงานรออยู่ — เลขายังไม่ได้มอบงานให้ทีม R&D
        </p>
      )}

      {items.length > 0 && (
        <ul className="mt-3 space-y-2">
          {items.map((item) => (
            <li
              key={item.id}
              className="flex items-start justify-between gap-3 rounded-[10px] p-2"
              style={{ background: "#f8f9ff" }}
            >
              <div className="min-w-0">
                <p className="truncate text-sm font-medium">{item.input_text.split("\n")[0]}</p>
                <p className="text-[11px]" style={{ color: "var(--text3)" }}>
                  {bangkokTime(item.created_at)} · {item.id.slice(0, 8)}
                </p>
              </div>
              <button className="btn-ghost shrink-0" disabled={busy} onClick={() => void pull([item.id])}>
                รับงานนี้
              </button>
            </li>
          ))}
        </ul>
      )}

      {note && (
        <p className="mt-3 text-xs" style={{ color: "var(--text2)" }}>
          {note}
        </p>
      )}
    </section>
  );
}
