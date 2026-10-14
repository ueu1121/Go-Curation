import React, { useState } from "react";
import { useCurator } from "@/components/curator/CuratorContext";
import { REFINEMENTS, RefineKey } from "@/lib/refine";

export function RefineChips({ active, setActive }: { active: RefineKey[]; setActive: (a: RefineKey[]) => void }) {
  const curator = useCurator();
  const [noMore, setNoMore] = useState(false);
  const toggle = (k: RefineKey) => setActive(active.includes(k) ? active.filter((x) => x !== k) : [...active, k]);
  const labels = REFINEMENTS.filter((r) => active.includes(r.key)).map((r) => r.label.toLowerCase());
  return (
    <div className="mt-3 space-y-3 rounded-2xl border border-stone-200 bg-white p-4 fade-up" data-testid="refine-panel">
      <p className="text-sm text-stone-600">These filter the cards already here, for this session only. Unknown data never counts as a match.</p>
      <div className="flex flex-wrap gap-2">
        {REFINEMENTS.map((r) => (
          <button key={r.key} data-testid={`refine-chip-${r.key}`} aria-pressed={active.includes(r.key)} onClick={() => toggle(r.key)}
            className={`chip ${active.includes(r.key) ? "chip-on" : ""}`}>{r.label}</button>
        ))}
        <button data-testid="refine-chip-another" className="chip" onClick={() => setNoMore(true)}>Another option</button>
      </div>
      {noMore && (
        <p className="text-sm text-[#8E4229]" data-testid="refine-another-note">
          There are no extra options beyond this batch. Phase 1 does not generate new suggestions.
        </p>
      )}
      {active.length > 0 && (
        <button data-testid="refine-save-pref-btn" className="btn-ghost"
          onClick={() => curator.open(undefined, `We prefer ${labels.join(" and ")} outings`)}>
          Save this as a preference… (you'll confirm first)
        </button>
      )}
    </div>
  );
}
