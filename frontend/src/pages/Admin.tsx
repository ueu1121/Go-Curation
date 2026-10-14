import React, { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { errorMessage, patch, post } from "@/api/client";
import type { Experience } from "@/api/types";
import { ErrorState, Loading, PageHeader, Pill } from "@/components/Bits";
import { useMe } from "@/context/AuthContext";
import { formatLocalDateTime, humanize } from "@/lib/format";
import { useGet } from "@/lib/useGet";
import { CandidateForm } from "@/pages/admin/CandidateForm";

type Cand = Experience & { publication_check: { eligible: boolean; errors: string[]; warnings: string[] } };
const STATES = ["unverified", "reviewed_supports_claim", "reviewed_partial", "reviewed_does_not_support", "stale"];

function Setup() {
  const q = useGet<any>("setup-check", "/admin/setup-check");
  if (q.isLoading) return <Loading />;
  if (q.error) return <ErrorState message={errorMessage(q.error)} />;
  return (
    <section className="card" data-testid="setup-check">
      <h2 className="font-serif text-xl">Setup diagnostic <Pill tone={q.data.ok ? "forest" : "clay"}>{q.data.ok ? "all checks pass" : "needs attention"}</Pill></h2>
      <p className="text-xs text-stone-500">Shows variable names and pass/fail only — never secret values.</p>
      <ul className="mt-3 space-y-1 text-sm">{q.data.checks.map((c: any) => (
        <li key={c.check} className="flex justify-between gap-2"><span>{humanize(c.check)}</span><span className={c.ok ? "text-[#2D4A3E]" : "text-red-700"}>{c.ok ? "ok" : "fail"}</span></li>
      ))}</ul>
      <p className="eyebrow mt-4 mb-1">Integrations</p>
      <ul className="space-y-1 text-sm">{q.data.providers.map((p: any) => (
        <li key={p.name} className="flex justify-between gap-2"><span>{p.name}</span><span className="text-stone-500">{p.connected ? "connected" : "not connected"} · {p.mode}</span></li>
      ))}</ul>
    </section>
  );
}

function Status() {
  const q = useGet<any>("admin-status", "/admin/status");
  if (!q.data) return null;
  const s = q.data;
  return (
    <section className="card text-sm" data-testid="admin-status">
      <h2 className="font-serif text-xl">System status</h2>
      <p>Last successful automation record: {s.last_successful_run ? formatLocalDateTime(s.last_successful_run.finished_at) : "none"}</p>
      <p>Last published batch: {s.last_published_batch ? `${s.last_published_batch.local_date} · ${s.last_published_batch.slot}` : "none"}</p>
      <p data-testid="admin-overdue-count">Overdue ideas: {s.overdue_ideas.length} · open ideas: {s.open_ideas.length}</p>
      <p>Failed / rejected tasks: {s.failed_runs.length}</p>
      {s.failed_runs.slice(0, 3).map((r: any, i: number) => <p key={i} className="text-xs text-red-700">{r.run_type}: {r.error_summary}</p>)}
    </section>
  );
}

function CandRow({ c, picked, onPick }: { c: Cand; picked: boolean; onPick: () => void }) {
  const qc = useQueryClient();
  const review = async (id: string, status: string) => {
    try {
      await patch(`/admin/evidence/${id}`, { verification_status: status });
      qc.invalidateQueries({ queryKey: ["admin-candidates"] });
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };
  return (
    <li className="rounded-xl border border-stone-200 bg-white p-3" data-testid={`admin-cand-${c.id}`}>
      <label className="flex items-start gap-3">
        <input type="checkbox" className="mt-1 h-5 w-5 accent-[#2D4A3E]" checked={picked} onChange={onPick} data-testid={`admin-cand-pick-${c.id}`} />
        <span><span className="font-medium">{c.title}</span> <span className="text-xs text-stone-500">fit {c.fit_score} · {humanize(c.research_status)}</span></span>
      </label>
      <p className={`mt-1 text-xs ${c.publication_check.eligible ? "text-[#2D4A3E]" : "text-red-700"}`} data-testid={`admin-cand-check-${c.id}`}>
        {c.publication_check.eligible ? "Eligible to publish" : `Blocked: ${c.publication_check.errors.map(humanize).join(", ")}`}
        {c.publication_check.warnings.length > 0 && ` · warnings: ${c.publication_check.warnings.map(humanize).join(", ")}`}
      </p>
      {c.evidence.map((e) => (
        <div key={e.id} className="mt-2 rounded-lg bg-[#F5F3ED] p-2 text-xs">
          <p className="break-all">{e.url}</p><p>Claim: {e.supported_claim}</p>
          <select data-testid={`evidence-review-${e.id}`} className="input mt-1 py-1 text-xs" value={e.verification_status} onChange={(x) => review(e.id!, x.target.value)}>
            {STATES.map((s) => <option key={s} value={s}>{humanize(s)}</option>)}
          </select>
        </div>
      ))}
    </li>
  );
}

function Candidates() {
  const { environment } = useMe();
  const q = useGet<{ items: Cand[] }>("admin-candidates", "/admin/candidates");
  const qc = useQueryClient();
  const [picked, setPicked] = useState<string[]>([]);
  const [slot, setSlot] = useState<"morning" | "midday">("morning");
  const [result, setResult] = useState<any>(null);
  const publish = async (status: "published" | "draft") => {
    try {
      const r = await post("/admin/batches", { idempotency_key: `admin-${environment.local_date}-${slot}-${picked.sort().join(".").slice(0, 120)}-${status}`,
        local_date: environment.local_date, slot, status, items: picked.map((id, i) => ({ experience_id: id, rank: i + 1 })) });
      setResult(r);
      toast.success(status === "published" ? "Batch published to Today" : "Draft stored");
      qc.invalidateQueries();
    } catch (e) {
      setResult((e as any)?.response?.data?.detail);
      toast.error(errorMessage(e));
    }
  };
  return (
    <section className="card space-y-3" data-testid="admin-candidates">
      <h2 className="font-serif text-xl">Real candidates</h2>
      {q.isLoading && <Loading />}
      {q.data?.items.length === 0 && <p className="text-sm italic text-stone-500">No real candidates yet. Demo cards never appear here.</p>}
      <ul className="space-y-2">{q.data?.items.map((c) => (
        <CandRow key={c.id} c={c} picked={picked.includes(c.id)} onPick={() => setPicked(picked.includes(c.id) ? picked.filter((x) => x !== c.id) : [...picked, c.id])} />
      ))}</ul>
      <div className="flex flex-wrap items-center gap-2">
        {(["morning", "midday"] as const).map((s) => <button key={s} aria-pressed={slot === s} data-testid={`admin-slot-${s}`} onClick={() => setSlot(s)} className={`chip ${slot === s ? "chip-on" : ""}`}>{s}</button>)}
        <button data-testid="admin-publish-btn" disabled={!picked.length} className="btn-primary" onClick={() => publish("published")}>Publish ({picked.length})</button>
        <button data-testid="admin-draft-btn" disabled={!picked.length} className="btn-ghost" onClick={() => publish("draft")}>Save draft</button>
      </div>
      {result && <pre data-testid="admin-batch-result" className="max-h-60 overflow-auto rounded-xl bg-stone-900 p-3 text-xs text-stone-100">{JSON.stringify(result.validation ?? result, null, 2)}</pre>}
    </section>
  );
}

export default function Admin() {
  const { member, environment } = useMe();
  const qc = useQueryClient();
  if (!member.is_admin) return <ErrorState message="Administrator access required." />;
  const resetDemo = async () => {
    await post("/admin/demo/reset");
    qc.invalidateQueries();
    toast.success("Demo data reset");
  };
  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Administrator" title="Setup & candidates">Manual path for real researched records. Nothing here books, emails or schedules anything.</PageHeader>
      <Setup />
      <Status />
      <Candidates />
      <CandidateForm />
      {environment.demo_mode && <button data-testid="admin-demo-reset" className="btn-ghost" onClick={resetDemo}>Reset demo data</button>}
    </div>
  );
}
