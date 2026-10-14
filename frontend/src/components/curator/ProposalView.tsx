import React, { useState } from "react";
import type { CuratorInput, ProposedChange } from "@/api/types";
import { Pill } from "@/components/Bits";
import { humanize } from "@/lib/format";

export type Edits = Record<string, { selected: boolean; payload: Record<string, string> }>;

function Toggle({ value, options, onChange, testId }: {
  value: string; options: [string, string][]; onChange: (v: string) => void; testId: string;
}) {
  return (
    <div className="inline-flex rounded-full border border-stone-300 bg-white p-0.5" role="radiogroup">
      {options.map(([v, label]) => (
        <button key={v} role="radio" aria-checked={value === v} data-testid={`${testId}-${v}`} onClick={() => onChange(v)}
          className={`rounded-full px-3 py-1.5 text-xs font-medium ${value === v ? "bg-[#2D4A3E] text-white" : "text-stone-600"}`}>
          {label}
        </button>
      ))}
    </div>
  );
}

function Answer({ change }: { change: ProposedChange }) {
  const found: { title: string; dataset: string }[] = change.payload.answer || [];
  if (!found.length)
    return <p className="text-sm text-stone-600">Nothing matching is stored yet. No live search runs in Phase 1 — you can queue a research request below.</p>;
  return (
    <ul className="text-sm text-stone-700 list-disc pl-5">
      {found.map((f, i) => <li key={i}>{f.title} {f.dataset === "demo" && <Pill tone="demo">DEMO</Pill>}</li>)}
    </ul>
  );
}

function ChangeRow({ change, edit, onEdit }: {
  change: ProposedChange; edit: Edits[string]; onEdit: (e: Edits[string]) => void;
}) {
  const set = (k: string, v: string) => onEdit({ ...edit, payload: { ...edit.payload, [k]: v } });
  const scope = edit.payload.scope ?? change.payload.scope;
  const audience = edit.payload.audience ?? change.payload.audience;
  return (
    <li className="rounded-xl border border-stone-200 bg-white p-3" data-testid={`proposed-change-${change.id}`}>
      <label className="flex items-start gap-3">
        <input type="checkbox" className="mt-1 h-5 w-5 accent-[#2D4A3E]" checked={edit.selected}
          data-testid={`proposed-change-toggle-${change.id}`} onChange={(e) => onEdit({ ...edit, selected: e.target.checked })} />
        <span>
          <span className="block text-[15px] text-stone-800">{change.summary}</span>
          <span className="text-xs text-stone-500">{humanize(change.type)}</span>
        </span>
      </label>
      {change.type === "answer_question" && <div className="mt-2 pl-8"><Answer change={change} /></div>}
      {change.editable.includes("text") && (
        <div className="mt-3 pl-8">
          <label className="text-xs text-stone-600" htmlFor={`text-${change.id}`}>Wording to save (edit if it's not quite right)</label>
          <input id={`text-${change.id}`} data-testid={`proposed-text-${change.id}`} className="input mt-1" maxLength={300}
            value={edit.payload.text ?? change.payload.text ?? ""} onChange={(e) => set("text", e.target.value)} />
        </div>
      )}
      {change.editable.some((k) => k === "scope" || k === "audience") && (
        <div className="mt-3 flex flex-wrap gap-2 pl-8">
          {change.editable.includes("scope") && (
            <Toggle testId={`scope-${change.id}`} value={scope} onChange={(v) => set("scope", v)}
              options={[["today", "Today only"], ["permanent", "Ongoing"]]} />
          )}
          {change.editable.includes("audience") && (
            <Toggle testId={`audience-${change.id}`} value={audience} onChange={(v) => set("audience", v)}
              options={[["shared", "Both of us"], ["personal", "Just me"]]} />
          )}
        </div>
      )}
      {scope === "permanent" && audience === "shared" && change.editable.includes("audience") && (
        <p className="mt-2 pl-8 text-xs text-[#8E4229]">Shared ongoing preferences wait for the other participant to accept.</p>
      )}
    </li>
  );
}

export function initialEdits(input: CuratorInput): Edits {
  return Object.fromEntries(input.proposed_changes.map((c) => [c.id, { selected: c.selected, payload: {} }]));
}

export function ProposalView({ input, edits, setEdits }: {
  input: CuratorInput; edits: Edits; setEdits: (e: Edits) => void;
}) {
  const [showOriginal] = useState(true);
  return (
    <div className="space-y-3" data-testid="curator-proposal">
      {showOriginal && (
        <blockquote className="border-l-2 border-[#C76B4B] pl-3 text-sm italic text-stone-600" data-testid="curator-original-text">
          “{input.original_text}”
        </blockquote>
      )}
      <div className="flex flex-wrap items-center gap-2">
        <Pill tone="warn" testId="curator-interpreter-label">{input.live_ai ? "Live AI interpretation" : "Guided interpretation — live AI not connected"}</Pill>
        {input.intents.map((i) => <Pill key={i} tone="neutral">{humanize(i)}</Pill>)}
      </div>
      <ul className="space-y-2">
        {input.proposed_changes.map((c) => (
          <ChangeRow key={c.id} change={c} edit={edits[c.id]} onEdit={(e) => setEdits({ ...edits, [c.id]: e })} />
        ))}
      </ul>
    </div>
  );
}
