import React, { useState } from "react";
import type { Exclusion, Plan, Visit } from "@/api/types";
import { DemoBadge, EmptyState, ErrorState, Loading, PageHeader, Pill } from "@/components/Bits";
import { RatingForm } from "@/components/PlanControls";
import { useAuth, useMe } from "@/context/AuthContext";
import { errorMessage } from "@/api/client";
import { formatLocalDate, humanize } from "@/lib/format";
import { useGet } from "@/lib/useGet";

interface HistoryData {
  offered: { id: string; title: string; category: string; local_date: string; slot: string; dataset: string }[];
  plans: Plan[]; visits: Visit[];
  rejections: { batch_item_id: string; member_id: string; reaction: string; reason: string | null; title: string | null }[];
  exclusions: Exclusion[];
}
const TABS = ["visits", "plans", "offered", "declined"] as const;
type Tab = typeof TABS[number];
const TYPE_LABEL: Record<Visit["visit_type"], string> = {
  experience: "Experience", town_visit: "Town visit (activities unknown)", drive_through: "Drive-through only", broad_note: "Broad note",
};

function VisitRow({ v }: { v: Visit }) {
  const { nameOf, me } = useAuth();
  const [rate, setRate] = useState(false);
  const mine = me ? v.feedback.find((f) => f.member_id === me.member.id) : undefined;
  return (
    <li className="card" data-testid={`visit-row-${v.id}`}>
      <div className="flex flex-wrap gap-2">
        {v.dataset === "demo" && <DemoBadge />}
        <Pill tone={v.visit_type === "experience" ? "forest" : "neutral"}>{TYPE_LABEL[v.visit_type]}</Pill>
        {v.user_reported && <Pill tone="muted">User-reported</Pill>}
        {v.needs_confirmation && <Pill tone="warn">Needs confirmation</Pill>}
      </div>
      <h3 className="mt-2 font-serif text-lg text-stone-900">{v.destination_name || humanize(v.category)}{v.activity && ` — ${v.activity}`}</h3>
      <p className="text-sm text-stone-600" data-testid={`visit-date-label-${v.id}`}>{v.visit_date ? formatLocalDate(v.visit_date) : "Date unknown"}</p>
      {v.notes && <p className="mt-1 text-sm text-stone-700">{v.notes}</p>}
      {v.feedback.map((f) => (
        <p key={f.member_id} className="mt-1 text-sm text-stone-700">{nameOf(f.member_id)}: {f.rating ? `${f.rating}/5` : "no rating"}{f.notes ? ` — ${f.notes}` : ""}
          {f.aspects?.map((a) => ` · ${a.aspect} ${a.sentiment}`)}</p>
      ))}
      {!v.historical && !mine?.rating && (rate ? <div className="mt-3"><RatingForm visitId={v.id} onDone={() => setRate(false)} /></div> :
        <button data-testid={`visit-rate-btn-${v.id}`} className="btn-ghost mt-2" onClick={() => setRate(true)}>Rate & add notes</button>)}
    </li>
  );
}

function Body({ tab, d }: { tab: Tab; d: HistoryData }) {
  const { nameOf } = useAuth();
  if (tab === "visits")
    return d.visits.length ? <ul className="space-y-4">{d.visits.map((v) => <VisitRow key={v.id} v={v} />)}</ul> : <EmptyState title="No visits recorded" />;
  if (tab === "plans")
    return d.plans.length ? (
      <ul className="space-y-3">{d.plans.map((p) => (
        <li key={p.id} className="card" data-testid={`plan-row-${p.id}`}>
          <div className="flex gap-2">{p.dataset === "demo" && <DemoBadge />}<Pill tone={p.status === "completed" ? "forest" : p.status === "selected" ? "clay" : "muted"}>{p.status}</Pill></div>
          <p className="mt-2 font-medium text-stone-800">{p.title}</p>
          <p className="text-sm text-stone-500">Planned for {formatLocalDate(p.planned_date)} · selected by {nameOf(p.selected_by)}</p>
        </li>))}</ul>
    ) : <EmptyState title="No plans selected yet" />;
  if (tab === "offered")
    return d.offered.length ? (
      <ul className="divide-y divide-stone-200 rounded-2xl border border-stone-200 bg-white">{d.offered.map((o) => (
        <li key={o.id} className="flex items-center justify-between gap-3 p-4 text-sm">
          <span className="text-stone-800">{o.title}</span>
          <span className="shrink-0 text-stone-500">{o.dataset === "demo" ? "demo" : `${formatLocalDate(o.local_date)} · ${o.slot}`}</span>
        </li>))}</ul>
    ) : <EmptyState title="Nothing offered yet" />;
  return (
    <div className="space-y-4">
      {d.rejections.length === 0 && d.exclusions.length === 0 && <EmptyState title="No rejections or blocks" />}
      {d.rejections.map((r) => (
        <div key={`${r.batch_item_id}-${r.member_id}`} className="card text-sm">
          <Pill tone={r.reaction === "not_for_us" ? "clay" : "neutral"}>{humanize(r.reaction)}</Pill>
          <p className="mt-2 text-stone-800">{r.title} — {nameOf(r.member_id)}{r.reason ? `: “${r.reason}”` : ""}</p>
          {r.reaction === "not_today" && <p className="text-xs text-stone-500">Not today never blocks future suggestions.</p>}
        </div>
      ))}
      {d.exclusions.map((x) => (
        <div key={x.id} className="card text-sm"><Pill tone="clay">{x.active ? "Blocked" : "Block removed"}</Pill>
          <p className="mt-2">{x.label || x.category} ({x.scope}){x.reason ? ` — ${x.reason}` : ""}</p></div>
      ))}
    </div>
  );
}

export default function History() {
  const q = useGet<HistoryData>("history", "/history");
  const [tab, setTab] = useState<Tab>("visits");
  const labels: Record<Tab, string> = { visits: "Visits", plans: "Plans", offered: "Offered", declined: "Declined" };
  return (
    <div>
      <PageHeader eyebrow="Memory" title="History">Selected is not the same as completed — both are kept separately.</PageHeader>
      <div className="mb-5 grid grid-cols-4 gap-1 rounded-full bg-[#F5F3ED] p-1" role="tablist">
        {TABS.map((t) => (
          <button key={t} role="tab" aria-selected={tab === t} data-testid={`history-tab-${t}`} onClick={() => setTab(t)}
            className={`min-h-[44px] rounded-full text-sm font-medium ${tab === t ? "bg-white text-[#2D4A3E] shadow-sm" : "text-stone-600"}`}>{labels[t]}</button>
        ))}
      </div>
      {q.isLoading && <Loading />}
      {q.error && <ErrorState message={errorMessage(q.error)} onRetry={() => q.refetch()} />}
      {q.data && <Body tab={tab} d={q.data} />}
    </div>
  );
}
