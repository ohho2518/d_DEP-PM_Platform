"use client";
// New Project Onboarding (Blueprint §6 STEP 1-4):
// กรอกข้อมูล → (new) ส่ง requirement ให้ PM Agent แตกงาน / (existing) สั่ง scan
// → เห็น task plan → ยืนยัน scope → ไปที่บอร์ด
import { useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api";
import type { BootstrapResult, ProjectKind, ProjectRelation, Task } from "@/lib/types";

/** ชนิดงาน — ตัดสินว่าเส้นทาง 6 ขั้นเปิดขั้นไหนบ้าง (ต้องตรงกับ `constants.ProjectKind`) */
const KINDS: { value: ProjectKind; label: string; hint: string }[] = [
  { value: "code", label: "งานมีโค้ด", hint: "ครบทุกขั้น — จบที่ deploy ขึ้นระบบจริง" },
  { value: "doc", label: "งานเอกสาร", hint: "ไม่มีโครงโค้ด — ขั้นสุดท้ายคือส่งมอบไฟล์" },
  { value: "idea", label: "💡 ไอเดีย (เก็บไว้ต่อยอด)", hint: "ยังไม่ลงมือ — ยกระดับเป็นโปรเจกต์จริงทีหลังได้" },
];

type Step = "form" | "plan" | "confirming" | "bootstrapped";

/** ชั้นความเกี่ยวข้องกับ ecosystem — ต้องตรงกับ RELATION_LABELS ใน services/scaffold.py */
const RELATIONS: { value: ProjectRelation; label: string }[] = [
  { value: "general", label: "งานทั่วไป (ไม่ใช่งานพัฒนาโค้ด)" },
  { value: "product", label: "Product — งาน Dev Team" },
  { value: "service", label: "Service — งานบริการลูกค้า tailor-made" },
  { value: "middleware", label: "Middleware/Engine กลาง (OCR, STT, PDF …)" },
  { value: "eco-team", label: "Ecosystem — เครื่องมือของทีม (+ contract d_CEO)" },
  { value: "eco-core", label: "Ecosystem — แกนกลาง d_CEO/d_Jarvis (+ contract)" },
];

export default function NewProjectPage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>("form");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [kind, setKind] = useState<ProjectKind>("code");
  const [type, setType] = useState<"new" | "existing" | "bootstrap">("new");
  const [repoUrl, setRepoUrl] = useState("");
  const [requirement, setRequirement] = useState("");

  // โหมด bootstrap — สร้างโฟลเดอร์จริงบนดิสก์ (ADR-05)
  const [target, setTarget] = useState("D:\\Dev_Proj\\");
  const [purpose, setPurpose] = useState("");
  const [stack, setStack] = useState("");
  const [relation, setRelation] = useState<ProjectRelation>("general");
  const [isPython, setIsPython] = useState(true);
  const [manifest, setManifest] = useState<BootstrapResult | null>(null);

  const [projectId, setProjectId] = useState<string | null>(null);
  const [plan, setPlan] = useState<Task[]>([]);
  const [source, setSource] = useState<string>("");

  async function submitBootstrap() {
    const result = await api.bootstrapProject({
      name,
      target,
      purpose,
      stack,
      relation,
      is_python: isPython,
    });
    setManifest(result);
    setProjectId(result.project.id);
    setStep("bootstrapped");
  }

  async function submitForm(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (type === "bootstrap") {
        await submitBootstrap();
        return;
      }
      const project = await api.createProject({
        name,
        type,
        kind,
        ...(type === "existing" ? { repo_url: repoUrl } : {}),
      });
      setProjectId(project.id);

      // ไอเดียยังไม่ต้องแตกงาน — เก็บโจทย์ไว้ก่อน แล้วค่อยยกระดับเมื่อพร้อมทำจริง
      if (kind === "idea") {
        router.push(`/projects/${project.id}`);
        return;
      }

      if (type === "new") {
        const res = await api.breakdown(project.id, requirement);
        setPlan(res.tasks);
        setSource(res.source);
      } else {
        await api.scan(project.id);
        const tasks = await api.listTasks(project.id);
        setPlan(tasks.data);
        setSource("scan (mock)");
      }
      setStep("plan");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function confirmScope() {
    if (!projectId) return;
    setStep("confirming");
    try {
      await api.confirmScope(projectId);
      router.push(`/projects/${projectId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setStep("plan");
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="text-xl font-bold">New Project</h1>

      {error && (
        <p className="card p-3 text-sm" style={{ color: "var(--danger)" }}>
          {error}
        </p>
      )}

      {step === "form" && (
        <form onSubmit={submitForm} className="space-y-4">
          <label className="block">
            <span className="mb-1 block text-sm" style={{ color: "var(--text2)" }}>ชื่อโปรเจกต์</span>
            <input
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="input"
              placeholder="เช่น dPRO AI Parking v2"
            />
          </label>

          {/* ชนิดงาน — ตัดสินเส้นทางของโปรเจกต์นี้ (ก้อนที่ 1 ของการรื้อ UI 2026-08-15) */}
          <div className="space-y-1.5">
            <span className="block text-sm" style={{ color: "var(--text2)" }}>
              งานนี้เป็นแบบไหน
            </span>
            <div className="flex flex-wrap gap-2">
              {KINDS.map((k) => (
                <button
                  type="button"
                  key={k.value}
                  onClick={() => setKind(k.value)}
                  title={k.hint}
                  className={kind === k.value ? "btn-primary" : "btn-ghost"}
                >
                  {k.label}
                </button>
              ))}
            </div>
            <span className="block text-xs" style={{ color: "var(--text3)" }}>
              {KINDS.find((k) => k.value === kind)?.hint}
            </span>
          </div>

          {kind === "idea" ? (
            <p className="text-xs" style={{ color: "var(--text3)" }}>
              ไอเดียจะถูกเก็บขึ้นบอร์ดเฉย ๆ <b>ยังไม่เรียก AI และยังไม่แตกงาน</b> —
              เปิดดูแล้วสั่งให้ช่วยหาข้อมูลต่อได้ พอพร้อมค่อยกด &ldquo;ยกระดับเป็นโปรเจกต์จริง&rdquo;
            </p>
          ) : (
          <>
          <div className="flex flex-col gap-2 text-sm">
            {(
              [
                ["new", "โปรเจกต์ใหม่ (PM Agent แตกงาน)"],
                ["bootstrap", "เปิดโปรเจกต์ใหม่ของจริง — สร้างโฟลเดอร์ + เอกสารกำกับ + git"],
                ["existing", "โปรเจกต์เดิม (scan repo — mock)"],
              ] as const
            ).map(([value, label]) => (
              <label key={value} className="flex items-center gap-2">
                <input
                  type="radio"
                  checked={type === value}
                  onChange={() => setType(value)}
                  style={{ accentColor: "var(--claude)" }}
                />
                {label}
              </label>
            ))}
          </div>

          {type === "bootstrap" ? (
            <div className="space-y-4">
              <label className="block">
                <span className="mb-1 block text-sm" style={{ color: "var(--text2)" }}>
                  โฟลเดอร์ปลายทาง (ต้องอยู่ใต้ D:\Dev_Proj)
                </span>
                <input
                  required
                  value={target}
                  onChange={(e) => setTarget(e.target.value)}
                  className="input font-mono text-sm"
                  placeholder="D:\Dev_Proj\4_RND\d_ProjectName"
                />
              </label>

              <label className="block">
                <span className="mb-1 block text-sm" style={{ color: "var(--text2)" }}>
                  Purpose (ไปอยู่ใน AGENTS.md §3)
                </span>
                <input value={purpose} onChange={(e) => setPurpose(e.target.value)} className="input" />
              </label>

              <label className="block">
                <span className="mb-1 block text-sm" style={{ color: "var(--text2)" }}>
                  Tech stack (ไปอยู่ใน AGENTS.md §4)
                </span>
                <input
                  value={stack}
                  onChange={(e) => setStack(e.target.value)}
                  className="input"
                  placeholder="เช่น Python 3.12 + FastAPI + SQLite"
                />
              </label>

              <label className="block">
                <span className="mb-1 block text-sm" style={{ color: "var(--text2)" }}>
                  ความเกี่ยวข้องกับ ecosystem (กำหนดว่าจะได้เอกสารชุดไหน)
                </span>
                <select
                  value={relation}
                  onChange={(e) => setRelation(e.target.value as ProjectRelation)}
                  className="input"
                >
                  {RELATIONS.map((r) => (
                    <option key={r.value} value={r.value}>
                      {r.label}
                    </option>
                  ))}
                </select>
              </label>

              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={isPython}
                  onChange={(e) => setIsPython(e.target.checked)}
                />
                เป็นงาน Python (เขียน requirements.txt + .env.example ให้)
              </label>

              <p className="text-xs" style={{ color: "var(--text3)" }}>
                ขั้นนี้ <b>ไม่เรียก AI เลย</b> — ได้โฟลเดอร์ + เอกสารกำกับ + git init เสมอ ·
                <b>ไม่ commit ให้</b> คุณตรวจเองก่อน · การเติมเนื้อหาเอกสารเป็นงานบนบอร์ดคนละขั้น
              </p>
            </div>
          ) : type === "new" ? (
            <label className="block">
              <span className="mb-1 block text-sm" style={{ color: "var(--text2)" }}>
                Requirement (PM Agent จะแตกเป็น task plan)
              </span>
              <textarea
                required
                rows={6}
                value={requirement}
                onChange={(e) => setRequirement(e.target.value)}
                className="input"
                placeholder="อธิบายสิ่งที่ต้องการสร้าง…"
              />
            </label>
          ) : (
            <label className="block">
              <span className="mb-1 block text-sm" style={{ color: "var(--text2)" }}>Repo URL</span>
              <input
                required
                type="url"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                className="input"
                placeholder="https://github.com/org/repo"
              />
            </label>
          )}
          </>
          )}

          <button
            disabled={busy}
            className="btn-primary"
          >
            {kind === "idea"
              ? busy
                ? "กำลังเก็บ…"
                : "เก็บไอเดียขึ้นบอร์ด"
              : busy
                ? type === "bootstrap"
                  ? "กำลังสร้างโฟลเดอร์…"
                  : "กำลังสร้าง task plan…"
                : type === "bootstrap"
                  ? "สร้างโปรเจกต์จริง + ลงบอร์ด"
                  : "สร้างโปรเจกต์ + แตกงาน"}
          </button>
        </form>
      )}

      {step === "bootstrapped" && manifest && (
        <div className="space-y-4">
          <div className="card p-4">
            <h2 className="font-semibold">สร้างเรียบร้อย</h2>
            <p className="mt-1 font-mono text-xs" style={{ color: "var(--text2)" }}>
              {manifest.target}
            </p>
            <ul className="mt-3 space-y-1 text-sm" style={{ color: "var(--text2)" }}>
              {manifest.steps.map((s, i) => (
                <li key={i}>· {s}</li>
              ))}
            </ul>
            <details className="mt-3 text-sm">
              <summary style={{ color: "var(--text3)" }}>
                ไฟล์ที่สร้าง ({manifest.created.length})
              </summary>
              <p className="mt-2 font-mono text-xs" style={{ color: "var(--text2)" }}>
                {manifest.created.join(" · ")}
              </p>
            </details>
          </div>

          <p className="text-sm" style={{ color: "var(--text2)" }}>
            ยังไม่ commit ให้ — เปิดโฟลเดอร์ตรวจก่อน แล้ว commit เองตามปกติ ·
            บนบอร์ดมี task <b>&quot;Sign-off เอกสารกำกับก่อนเริ่มงาน&quot;</b> รออยู่แล้ว
          </p>

          <button onClick={() => router.push(`/projects/${projectId}`)} className="btn-primary">
            ไปที่บอร์ด
          </button>
        </div>
      )}

      {(step === "plan" || step === "confirming") && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">
              Task Plan{" "}
              <span className="text-xs" style={{ color: "var(--text3)" }}>
                (source: {source}
                {source === "fallback" && " — ไม่มี ANTHROPIC_API_KEY จึงได้ task เดียว"})
              </span>
            </h2>
            <span className="text-sm" style={{ color: "var(--text2)" }}>{plan.length} tasks</span>
          </div>

          <ul className="space-y-2">
            {plan.map((t) => (
              <li
                key={t.id}
                className="card p-3 text-sm"
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium">{t.title}</span>
                  <span className="chip">
                    {t.priority}
                    {t.estimate_points ? ` · ${t.estimate_points}pt` : ""}
                  </span>
                </div>
                {t.description && (
                  <p className="mt-1" style={{ color: "var(--text2)" }}>{t.description}</p>
                )}
                {t.spec && <p className="mt-1 text-xs" style={{ color: "var(--text3)" }}>spec: {t.spec}</p>}
              </li>
            ))}
          </ul>

          <div className="flex gap-3">
            <button
              onClick={confirmScope}
              disabled={step === "confirming"}
              className="btn-primary"
            >
              {step === "confirming" ? "กำลังยืนยัน…" : "ยืนยัน scope → เข้าบอร์ด"}
            </button>
            {projectId && (
              <button
                onClick={() => router.push(`/projects/${projectId}`)}
                className="btn-ghost"
              >
                ข้ามไปดูบอร์ด (ยังไม่ยืนยัน)
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
