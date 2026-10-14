import React, { useState } from "react";
import { ExternalLink } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { errorMessage, post } from "@/api/client";
import type { BatchItem, Evidence } from "@/api/types";
import { Field, Pill, Unknown } from "@/components/Bits";
import { formatLocalDate, formatLocalDateTime, humanize } from "@/lib/format";

const orUnknown = (v: string | null | undefined, label = "Unknown") => (v ? v : <Unknown>{label}</Unknown>);

function EvidenceList({ sources }: { sources: Evidence[] }) {
  if (!sources.length)
    return <Unknown>No evidence sources. {""}This card cannot be published as a researched recommendation.</Unknown>;
  return (
    <ul className="space-y-3">
      {sources.map((s, i) => (
        <li key={s.id || i} className="rounded-xl border border-stone-200 bg-white p-3">
          <p className="text-sm text-stone-800">“{s.supported_claim}”</p>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-stone-500">
            <Pill tone={s.verification_status === "reviewed_supports_claim" ? "forest" : "warn"}>{humanize(s.verification_status)}</Pill>
            <span>{humanize(s.source_type)}</span>
            <span>Checked: {s.reviewed_at || s.retrieved_at ? formatLocalDateTime(s.reviewed_at || s.retrieved_at) : "not recorded"}</span>
          </div>
          {s.url && (
            <a href={s.url} target="_blank" rel="noopener noreferrer nofollow" className="mt-2 inline-flex items-center gap-1 text-sm text-[#2D4A3E] underline">
              {s.title || new URL(s.url).hostname} <ExternalLink className="h-3.5 w-3.5" />
            </a>
          )}
        </li>
      ))}
    </ul>
  );
}

function BlockAction({ item }: { item: BatchItem }) {
  const [confirming, setConfirming] = useState(false);
  const qc = useQueryClient();
  const block = async () => {
    try {
      await post("/exclusions", { scope: "experience", target_id: item.experience_id, label: item.snapshot.title,
        reason: "Blocked from card", temporary: false });
      toast.success("Blocked permanently. You can undo this in Preferences.");
      setConfirming(false);
      qc.invalidateQueries({ queryKey: ["history"] });
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };
  return confirming ? (
    <div className="flex flex-wrap gap-2">
      <button data-testid={`block-confirm-${item.id}`} className="btn-danger" onClick={block}>Yes, never suggest this again</button>
      <button className="btn-ghost" onClick={() => setConfirming(false)}>Keep it</button>
    </div>
  ) : (
    <button data-testid={`block-btn-${item.id}`} className="btn-ghost text-red-700" onClick={() => setConfirming(true)}>Block permanently…</button>
  );
}

export function CardDetails({ item }: { item: BatchItem }) {
  const e = item.snapshot;
  const t = e.travel;
  return (
    <div className="space-y-5" data-testid={`card-details-${item.id}`}>
      <dl className="grid gap-1 sm:grid-cols-2">
        <Field label="Why it's unique">{orUnknown(e.why_unique, "Not yet researched")}</Field>
        <Field label="Why it fits you">{orUnknown(e.fit_explanation)}</Field>
        <Field label="Hidden perk / local advice">{orUnknown(e.hidden_perk, "None found yet")}</Field>
        <Field label="Best timing">{orUnknown(e.best_timing)}</Field>
        <Field label="Expected visit length">{orUnknown(e.duration_estimate)}</Field>
        <Field label="Suggested outing window">{orUnknown(e.suggested_window)}</Field>
        <Field label="Booking">
          {e.booking.required == null ? <Unknown>Booking requirement unknown</Unknown> : e.booking.required ? "Booking required" : "No booking needed"}
          {e.booking.deadline && <> · deadline {formatLocalDate(e.booking.deadline)}</>}
        </Field>
        <Field label="Accessibility & walking">{orUnknown(e.accessibility_notes)}</Field>
        <Field label="Weather">{orUnknown(e.weather_notes, "No weather data connected")}</Field>
        <Field label="Optional nearby backup">{orUnknown(e.nearby_backup, "None suggested")}</Field>
        <Field label="Distance & travel">
          <span className="block">Straight-line: {t.geo_distance_km != null ? `${t.geo_distance_km} km` : <Unknown>unknown</Unknown>}</span>
          <span className="block">Driving: {t.driving_distance_km != null ? `${t.driving_distance_km} km` : <Unknown>unknown</Unknown>}
            {" · "}{t.driving_duration_min != null ? `${t.driving_duration_min} min` : <Unknown>time unknown</Unknown>}</span>
          <span className="block text-xs text-stone-500">From {t.origin_label || "origin not set"} · {t.measurement_source || "no measurement"} · {t.status}</span>
        </Field>
        {(item.novelty_explanation || item.repeat_exception) && (
          <Field label="Why this differs from before">{item.novelty_explanation || item.repeat_exception}</Field>
        )}
      </dl>
      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-xl bg-[#F5F3ED] p-3" data-testid={`fit-score-${item.id}`}>
          <p className="eyebrow">Preference fit</p>
          <p className="font-serif text-2xl text-stone-900">{item.fit_score}<span className="text-sm text-stone-500">/100</span></p>
          <p className="text-xs text-stone-500">How well it suits you — not proof of facts.</p>
          {item.fit_score < 70 && (
            <p className="mt-1 text-xs font-medium text-[#8E4229]" data-testid={`below-threshold-${item.id}`}>
              {item.dataset === "demo" ? "Deliberately below" : "Below"} the 70-point publication threshold
              {item.dataset === "demo" ? " — demo only; the server rejects it as a genuine recommendation." : "."}
            </p>
          )}
        </div>
        <div className="rounded-xl bg-[#F5F3ED] p-3" data-testid={`evidence-status-${item.id}`}>
          <p className="eyebrow">Evidence</p>
          <p className="font-serif text-xl text-stone-900">{humanize(e.evidence_status || (e.evidence.length ? "unreviewed" : "none"))}</p>
          <p className="text-xs text-stone-500">{e.evidence.length} source(s)</p>
        </div>
      </div>
      <div>
        <p className="eyebrow mb-2">Evidence & supported claims</p>
        <EvidenceList sources={e.evidence} />
      </div>
      {e.unknowns.length > 0 && (
        <div>
          <p className="eyebrow mb-2">Still unknown</p>
          <div className="flex flex-wrap gap-2">{e.unknowns.map((u) => <Pill key={u} tone="muted">{u}</Pill>)}</div>
        </div>
      )}
      {e.verification_notes && <p className="text-sm text-stone-600">Verification notes: {e.verification_notes}</p>}
      <BlockAction item={item} />
    </div>
  );
}
