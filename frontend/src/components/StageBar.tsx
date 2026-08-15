"use client";
// แถบเส้นทาง 6 ขั้นของโปรเจกต์ — ใช้ทั้งบนบอร์ดและหน้ารวม
// ค่าทุกช่องมาจาก backend (`services/stages.py`) ซึ่งคำนวณสดจากของจริง
// ⚠️ ห้ามคำนวณขั้นเองในฝั่ง frontend — จะกลายเป็นความจริงคนละชุดกับ backend ทันที
import { STAGE_COLOR, type ProjectStages } from "@/lib/types";

export function StageBar({
  pipeline,
  compact = false,
}: {
  pipeline: ProjectStages;
  compact?: boolean;
}) {
  return (
    <div
      className="flex overflow-hidden rounded-[10px] border"
      style={{ borderColor: "var(--border)" }}
    >
      {pipeline.stages.map((s) => {
        const color = STAGE_COLOR[s.stage];
        const filled = s.state !== "todo";
        return (
          <div
            key={s.stage}
            title={s.state === "current" ? `กำลังอยู่ขั้นนี้: ${s.label}` : s.label}
            className={`flex-1 border-r px-1 text-center ${compact ? "py-1" : "py-1.5"}`}
            style={{
              borderColor: "var(--border)",
              background: filled ? color : "var(--surface)",
              // ขั้นที่ทำแล้วจางกว่าขั้นที่กำลังทำ — ตาจะวิ่งไปที่ "ตอนนี้อยู่ไหน" ก่อน
              opacity: s.state === "done" ? 0.55 : 1,
            }}
          >
            <span
              className={`${compact ? "text-[9.5px]" : "text-[10.5px]"} font-bold`}
              style={{ color: filled ? "#fff" : "var(--text3)" }}
            >
              {s.label}
            </span>
          </div>
        );
      })}
    </div>
  );
}

/** บรรทัดเดียวที่บอกว่า "ต้องทำอะไรต่อ" — คู่กับแถบขั้นเสมอ */
export function NextAction({ pipeline }: { pipeline: ProjectStages }) {
  const color = pipeline.current ? STAGE_COLOR[pipeline.current] : "var(--ok)";
  return (
    <span className="flex items-center gap-2 text-xs" style={{ color: "var(--text2)" }}>
      <span className="status-dot" style={{ background: color }} />
      ขั้นต่อไป: {pipeline.next_action}
    </span>
  );
}
