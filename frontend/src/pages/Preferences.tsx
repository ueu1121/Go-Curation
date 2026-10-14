import React, { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { errorMessage, post, put } from "@/api/client";
import type { Exclusion } from "@/api/types";
import { ErrorState, Loading, PageHeader, Pill } from "@/components/Bits";
import { useAuth, useMe } from "@/context/AuthContext";
import { formatLocalDateTime } from "@/lib/format";
import { useGet } from "@/lib/useGet";
import { api } from "@/api/client";

type Prefs = Record<string, any>;

function TextRow({ label, value, onChange, testId, hint }: { label: string; value: string; onChange: (v: string) => void; testId: string; hint?: string }) {
  return (
    <label className="block py-2">
      <span className="eyebrow">{label}</span>
      <input data-testid={testId} className="input mt-1" value={value ?? ""} onChange={(e) => onChange(e.target.value)} />
      {hint && <span className="mt-1 block text-xs text-stone-500">{hint}</span>}
    </label>
  );
}

function SharedProfile({ prefs }: { prefs: Prefs }) {
  const qc = useQueryClient();
  const { nameOf } = useAuth();
  const [p, setP] = useState<Prefs>(prefs);
  useEffect(() => { setP(prefs); }, [prefs]);
  const set = (path: string[], v: unknown) => {
    const next = structuredClone(p);
    let o = next;
    path.slice(0, -1).forEach((k) => { o = o[k]; });
    o[path[path.length - 1]] = v;
    setP(next);
  };
  const save = async () => {
    try {
      const fields = ["origin", "distance_policy", "availability", "interests", "avoidances", "effort_tolerance", "budget",
        "walking_tolerance", "accessibility_needs", "dietary", "tie_break_rule", "outing_shape"];
      await put("/preferences", Object.fromEntries(fields.map((f) => [f, p[f]])));
      toast.success("Shared profile saved");
      qc.invalidateQueries({ queryKey: ["preferences"] });
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };
  const dp = p.distance_policy;
  return (
    <section className="card" data-testid="shared-profile">
      <h2 className="font-serif text-xl text-stone-900">Shared profile</h2>
      <p className="text-xs text-stone-500">Last changed {p.updated_by ? `by ${nameOf(p.updated_by)} · ${formatLocalDateTime(p.updated_at)}` : "never (initial setup)"}</p>
      <TextRow testId="pref-origin" label="Home origin" value={p.origin.label} onChange={(v) => set(["origin", "label"], v)}
        hint={`Precision: ${p.origin.precision} · ${p.origin.status}. Coordinates ${p.origin.lat == null ? "not set" : "set"}.`} />
      <div className="py-2">
        <span className="eyebrow">Distance rule basis</span>
        <div className="mt-1 inline-flex rounded-full border border-stone-300 bg-white p-0.5">
          {(["geographic", "driving"] as const).map((b) => (
            <button key={b} data-testid={`pref-basis-${b}`} aria-pressed={dp.basis === b} onClick={() => set(["distance_policy", "basis"], b)}
              className={`rounded-full px-3 py-1.5 text-sm ${dp.basis === b ? "bg-[#2D4A3E] text-white" : "text-stone-600"}`}>
              {b === "geographic" ? "Straight-line radius" : "Road distance"}</button>
          ))}
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <TextRow testId="pref-primary-km" label="Primary km" value={String(dp.primary_km)} onChange={(v) => set(["distance_policy", "primary_km"], Number(v) || 0)} />
        <TextRow testId="pref-exceptional-km" label="Exceptional km" value={String(dp.exceptional_km)} onChange={(v) => set(["distance_policy", "exceptional_km"], Number(v) || 0)} hint="Must be labelled exceptional" />
        <TextRow testId="pref-depart" label="Leave after" value={p.availability.depart_after} onChange={(v) => set(["availability", "depart_after"], v)} />
        <TextRow testId="pref-return" label="Home by" value={p.availability.return_by} onChange={(v) => set(["availability", "return_by"], v)} />
      </div>
      <p className="text-xs text-stone-500">{p.availability.note} Days: {p.availability.days.join(", ")} · Timezone {p.timezone}</p>
      <TextRow testId="pref-effort" label="Effort tolerance" value={p.effort_tolerance} onChange={(v) => set(["effort_tolerance"], v)} />
      <TextRow testId="pref-budget" label="Budget for two (max $, or unspecified)" value={p.budget.max_for_two ?? "unspecified"}
        onChange={(v) => set(["budget"], v === "unspecified" || !v ? { status: "unspecified", max_for_two: null } : { status: "set", max_for_two: Number(v) || null })} />
      <TextRow testId="pref-walking" label="Shared walking tolerance" value={p.walking_tolerance} onChange={(v) => set(["walking_tolerance"], v)} />
      <TextRow testId="pref-accessibility" label="Accessibility needs" value={p.accessibility_needs} onChange={(v) => set(["accessibility_needs"], v)} />
      <TextRow testId="pref-dietary" label="Dietary" value={p.dietary} onChange={(v) => set(["dietary"], v)} />
      <TextRow testId="pref-tiebreak" label="Tie-break rule (agree together)" value={p.tie_break_rule} onChange={(v) => set(["tie_break_rule"], v)} />
      <TextRow testId="pref-interests" label="Interests (comma separated)" value={p.interests.join(", ")} onChange={(v) => set(["interests"], v.split(",").map((s) => s.trim()).filter(Boolean))} />
      <TextRow testId="pref-avoidances" label="Avoid (comma separated)" value={p.avoidances.join("; ")} onChange={(v) => set(["avoidances"], v.split(";").map((s) => s.trim()).filter(Boolean))} hint="Separate with semicolons" />
      <button data-testid="pref-save-btn" className="btn-primary mt-3 w-full" onClick={save}>Save shared profile</button>
    </section>
  );
}

function Personal() {
  const { member } = useMe();
  const { refresh } = useAuth();
  const [name, setName] = useState(member.display_name);
  const [walk, setWalk] = useState(member.personal_preferences.walking_tolerance || "unspecified");
  const save = async () => {
    try {
      await put("/members/me", { display_name: name });
      await put("/preferences/personal", { walking_tolerance: walk });
      await refresh();
      toast.success("Your personal settings are saved");
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };
  return (
    <section className="card" data-testid="personal-profile">
      <h2 className="font-serif text-xl text-stone-900">Just me</h2>
      <p className="text-xs text-stone-500">Only you can change these. Your partner sees them, attributed to you.</p>
      <TextRow testId="personal-name" label="Display name" value={name} onChange={setName} />
      <TextRow testId="personal-walking" label="My walking tolerance" value={walk} onChange={setWalk} />
      <button data-testid="personal-save-btn" className="btn-secondary w-full" onClick={save}>Save my settings</button>
    </section>
  );
}

function Exclusions() {
  const q = useGet<{ items: Exclusion[] }>("exclusions", "/exclusions");
  const qc = useQueryClient();
  const [cat, setCat] = useState("");
  const add = async () => {
    try {
      await post("/exclusions", { scope: "category", category: cat.trim().toLowerCase().replace(/\s+/g, "_"), label: cat, temporary: false });
      setCat("");
      qc.invalidateQueries({ queryKey: ["exclusions"] });
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };
  const remove = async (id: string) => {
    await api.delete(`/exclusions/${id}`);
    qc.invalidateQueries({ queryKey: ["exclusions"] });
  };
  const active = q.data?.items.filter((x) => x.active) ?? [];
  return (
    <section className="card" data-testid="exclusions-section">
      <h2 className="font-serif text-xl text-stone-900">Explicit exclusions</h2>
      <p className="text-xs text-stone-500">These always win over scores. “Not today” and “Not for us” never create these.</p>
      <ul className="my-3 space-y-2">
        {active.length === 0 && <li className="text-sm italic text-stone-500">None yet.</li>}
        {active.map((x) => (
          <li key={x.id} className="flex items-center justify-between gap-2 text-sm">
            <span><Pill tone="clay">{x.scope}</Pill> {x.label || x.category}</span>
            <button data-testid={`exclusion-remove-${x.id}`} className="btn-ghost" onClick={() => remove(x.id)}>Remove</button>
          </li>
        ))}
      </ul>
      <div className="flex gap-2">
        <input data-testid="exclusion-category-input" className="input" placeholder="Block a category, e.g. shopping mall" value={cat} onChange={(e) => setCat(e.target.value)} />
        <button data-testid="exclusion-add-btn" className="btn-primary" disabled={!cat.trim()} onClick={add}>Block</button>
      </div>
    </section>
  );
}

export default function Preferences() {
  const q = useGet<Prefs>("preferences", "/preferences");
  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Settings" title="Preferences">Unknown details stay “unspecified” until you set them — nothing is inferred from age.</PageHeader>
      {q.isLoading && <Loading />}
      {q.error && <ErrorState message={errorMessage(q.error)} onRetry={() => q.refetch()} />}
      {q.data && <SharedProfile prefs={q.data} />}
      <Personal />
      <Exclusions />
    </div>
  );
}
