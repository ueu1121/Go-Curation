import React, { useState } from "react";
import { Info, SlidersHorizontal, Sunrise, Sun } from "lucide-react";
import type { Batch, TodayResponse } from "@/api/types";
import { EmptyState, ErrorState, Loading, PageHeader, Pill } from "@/components/Bits";
import { ExcursionCard } from "@/components/ExcursionCard";
import { RefineChips } from "@/components/RefineChips";
import { useCurator } from "@/components/curator/CuratorContext";
import { errorMessage } from "@/api/client";
import { applyRefinements, REFINEMENTS, RefineKey } from "@/lib/refine";
import { formatLocalDate, formatLocalDateTime } from "@/lib/format";
import { useGet } from "@/lib/useGet";

function BatchSection({ batch, active, onClear }: { batch: Batch; active: RefineKey[]; onClear: () => void }) {
  const curator = useCurator();
  const { kept, hiddenUnknown } = applyRefinements(batch.items, active);
  const Icon = batch.slot === "morning" ? Sunrise : Sun;
  const labels = REFINEMENTS.filter((r) => active.includes(r.key)).map((r) => r.label.toLowerCase()).join(", ");
  return (
    <section className="mb-10" data-testid={`batch-${batch.slot}`}>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="flex items-center gap-2 font-serif text-xl text-stone-900"><Icon className="h-5 w-5 text-[#C76B4B]" />
          {batch.slot === "morning" ? "Morning" : "Midday"} batch</h2>
        <span className="text-xs text-stone-500">{batch.dataset === "demo" ? "Synthetic demo" : formatLocalDateTime(batch.published_at)}</span>
      </div>
      {batch.status === "insufficient_candidates" && (
        <EmptyState testId="insufficient-candidates" title="Not enough qualified options">
          {batch.note || "Fewer than two options passed the publishing rules, so nothing was padded in."}
        </EmptyState>
      )}
      {active.length > 0 && kept.length === 0 && batch.items.length > 0 && (
        <EmptyState testId={`refine-empty-${batch.slot}`} title="No cards match these filters">
          {hiddenUnknown > 0 && <p>{hiddenUnknown} card(s) hidden because the data needed to judge is unknown.</p>}
          <p className="mt-1">No new options are generated in Phase 1.</p>
          <div className="mt-4 flex flex-wrap justify-center gap-2">
            <button data-testid={`refine-clear-${batch.slot}`} className="btn-secondary" onClick={onClear}>Remove filters</button>
            <button data-testid={`refine-research-${batch.slot}`} className="btn-ghost"
              onClick={() => curator.open(undefined, `Could you research something ${labels} for a future outing?`)}>Ask for research…</button>
          </div>
        </EmptyState>
      )}
      <div className="space-y-6">{kept.map((item, i) => <ExcursionCard key={item.id} item={item} index={i} />)}</div>
      {active.length > 0 && kept.length > 0 && hiddenUnknown > 0 && (
        <p className="mt-3 text-sm text-stone-500">{hiddenUnknown} more hidden because their data is unknown — not because they fail the filter.</p>
      )}
    </section>
  );
}

export default function Today() {
  const q = useGet<TodayResponse>("today", "/board/today");
  const [active, setActive] = useState<RefineKey[]>([]);
  const [showRefine, setShowRefine] = useState(false);
  if (q.isLoading) return <Loading label="Loading today's board" />;
  if (q.error || !q.data) return <ErrorState message={errorMessage(q.error)} onRetry={() => q.refetch()} />;
  const d = q.data;
  return (
    <div>
      <PageHeader eyebrow={formatLocalDate(d.local_date)} title="Today's options">
        A small set to choose from. Your window is roughly 1–9 PM — nothing needs to fill it.
      </PageHeader>
      <div className="mb-6 flex items-start gap-3 rounded-2xl bg-[#F5F3ED] p-4 text-sm text-stone-700" data-testid="phase-notice">
        <Info className="mt-0.5 h-5 w-5 shrink-0 text-[#2D4A3E]" />
        <div>
          <p>{d.phase_notice}</p>
          {d.mode === "demo" && <p className="mt-1"><Pill tone="demo" testId="demo-mode-banner">Showing demo examples</Pill> These are synthetic and exist only to test the board.</p>}
        </div>
      </div>
      {d.mode !== "empty" && (
        <div className="mb-6">
          <button data-testid="refine-toggle-btn" aria-expanded={showRefine} onClick={() => setShowRefine(!showRefine)} className="btn-ghost">
            <SlidersHorizontal className="h-4 w-4" /> Refine these options{active.length ? ` (${active.length})` : ""}
          </button>
          {showRefine && <RefineChips active={active} setActive={setActive} />}
        </div>
      )}
      {d.mode === "empty" && (
        <EmptyState testId="today-empty" icon={<Sunrise className="h-6 w-6" />} title="No batch for today yet">
          Batches appear here once options are published. Live discovery isn't running in Phase 1, so nothing is invented to fill the gap.
        </EmptyState>
      )}
      {d.batches.map((b) => <BatchSection key={b.id} batch={b} active={active} onClear={() => setActive([])} />)}
    </div>
  );
}
