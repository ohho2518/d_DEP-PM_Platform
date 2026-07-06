"use client";
// Agent Office — ตัวการ์ตูน AI agent เดินไปมาในออฟฟิศจำลอง แสดงสถานะจริงจาก task บนบอร์ด
// busy = task ของ role นั้นกำลัง active (เดิน+ป้ายงาน) | idle = ยืนจิบกาแฟริมโต๊ะ
import { useEffect, useRef, useState } from "react";
import type { Task } from "@/lib/types";

interface AgentDef {
  role: string;
  label: string;
  emoji: string;
  color: string;
  home: number; // ตำแหน่งยืนพัก (% ของความกว้าง)
}

// ทีมตาม ai-dev-team-complete.html: PM/Orchestrator (Claude), Dev (Codex), SR+Reviewer
const AGENTS: AgentDef[] = [
  { role: "pm", label: "PM · Claude", emoji: "🧑‍💼", color: "var(--claude)", home: 6 },
  { role: "dev", label: "Dev · Codex", emoji: "👨‍💻", color: "var(--codex)", home: 32 },
  { role: "senior_architect", label: "SR · Gemini", emoji: "👷", color: "var(--gemini)", home: 58 },
  { role: "reviewer", label: "Reviewer", emoji: "🕵️", color: "var(--warn)", home: 82 },
];

interface Activity {
  busy: boolean;
  taskTitle?: string;
}

/** สถานะจริงของแต่ละ agent จาก task list (โพลทุก 4 วิจากหน้า board อยู่แล้ว) */
function deriveActivity(tasks: Task[]): Record<string, Activity> {
  const act: Record<string, Activity> = {};
  for (const a of AGENTS) act[a.role] = { busy: false };

  for (const t of tasks) {
    // งานกำลังถูก implement โดย persona ตาม agent_role
    if ((t.status === "assigned" || t.status === "in_progress") && t.agent_role) {
      act[t.agent_role] = { busy: true, taskTitle: t.title };
      act["pm"] = { busy: true, taskTitle: "ประสานงาน: " + t.title }; // PM/orchestrator คุมงานอยู่
    }
    // งานอยู่ในมือ reviewer
    if (t.status === "review") {
      act["reviewer"] = { busy: true, taskTitle: "ตรวจ: " + t.title };
    }
  }
  return act;
}

export default function AgentOffice({ tasks }: { tasks: Task[] }) {
  const activity = deriveActivity(tasks);
  return (
    <div className="card p-3">
      <div className="mb-2 flex items-center justify-between">
        <span className="text-xs font-semibold tracking-wide" style={{ color: "var(--text2)" }}>
          🏢 AGENT OFFICE
        </span>
        <span className="flex items-center gap-3 text-[11px]" style={{ color: "var(--text3)" }}>
          <span className="flex items-center gap-1"><span className="status-dot dot-busy" /> กำลังทำงาน</span>
          <span className="flex items-center gap-1"><span className="status-dot dot-idle" /> ว่าง</span>
        </span>
      </div>
      <div className="office">
        {AGENTS.map((a) => (
          <Actor key={a.role} def={a} activity={activity[a.role]} />
        ))}
      </div>
    </div>
  );
}

function Actor({ def, activity }: { def: AgentDef; activity: Activity }) {
  // ตำแหน่ง (%) — ตอน busy เดินสุ่มไปมา, ตอน idle กลับโต๊ะตัวเอง
  const [pos, setPos] = useState(def.home);
  const [flip, setFlip] = useState(false);
  const posRef = useRef(pos);
  posRef.current = pos;

  useEffect(() => {
    if (!activity.busy) {
      setFlip(posRef.current > def.home);
      setPos(def.home);
      return;
    }
    const id = setInterval(() => {
      // เดินสุ่มรอบ ๆ พื้นที่ตัวเอง (บวกลบ ~18%)
      const target = Math.min(88, Math.max(2, def.home + (Math.random() * 36 - 18)));
      setFlip(target < posRef.current);
      setPos(target);
    }, 900);
    return () => clearInterval(id);
  }, [activity.busy, def.home]);

  return (
    <div
      className={`agent-actor ${activity.busy ? "working" : "idle"} ${flip ? "flip" : ""}`}
      style={{ left: `${pos}%` }}
      title={activity.busy ? activity.taskTitle : `${def.label} — ว่าง`}
    >
      {activity.busy && activity.taskTitle && (
        <span className="agent-bubble">⚙ {activity.taskTitle}</span>
      )}
      <span className="agent-emoji">{activity.busy ? def.emoji : "☕"}</span>
      <span className="agent-name" style={{ background: def.color }}>
        <span className={`status-dot ${activity.busy ? "dot-busy" : "dot-idle"}`} style={{ marginRight: 4, width: 5, height: 5 }} />
        {def.label}
      </span>
    </div>
  );
}
