import React, { useState } from "react";
import { Bookmark, ChevronDown, MessageCircle } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { errorMessage, post } from "@/api/client";
import type { BatchItem } from "@/api/types";
import { DemoBadge, Pill } from "@/components/Bits";
import { CardDetails } from "@/components/CardDetails";
import { PlanControls } from "@/components/PlanControls";
import { ReactionBar, ReactionSummary } from "@/components/ReactionBar";
import { useCurator } from "@/components/curator/CuratorContext";
import { useMe } from "@/context/AuthContext";
import { costLabel, humanize, travelLabel, whenLabel } from "@/lib/format";
import type { Experience } from "@/api/types";

function practical(e: Experience): { known: string[]; missing: string[] } {
  const known: string[] = [];
  const missing: string[] = [];
  const add = (ok: boolean, label: string, name: string) => (ok ? known.push(label) : missing.push(name));
  add(e.cost_for_two.status !== "unknown" && e.cost_for_two.max != null, costLabel(e.cost_for_two), "cost");
  add(travelLabel(e.travel) !== "Travel unknown", travelLabel(e.travel), "travel time");
  add(!!e.crowd_level, e.crowd_guidance || "", "crowds");
  add(!!e.duration_estimate, e.duration_estimate || "", "visit length");
  return { known, missing };
}

function PracticalLine({ e, id }: { e: Experience; id: string }) {
  const { known, missing } = practical(e);
  return (
    <p className="mt-3 text-sm text-stone-600" data-testid={`practical-summary-${id}`}>
      {known.length > 0 && <span className="block">{known.join(" · ")}</span>}
      {missing.length > 0 && <span className="italic text-stone-500">Not yet known: {missing.join(", ")}</span>}
    </p>
  );
}

function SaveButton({ item }: { item: BatchItem }) {
  const { member } = useMe();
  const qc = useQueryClient();
  const saved = item.saved_by.includes(member.id);
  const toggle = async () => {
    try {
      const r = await post<{ saved: boolean }>("/interests", { experience_id: item.experience_id });
      toast.success(r.saved ? "Saved for later — not a plan" : "Removed from saved");
      qc.invalidateQueries({ queryKey: ["today"] });
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };
  return (
    <button data-testid={`save-interest-${item.id}`} aria-pressed={saved} onClick={toggle} className="btn-ghost">
      <Bookmark className={`h-4 w-4 ${saved ? "fill-[#2D4A3E]" : ""}`} /> {saved ? "Saved" : "Save for later"}
    </button>
  );
}

export function ExcursionCard({ item, index }: { item: BatchItem; index: number }) {
  const [open, setOpen] = useState(false);
  const curator = useCurator();
  const e = item.snapshot;
  return (
    <article data-testid={`excursion-card-${item.id}`} className="card fade-up" style={{ animationDelay: `${index * 70}ms` }}>
      <div className="flex flex-wrap items-center gap-2">
        {item.dataset === "demo" && <DemoBadge testId={`demo-badge-${item.id}`} />}
        <Pill tone="forest">{humanize(e.category)}</Pill>
        <Pill tone="neutral">{e.effort ?? "effort unknown"}</Pill>
      </div>
      <h3 className="mt-3 font-serif text-2xl leading-snug text-stone-900" data-testid={`card-title-${item.id}`}>{e.title}</h3>
      <p className="mt-1 text-[15px] leading-relaxed text-stone-700">{e.why_now || "Why-now not yet researched."}</p>
      <p className="mt-2 text-sm font-medium text-[#8E4229]">{whenLabel(e)}{e.suggested_window ? ` · ${e.suggested_window}` : ""}</p>
      <PracticalLine e={e} id={item.id} />
      <div className="mt-4"><ReactionSummary item={item} /></div>
      <div className="mt-4 space-y-4">
        <ReactionBar item={item} />
        <PlanControls item={item} />
      </div>
      <button data-testid={`card-expand-${item.id}`} aria-expanded={open} onClick={() => setOpen(!open)}
        className="mt-4 flex w-full items-center justify-between rounded-xl bg-[#F5F3ED] px-4 py-3 text-left text-sm font-medium text-stone-800">
        {open ? "Hide details" : "View details"}
        <ChevronDown className={`h-5 w-5 transition-transform duration-300 ${open ? "rotate-180" : ""}`} />
      </button>
      {open && <div className="mt-4 fade-up"><CardDetails item={item} /></div>}
      <div className="mt-4 flex flex-wrap gap-2 border-t border-stone-200 pt-3">
        <SaveButton item={item} />
        <button data-testid={`card-tell-curator-${item.id}`} className="btn-ghost"
          onClick={() => curator.open({ batch_item_id: item.id, title: e.title })}>
          <MessageCircle className="h-4 w-4" /> Tell the curator about this
        </button>
      </div>
    </article>
  );
}
