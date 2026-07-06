"use client";
// New Project Onboarding (Blueprint §6 STEP 1-4):
// กรอกข้อมูล → (new) ส่ง requirement ให้ PM Agent แตกงาน / (existing) สั่ง scan
// → เห็น task plan → ยืนยัน scope → ไปที่บอร์ด
import { useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api";
import type { Task } from "@/lib/types";

type Step = "form" | "plan" | "confirming";

export default function NewProjectPage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>("form");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [type, setType] = useState<"new" | "existing">("new");
  const [repoUrl, setRepoUrl] = useState("");
  const [requirement, setRequirement] = useState("");

  const [projectId, setProjectId] = useState<string | null>(null);
  const [plan, setPlan] = useState<Task[]>([]);
  const [source, setSource] = useState<string>("");

  async function submitForm(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const project = await api.createProject({
        name,
        type,
        ...(type === "existing" ? { repo_url: repoUrl } : {}),
      });
      setProjectId(project.id);

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

          <div className="flex gap-4 text-sm">
            {(["new", "existing"] as const).map((t) => (
              <label key={t} className="flex items-center gap-2">
                <input
                  type="radio"
                  checked={type === t}
                  onChange={() => setType(t)}
                  style={{ accentColor: "var(--claude)" }}
                />
                {t === "new" ? "โปรเจกต์ใหม่ (PM Agent แตกงาน)" : "โปรเจกต์เดิม (scan repo — mock)"}
              </label>
            ))}
          </div>

          {type === "new" ? (
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

          <button
            disabled={busy}
            className="btn-primary"
          >
            {busy ? "กำลังสร้าง task plan…" : "สร้างโปรเจกต์ + แตกงาน"}
          </button>
        </form>
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
