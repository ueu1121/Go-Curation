import React, { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { errorMessage, post } from "@/api/client";

const WEIGHTS: [string, number][] = [["uniqueness", 25], ["low_crowd", 20], ["preference_fit", 15], ["timing", 15], ["evidence", 15], ["practicality", 10]];
const TEXT_FIELDS: [string, string][] = [
  ["title", "Title *"], ["category", "Category * (e.g. food, history, wildlife)"], ["description", "Description *"],
  ["why_now", "Why now"], ["why_unique", "Why unique"], ["fit_explanation", "Why it fits"], ["hidden_perk", "Hidden perk"],
  ["best_timing", "Best timing"], ["duration_estimate", "Visit length"], ["suggested_window", "Suggested window"],
  ["crowd_guidance", "Crowd guidance (say what it's based on)"], ["accessibility_notes", "Accessibility & walking"],
  ["weather_notes", "Weather notes"], ["nearby_backup", "Optional nearby backup"], ["distinct_angle", "Distinct angle (needed for parks/waterfalls)"],
  ["novelty_explanation", "How it differs from a previous visit"], ["verification_notes", "Verification notes"],
];
type Ev = { url: string; supported_claim: string; source_type: string; verification_status: string; retrieved_at: string };
const blankEv = (): Ev => ({ url: "", supported_claim: "", source_type: "official", verification_status: "unverified", retrieved_at: "" });
const nul = (v: string) => (v.trim() === "" ? null : v.trim());
const num = (v: string) => (v.trim() === "" ? null : Number(v));

function Inp({ k, label, f, set, type = "text" }: { k: string; label: string; f: Record<string, string>; set: (k: string, v: string) => void; type?: string }) {
  return (
    <label className="block">
      <span className="text-xs text-stone-600">{label}</span>
      <input data-testid={`cand-${k}`} type={type} className="input mt-0.5" value={f[k] ?? ""} onChange={(e) => set(k, e.target.value)} />
    </label>
  );
}

function buildBody(f: Record<string, string>, ev: Ev[]) {
  return {
    destination: { name: f.dest_name, locality: nul(f.locality || ""), kind: f.dest_kind || "attraction", aliases: [] },
    experience: {
      ...Object.fromEntries(TEXT_FIELDS.map(([k]) => [k, nul(f[k] || "")])),
      kind: f.kind || "evergreen", effort: nul(f.effort || ""), indoor: f.indoor === "yes" ? true : f.indoor === "no" ? false : null,
      crowd_level: nul(f.crowd_level || ""), exceptional_distance: f.exceptional === "yes",
      cost_for_two: { min: num(f.cost_min || ""), max: num(f.cost_max || ""), currency: "CAD", status: f.cost_status || "unknown" },
      booking: { required: f.booking_required === "yes" ? true : f.booking_required === "no" ? false : null, deadline: nul(f.booking_deadline || ""), notes: null },
      unknowns: (f.unknowns || "").split(",").map((s) => s.trim()).filter(Boolean),
    },
    travel: { geo_distance_km: num(f.geo_km || ""), geo_method: nul(f.geo_method || ""), driving_distance_km: num(f.drive_km || ""),
      driving_duration_min: num(f.drive_min || ""), measurement_source: nul(f.measure_src || ""), status: f.travel_status || "unknown" },
    occurrences: f.start_date ? [{ start_date: f.start_date, end_date: nul(f.end_date || ""), booking_deadline: nul(f.booking_deadline || ""), timezone: "America/Toronto", availability_status: "unknown" }] : [],
    evidence: ev.filter((e) => e.url.trim()).map((e) => ({ ...e, retrieved_at: nul(e.retrieved_at) })),
    score_components: Object.fromEntries(WEIGHTS.map(([k]) => [k, Number(f[`s_${k}`] || 0)])),
  };
}

export function CandidateForm() {
  const qc = useQueryClient();
  const [f, setF] = useState<Record<string, string>>({ kind: "evergreen", cost_status: "unknown", travel_status: "unknown" });
  const [ev, setEv] = useState<Ev[]>([blankEv()]);
  const [result, setResult] = useState<any>(null);
  const set = (k: string, v: string) => setF({ ...f, [k]: v });
  const setE = (i: number, k: keyof Ev, v: string) => setEv(ev.map((e, j) => (j === i ? { ...e, [k]: v } : e)));
  const submit = async () => {
    try {
      const r = await post("/admin/candidates", buildBody(f, ev));
      setResult(r);
      qc.invalidateQueries({ queryKey: ["admin-candidates"] });
      toast.success("Candidate stored");
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };
  const total = WEIGHTS.reduce((s, [k]) => s + Number(f[`s_${k}`] || 0), 0);
  return (
    <section className="card space-y-3" data-testid="candidate-form">
      <h2 className="font-serif text-xl">Enter a researched candidate</h2>
      <p className="text-xs text-stone-500">Real records only — never invent details. Leave unknowns empty. Same publication rules as automation.</p>
      <Inp k="dest_name" label="Destination name *" f={f} set={set} />
      <div className="grid grid-cols-2 gap-2"><Inp k="locality" label="Town" f={f} set={set} /><Inp k="dest_kind" label="Place type" f={f} set={set} /></div>
      {TEXT_FIELDS.map(([k, l]) => <Inp key={k} k={k} label={l} f={f} set={set} />)}
      <div className="grid grid-cols-2 gap-2">
        <Inp k="kind" label="evergreen | seasonal | dated_event" f={f} set={set} /><Inp k="effort" label="easy | moderate | involved" f={f} set={set} />
        <Inp k="indoor" label="Indoor? yes | no" f={f} set={set} /><Inp k="crowd_level" label="Crowd: low | moderate | high" f={f} set={set} />
        <Inp k="cost_min" label="Cost min (two)" f={f} set={set} /><Inp k="cost_max" label="Cost max (two)" f={f} set={set} />
        <Inp k="cost_status" label="unknown | estimate | verified" f={f} set={set} /><Inp k="booking_required" label="Booking? yes | no" f={f} set={set} />
        <Inp k="start_date" label="Event start" type="date" f={f} set={set} /><Inp k="end_date" label="Event end" type="date" f={f} set={set} />
        <Inp k="booking_deadline" label="Booking deadline" type="date" f={f} set={set} /><Inp k="exceptional" label="Exceptional distance? yes" f={f} set={set} />
        <Inp k="geo_km" label="Straight-line km" f={f} set={set} /><Inp k="geo_method" label="Straight-line method" f={f} set={set} />
        <Inp k="drive_km" label="Driving km" f={f} set={set} /><Inp k="drive_min" label="Driving minutes" f={f} set={set} />
        <Inp k="measure_src" label="Measurement source" f={f} set={set} /><Inp k="travel_status" label="unknown | estimate | verified" f={f} set={set} />
      </div>
      <Inp k="unknowns" label="Unknowns (comma separated)" f={f} set={set} />
      <p className="eyebrow pt-2">Evidence (a URL alone is not proof)</p>
      {ev.map((e, i) => (
        <div key={i} className="space-y-1 rounded-xl bg-[#F5F3ED] p-3">
          <input data-testid={`cand-ev-url-${i}`} className="input" placeholder="https://source" value={e.url} onChange={(x) => setE(i, "url", x.target.value)} />
          <input data-testid={`cand-ev-claim-${i}`} className="input" placeholder="Claim this source supports" value={e.supported_claim} onChange={(x) => setE(i, "supported_claim", x.target.value)} />
          <div className="grid grid-cols-3 gap-1">
            <input data-testid={`cand-ev-type-${i}`} className="input" placeholder="official" value={e.source_type} onChange={(x) => setE(i, "source_type", x.target.value)} />
            <input data-testid={`cand-ev-status-${i}`} className="input" placeholder="unverified" value={e.verification_status} onChange={(x) => setE(i, "verification_status", x.target.value)} />
            <input data-testid={`cand-ev-checked-${i}`} className="input" type="date" aria-label="Checked on" value={e.retrieved_at} onChange={(x) => setE(i, "retrieved_at", x.target.value)} />
          </div>
        </div>
      ))}
      <button className="btn-ghost" data-testid="cand-add-evidence" onClick={() => setEv([...ev, blankEv()])}>+ Add evidence</button>
      <p className="eyebrow pt-2">Fit score components · total {total}/100 (publish needs ≥ 70)</p>
      <div className="grid grid-cols-3 gap-2">{WEIGHTS.map(([k, w]) => <Inp key={k} k={`s_${k}`} label={`${k.replace("_", " ")} /${w}`} f={f} set={set} />)}</div>
      <button data-testid="cand-submit-btn" className="btn-primary w-full" onClick={submit}>Store candidate</button>
      {result && (
        <pre data-testid="cand-result" className="max-h-60 overflow-auto rounded-xl bg-stone-900 p-3 text-xs text-stone-100">{JSON.stringify(result.publication_check ?? result, null, 2)}</pre>
      )}
    </section>
  );
}
