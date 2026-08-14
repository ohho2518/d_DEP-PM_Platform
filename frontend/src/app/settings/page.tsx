"use client";
// ตั้งค่าผู้ให้บริการ AI — คีย์ · ตัวหลัก · ลำดับสำรอง · ปุ่มทดสอบ
// เกิดจากใบสั่งงาน 2026-08-06: วันที่เครดิตหมด การสลับไปเจ้าสำรองต้องทำได้ทันที
// ไม่ใช่ต้องไปแก้ไฟล์ .env แล้ว restart backend กลางวิกฤต
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type {
  BudgetAction,
  LlmSettings,
  ProviderTestKind,
  ProviderTestResult,
} from "@/lib/types";

const LABELS: Record<string, string> = {
  anthropic: "Anthropic (Claude)",
  openai: "OpenAI",
  google: "Google (Gemini)",
};

const KIND_HINT: Record<ProviderTestKind, { text: string; color: string }> = {
  account: { text: "บัญชีใช้ไม่ได้ — เครดิตหมดหรือคีย์ผิด", color: "var(--danger)" },
  temporary: { text: "ขัดข้องชั่วคราว — ลองใหม่อีกครั้ง", color: "var(--warn)" },
  request: { text: "คำขอไม่ถูกต้อง (ไม่ใช่ปัญหาของบัญชี)", color: "var(--warn)" },
  unknown: { text: "ไม่ทราบสาเหตุ", color: "var(--warn)" },
};

