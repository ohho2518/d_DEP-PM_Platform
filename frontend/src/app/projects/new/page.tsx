"use client";
// New Project Onboarding (Blueprint §6 STEP 1-4):
// กรอกข้อมูล → (new) ส่ง requirement ให้ PM Agent แตกงาน / (existing) สั่ง scan
// → เห็น task plan → ยืนยัน scope → ไปที่บอร์ด
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import type {
  BootstrapResult,
  ProjectKind,
  ProjectRelation,
  ScaffoldOptions,
  Task,
} from "@/lib/types";

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

/** ชั้นที่ติ๊ก "เป็น Product/Service ด้วย" ได้ — ต้องตรงกับ `_DUAL_PS_RELATIONS` ฝั่ง backend */
const DUAL_PS_RELATIONS: ProjectRelation[] = ["eco-team", "middleware"];

/** รากสำรองตอนที่ยังโหลด scaffold-options ไม่เสร็จ (หรือ backend ตอบไม่ได้) */
const FALLBACK_ROOT = "D:\\Dev_Proj";

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
  const [options, setOptions] = useState<ScaffoldOptions | null>(null);
  const [teamDir, setTeamDir] = useState("");
  /** ผู้ใช้พิมพ์ path เอง = หยุดประกอบให้อัตโนมัติ (เลือกทีมใหม่ = กลับมา auto) */
  const [typedTarget, setTypedTarget] = useState("");
  const [targetTouched, setTargetTouched] = useState(false);
  const [purpose, setPurpose] = useState("");
  const [stack, setStack] = useState("");
  const [relation, setRelation] = useState<ProjectRelation>("general");
  const [ecoTeam, setEcoTeam] = useState("");
  const [dualPs, setDualPs] = useState(false);
  const [isPython, setIsPython] = useState(true);
  const [designFiles, setDesignFiles] = useState<File[]>([]);
  const [manifest, setManifest] = useState<BootstrapResult | null>(null);
  const [savedDesign, setSavedDesign] = useState<string[]>([]);
  const [designError, setDesignError] = useState<string | null>(null);
  const [commitMsg, setCommitMsg] = useState<string | null>(null);
  const [committing, setCommitting] = useState(false);

  const [projectId, setProjectId] = useState<string | null>(null);
  const [plan, setPlan] = useState<Task[]>([]);
  const [source, setSource] = useState<string>("");

  const root = options?.allowed_root ?? FALLBACK_ROOT;

  // ราก + โฟลเดอร์ทีมมาจาก backend เสมอ (เปลี่ยน SCAFFOLD_ALLOWED_ROOT แล้วฟอร์มตามทันที)
  // ตั้งค่าเริ่มต้นเป็น _INBOX เหมือน new-project-studio — ที่พักของใหม่ที่ยังไม่รู้ทีม
  useEffect(() => {
    let alive = true;
    api
      .scaffoldOptions()
      .then((opts) => {
        if (!alive) return;
        setOptions(opts);
        if (opts.teams.some((t) => t.name === opts.inbox)) setTeamDir(opts.inbox);
      })
      .catch(() => {
        /* โหลดไม่ได้ = พิมพ์ path เองเหมือนเดิม ไม่ต้องขึ้น error ทั้งหน้า */
      });
    return () => {
      alive = false;
    };
  }, []);

  // `<ราก>\<ทีม>\<ชื่อโปรเจกต์>` — คิดสดตอน render (ไม่เก็บเป็น state คู่ขนาน ไม่งั้นต้องมี
  // effect คอยไล่ให้ตรงกันเอง) · ทีมว่าง = วางที่ราก ซึ่ง backend เตือนให้เองใน steps
  const target = targetTouched
    ? typedTarget
    : `${root}${teamDir ? `\\${teamDir}` : ""}\\${name.trim()}`;

  async function submitBootstrap() {
    const result = await api.bootstrapProject({
      name,
      target,
      // ชนิดงานที่เลือกไว้ข้างบน — เส้นทาง 6 ขั้นของโปรเจกต์ขึ้นกับค่านี้
      // (`idea` มาไม่ถึงตรงนี้: เลือกไอเดียแล้วฟอร์มจะไม่มีโหมด bootstrap ให้เลือก)
      kind: kind === "idea" ? "code" : kind,
      purpose,
      stack,
      relation,
      is_python: isPython,
      team: relation === "eco-team" ? ecoTeam : "",
      dual_ps: DUAL_PS_RELATIONS.includes(relation) ? dualPs : false,
    });
    setManifest(result);
    setProjectId(result.project.id);

    // ไฟล์ดีไซน์ที่แนบมาตอนเปิดโปรเจกต์ → `_design_input/` (ยังไม่เรียก AI — ส่งให้ PM ที่บอร์ด)
    // แนบไม่สำเร็จต้อง**ไม่กลบ**ความจริงว่าโฟลเดอร์ถูกสร้างไปแล้ว
    if (designFiles.length) {
      try {
        const uploaded = await api.uploadDesignFiles(result.project.id, designFiles);
        setSavedDesign(uploaded.saved);
      } catch (err) {
        setDesignError(err instanceof Error ? err.message : String(err));
      }
    }
    setStep("bootstrapped");
  }

  async function commitNow() {
    if (!projectId) return;
    setCommitting(true);
    setCommitMsg(null);
    try {
      const res = await api.commitProject(projectId);
      setCommitMsg(`✅ ${res.detail}`);
    } catch (err) {
      setCommitMsg(`❌ ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setCommitting(false);
    }
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
                  ทีมเจ้าของ (โฟลเดอร์ปลายทาง)
                </span>
                <select
                  value={teamDir}
                  onChange={(e) => {
                    // เลือกทีม = สั่งชัดเจน → กลับมาประกอบ path ให้อัตโนมัติอีกครั้ง
                    setTeamDir(e.target.value);
                    setTargetTouched(false);
                  }}
                  className="input"
                >
                  <option value="">
                    {options?.teams.length
                      ? "— พิมพ์ path เอง (วางที่ราก ผิดกฎจัดระเบียบ) —"
                      : "— พิมพ์ path เอง —"}
                  </option>
                  {options?.teams.map((t) => (
                    <option key={t.name} value={t.name}>
                      {t.hint ? `${t.name} — ${t.hint}` : t.name}
                    </option>
                  ))}
                </select>
                {teamDir && (
                  <span className="mt-1 block font-mono text-xs" style={{ color: "var(--text3)" }}>
                    📁 {root}\{teamDir}
                  </span>
                )}
              </label>

              <label className="block">
                <span className="mb-1 block text-sm" style={{ color: "var(--text2)" }}>
                  โฟลเดอร์ปลายทาง (ต้องอยู่ใต้ {root})
                </span>
                <input
                  required
                  value={target}
                  onChange={(e) => {
                    setTypedTarget(e.target.value);
                    setTargetTouched(true);
                  }}
                  className="input font-mono text-sm"
                  placeholder={`${root}\\4_RND\\d_ProjectName`}
                />
                <span className="mt-1 block text-xs" style={{ color: "var(--text3)" }}>
                  {targetTouched
                    ? "พิมพ์เอง — เลือกทีมใหม่เมื่อไหร่ ระบบจะกลับมาประกอบ path ให้"
                    : "ประกอบให้จาก ทีม + ชื่อโปรเจกต์ — แก้เองได้"}
                </span>
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

              {relation === "eco-team" && (
                <label className="block">
                  <span className="mb-1 block text-sm" style={{ color: "var(--text2)" }}>
                    สังกัดทีมไหนใน ecosystem (ต่อท้ายบรรทัด Ecosystem ใน AGENTS.md)
                  </span>
                  <input
                    value={ecoTeam}
                    onChange={(e) => setEcoTeam(e.target.value)}
                    className="input"
                    placeholder="เช่น Marketing Team — d_MOS"
                  />
                </label>
              )}

              {DUAL_PS_RELATIONS.includes(relation) && (
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={dualPs}
                    onChange={(e) => setDualPs(e.target.checked)}
                  />
                  ตัวนี้เป็น Product/Service ด้วย (ขาย/ให้บริการภายนอก)
                </label>
              )}

              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={isPython}
                  onChange={(e) => setIsPython(e.target.checked)}
                />
                เป็นงาน Python (เขียน requirements.txt + .env.example ให้)
              </label>

              <DesignDropZone files={designFiles} onChange={setDesignFiles} />

              <p className="text-xs" style={{ color: "var(--text3)" }}>
                ขั้นนี้ <b>ไม่เรียก AI เลย</b> — ได้โฟลเดอร์ + เอกสารกำกับ + git init เสมอ ·
                <b>ไม่ commit ให้</b> คุณตรวจเองก่อน (มีปุ่ม commit ให้กดหลังตรวจ) ·
                การเติมเนื้อหาเอกสารเป็นงานบนบอร์ดคนละขั้น
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
            {savedDesign.length > 0 && (
              <p className="mt-3 text-sm" style={{ color: "var(--text2)" }}>
                📎 ไฟล์ดีไซน์ที่เก็บไว้ใน <span className="font-mono text-xs">_design_input\</span>:{" "}
                {savedDesign.join(", ")} —{" "}
                <span style={{ color: "var(--text3)" }}>
                  ส่งให้ PM แตกงานได้ที่แผง &ldquo;ไฟล์ดีไซน์&rdquo; บนบอร์ด
                </span>
              </p>
            )}
            {designError && (
              <p className="mt-3 text-sm" style={{ color: "var(--danger)" }}>
                ⚠️ โฟลเดอร์สร้างเรียบร้อยแล้ว แต่แนบไฟล์ดีไซน์ไม่สำเร็จ: {designError}
                <br />
                ลองแนบใหม่ได้ที่แผง &ldquo;ไฟล์ดีไซน์&rdquo; บนบอร์ด
              </p>
            )}
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
            ยังไม่ commit ให้ — เปิดโฟลเดอร์ตรวจช่อง <code>Need confirmation</code> ก่อน
            แล้วค่อยกดปุ่มข้างล่าง (หรือ commit เองจากเทอร์มินัลก็ได้) ·
            บนบอร์ดมี task <b>&quot;Sign-off เอกสารกำกับก่อนเริ่มงาน&quot;</b> รออยู่แล้ว
          </p>

          <div className="flex flex-wrap items-center gap-3">
            <button onClick={() => router.push(`/projects/${projectId}`)} className="btn-primary">
              ไปที่บอร์ด
            </button>
            <button onClick={commitNow} disabled={committing} className="btn-ghost">
              {committing ? "กำลัง commit…" : "📌 Commit เลย"}
            </button>
            {commitMsg && (
              <span className="text-sm" style={{ color: "var(--text2)" }}>
                {commitMsg}
              </span>
            )}
          </div>
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

/** ช่องลากไฟล์ดีไซน์/สเปกมาแนบตอนเปิดโปรเจกต์ (เหมือน new-project-studio)
 *  ไฟล์ถูกเก็บลง `_design_input/` หลัง bootstrap สำเร็จ — **ยังไม่เรียก AI ที่นี่** */
function DesignDropZone({
  files,
  onChange,
}: {
  files: File[];
  onChange: (files: File[]) => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [hot, setHot] = useState(false);

  function add(list: FileList | null) {
    if (!list?.length) return;
    onChange([...files, ...Array.from(list)]);
  }

  return (
    <div>
      <span className="mb-1 block text-sm" style={{ color: "var(--text2)" }}>
        ไฟล์ดีไซน์/สเปก (ถ้ามี) — .md / .txt / .pdf / .docx / รูป
      </span>
      <div
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setHot(true);
        }}
        onDragLeave={() => setHot(false)}
        onDrop={(e) => {
          e.preventDefault();
          setHot(false);
          add(e.dataTransfer.files);
        }}
        className="cursor-pointer rounded-lg border-2 border-dashed p-5 text-center text-sm"
        style={{
          borderColor: hot ? "var(--claude)" : "var(--border)",
          color: "var(--text3)",
        }}
      >
        📎 ลากไฟล์มาวาง หรือ คลิกเพื่อเลือก
      </div>
      <input
        ref={inputRef}
        type="file"
        multiple
        hidden
        onChange={(e) => {
          add(e.target.files);
          e.target.value = ""; // เลือกไฟล์ชื่อเดิมซ้ำได้ (ไม่งั้น onChange ไม่ยิง)
        }}
      />
      {files.length > 0 && (
        <ul className="mt-2 space-y-1 text-sm" style={{ color: "var(--text2)" }}>
          {files.map((f, i) => (
            <li key={`${f.name}-${i}`} className="flex items-center gap-2">
              <span>📄 {f.name}</span>
              <button
                type="button"
                onClick={() => onChange(files.filter((_, j) => j !== i))}
                style={{ color: "var(--text3)" }}
              >
                ✕
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