export default function SettingsPage() {
  const [settings, setSettings] = useState<LlmSettings | null>(null);
  const [primary, setPrimary] = useState("");
  const [fallbacks, setFallbacks] = useState<string[]>([]);
  const [keyDrafts, setKeyDrafts] = useState<Record<string, string>>({});
  const [modelDrafts, setModelDrafts] = useState<Record<string, string>>({});
  const [budget, setBudget] = useState("0");
  const [budgetAction, setBudgetAction] = useState<BudgetAction>("warn");
  const [results, setResults] = useState<Record<string, ProviderTestResult>>({});
  const [testing, setTesting] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const data = await api.llmSettings();
      setSettings(data);
      setPrimary(data.provider);
      setFallbacks(data.fallbacks);
      setModelDrafts(Object.fromEntries(data.providers.map((p) => [p.name, p.model])));
      setBudget(String(data.budget_usd));
      setBudgetAction(data.budget_action);
      setKeyDrafts({});
    } catch (e) {
      setError(String(e));
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function save(extraKeys: Record<string, string> = {}) {
    setSaving(true);
    setError(null);
    try {
      // ส่งเฉพาะคีย์ที่พิมพ์ใหม่จริง ๆ — ช่องว่าง = ไม่แตะของเดิม (ดู schemas/settings.py)
      const keys = { ...extraKeys };
      for (const [name, value] of Object.entries(keyDrafts)) {
        if (value.trim()) keys[name] = value.trim();
      }
      const data = await api.saveLlmSettings({
        provider: primary,
        fallbacks,
        keys,
        models: modelDrafts,
        // ช่องว่าง/พิมพ์ผิด = ไม่จำกัด (0) — ไม่ส่ง NaN ไปให้ backend ปฏิเสธเป็น 422
        budget_usd: Math.max(0, Number(budget) || 0),
        budget_action: budgetAction,
      });
      setSettings(data);
      setBudget(String(data.budget_usd));
      setBudgetAction(data.budget_action);
      setKeyDrafts({});
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch (e) {
      setError(String(e));
    } finally {
      setSaving(false);
    }
  }

  async function runTest(provider?: string) {
    setTesting(provider ?? "*");
    setError(null);
    try {
      const { results: list } = await api.testLlmProvider(provider);
      setResults((prev) => ({
        ...prev,
        ...Object.fromEntries(list.map((r) => [r.provider, r])),
      }));
    } catch (e) {
      setError(String(e));
    } finally {
      setTesting(null);
    }
  }

  function toggleFallback(name: string) {
    setFallbacks((prev) =>
      prev.includes(name) ? prev.filter((n) => n !== name) : [...prev, name],
    );
  }

  function moveFallback(name: string, direction: -1 | 1) {
    setFallbacks((prev) => {
      const index = prev.indexOf(name);
      const target = index + direction;
      if (index < 0 || target < 0 || target >= prev.length) return prev;
      const next = [...prev];
      [next[index], next[target]] = [next[target], next[index]];
      return next;
    });
  }

  if (error && !settings)
    return (
      <p className="card p-4 text-sm" style={{ color: "var(--danger)" }}>
        เชื่อมต่อ backend ไม่ได้: {error}
      </p>
    );
  if (!settings) return <p style={{ color: "var(--text2)" }}>กำลังโหลด…</p>;

  const chain = [primary, ...fallbacks.filter((n) => n !== primary)];
  const noKeyAtAll = settings.providers.every((p) => !p.key_set);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">ตั้งค่า AI</h1>
        <button className="btn-ghost" onClick={() => runTest()} disabled={testing !== null}>
          {testing === "*" ? "กำลังทดสอบ…" : "ทดสอบทั้งหมด"}
        </button>
      </div>

      <p className="text-xs" style={{ color: "var(--text3)" }}>
        เจ้าหลักล่ม → ระบบไล่ไปตามลำดับสำรองเอง และ<b>ติดป้ายในผลงาน</b>ว่าใครเป็นคนทำ ·
        บันทึกแล้วมีผลทันทีโดยไม่ต้อง restart · คีย์ถูกเก็บใน <code>backend/.env</code> เท่านั้น
      </p>

      {noKeyAtAll && (
        <p
          className="rounded-[14px] border p-3 text-sm"
          style={{ borderColor: "var(--danger)", color: "var(--danger)" }}
        >
          ยังไม่ได้ตั้งคีย์เลยสักเจ้า — ระบบจะทำงานในโหมด deterministic (ผลงานเป็นข้อความตัวอย่าง)
        </p>
      )}

      {error && (
        <p className="card p-3 text-sm" style={{ color: "var(--danger)" }}>
          {error}
        </p>
      )}

      {/* ลำดับที่จะถูกเรียกจริง */}
      <div className="card p-4">
        <h2 className="mb-2 text-sm font-semibold">ลำดับการเรียก</h2>
        <div className="flex flex-wrap items-center gap-2 text-sm">
          {chain.map((name, i) => (
            <span key={name} className="flex items-center gap-2">
              {i > 0 && <span style={{ color: "var(--text3)" }}>→</span>}
              <span className="chip">
                {i === 0 ? "ตัวหลัก: " : `สำรอง ${i}: `}
                {LABELS[name] ?? name}
              </span>
            </span>
          ))}
          {chain.length === 1 && (
            <span className="text-xs" style={{ color: "var(--warn)" }}>
              ยังไม่มีตัวสำรอง — เจ้านี้ล่มเมื่อไหร่ งานหยุดทันที
            </span>
          )}
        </div>
      </div>

      {/* เพดานค่าใช้จ่าย (§5 ใบสั่งงาน 2026-08-06) */}
      <div className="card space-y-3 p-4">
        <h2 className="text-sm font-semibold">เพดานค่าใช้จ่าย (ต่อโปรเจกต์)</h2>
        <div className="flex flex-wrap items-end gap-4">
          <label className="text-sm">
            <span style={{ color: "var(--text2)" }}>เพดาน (USD) · 0 = ไม่จำกัด</span>
            <input
              type="number"
              min={0}
              step="0.5"
              className="input mt-1 w-40"
              value={budget}
              onChange={(e) => setBudget(e.target.value)}
            />
          </label>
          <div className="flex items-center gap-3 text-sm">
            {(["warn", "stop"] as BudgetAction[]).map((action) => (
              <label key={action} className="flex items-center gap-1">
                <input
                  type="radio"
                  name="budget-action"
                  checked={budgetAction === action}
                  onChange={() => setBudgetAction(action)}
                />
                {action === "warn" ? "เตือนอย่างเดียว" : "หยุดไม่เริ่มงานใหม่"}
              </label>
            ))}
          </div>
        </div>
        <p className="text-xs" style={{ color: "var(--text3)" }}>
          ⚠️ ตัวเลขค่าใช้จ่ายเป็น<b>ประมาณการ</b>จากราคาที่ตั้งไว้ข้างล่าง <b>ไม่ใช่บิลจริง</b>{" "}
          (ส่วนลด/เครดิตไม่ถูกนับ) · &ldquo;หยุด&rdquo; หมายถึงไม่หยิบ task ใหม่ —
          ตัวที่กำลังทำอยู่ยังทำจนจบเสมอ เพราะจ่ายค่าโทเคนไปแล้ว
        </p>
        <table className="w-full text-left text-xs" style={{ color: "var(--text2)" }}>
          <thead style={{ color: "var(--text3)" }}>
            <tr>
              <th className="py-1">ราคาที่ใช้ประมาณการ (USD ต่อ 1 ล้านโทเคน)</th>
              <th className="py-1">เข้า</th>
              <th className="py-1">ออก</th>
            </tr>
          </thead>
          <tbody>
            {settings.providers.map((p) => (
              <tr key={p.name}>
                <td className="py-1">{LABELS[p.name] ?? p.name}</td>
                <td className="py-1">${p.price_in}</td>
                <td className="py-1">${p.price_out}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="text-[11px]" style={{ color: "var(--text3)" }}>
          ราคาแก้ได้ที่ <code>backend/.env</code> (<code>LLM_PRICE_*</code>) — ตั้งใจไม่ให้แก้จากหน้านี้
          เพราะเป็นตัวเลขที่ต้องยืนยันกับบิลจริงก่อน
        </p>
      </div>

      {settings.providers.map((p) => {
        const result = results[p.name];
        const isFallback = fallbacks.includes(p.name);
        return (
          <div key={p.name} className="card space-y-3 p-4">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold">{LABELS[p.name] ?? p.name}</h2>
              <div className="flex items-center gap-3 text-sm">
                <label className="flex items-center gap-1">
                  <input
                    type="radio"
                    name="primary"
                    checked={primary === p.name}
                    onChange={() => setPrimary(p.name)}
                  />
                  ตัวหลัก
                </label>
                <label className="flex items-center gap-1">
                  <input
                    type="checkbox"
                    checked={isFallback}
                    disabled={primary === p.name}
                    onChange={() => toggleFallback(p.name)}
                  />
                  ตัวสำรอง
                </label>
                {isFallback && (
                  <span className="flex gap-1">
                    <button className="btn-ghost px-2" onClick={() => moveFallback(p.name, -1)}>
                      ↑
                    </button>
                    <button className="btn-ghost px-2" onClick={() => moveFallback(p.name, 1)}>
                      ↓
                    </button>
                  </span>
                )}
              </div>
            </div>

            <div className="grid gap-3 md:grid-cols-2">
              <label className="text-sm">
                <span style={{ color: "var(--text2)" }}>API key</span>
                <input
                  type="password"
                  className="input mt-1 w-full"
                  autoComplete="off"
                  placeholder={p.key_set ? `ตั้งไว้แล้ว: ${p.key_masked}` : "ยังไม่ได้ตั้ง"}
                  value={keyDrafts[p.name] ?? ""}
                  onChange={(e) =>
                    setKeyDrafts((prev) => ({ ...prev, [p.name]: e.target.value }))
                  }
                />
                <span className="text-[11px]" style={{ color: "var(--text3)" }}>
                  เว้นว่าง = ไม่แก้ของเดิม
                </span>
              </label>

              <label className="text-sm">
                <span style={{ color: "var(--text2)" }}>ชื่อรุ่น</span>
                <input
                  className="input mt-1 w-full"
                  value={modelDrafts[p.name] ?? ""}
                  onChange={(e) =>
                    setModelDrafts((prev) => ({ ...prev, [p.name]: e.target.value }))
                  }
                />
              </label>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <button
                className="btn-ghost"
                onClick={() => runTest(p.name)}
                disabled={testing !== null}
              >
                {testing === p.name ? "กำลังทดสอบ…" : "ทดสอบ"}
              </button>
              {p.key_set && (
                <button
                  className="btn-ghost"
                  onClick={() => save({ [p.name]: "" })}
                  disabled={saving}
                >
                  ลบคีย์
                </button>
              )}
              {result && (
                <span
                  className="text-sm"
                  style={{
                    color: result.ok
                      ? "var(--ok)"
                      : KIND_HINT[result.kind ?? "unknown"].color,
                  }}
                >
                  {result.ok
                    ? `✅ ใช้ได้ — ${result.model} (${result.latency_ms} ms)`
                    : `❌ ${KIND_HINT[result.kind ?? "unknown"].text}`}
                </span>
              )}
            </div>

            {result && !result.ok && result.detail && (
              <pre
                className="overflow-x-auto rounded-[10px] p-2 text-[11px]"
                style={{ background: "var(--bg)", color: "var(--text2)" }}
              >
                {result.detail}
              </pre>
            )}
          </div>
        );
      })}

      <div className="flex items-center gap-3">
        <button className="btn-primary" onClick={() => save()} disabled={saving}>
          {saving ? "กำลังบันทึก…" : "บันทึก"}
        </button>
        {saved && (
          <span className="text-sm" style={{ color: "var(--ok)" }}>
            บันทึกแล้ว — มีผลทันที
          </span>
        )}
      </div>
    </div>
  );
}
