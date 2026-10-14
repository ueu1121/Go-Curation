import React, { useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Loader2, Sparkles, X } from "lucide-react";
import { toast } from "sonner";
import { errorMessage, post } from "@/api/client";
import type { CuratorInput } from "@/api/types";
import type { CuratorRef } from "@/components/curator/CuratorContext";
import { Edits, initialEdits, ProposalView } from "@/components/curator/ProposalView";

const EXAMPLES = [
  "Something easy this afternoon, not another waterfall.",
  "We drove through Cambridge, but we did not visit attractions.",
  "Is there a BBQ event coming up?",
  "That was nice, but the walking was too much.",
];

function Clarify({ input, onPick }: { input: CuratorInput; onPick: (id: string) => void }) {
  const c = input.clarification!;
  return (
    <div className="space-y-3 rounded-xl bg-[#F7E7E0] p-4" data-testid="curator-clarification">
      <p className="font-medium text-[#8E4229]">{c.question}</p>
      <div className="grid gap-2">
        {c.choices.map((ch) => (
          <button key={ch.id} data-testid={`clarify-choice-${ch.id}`} className="btn-secondary justify-start text-left" onClick={() => onPick(ch.id)}>
            {ch.label}
          </button>
        ))}
      </div>
    </div>
  );
}

function Result({ input }: { input: CuratorInput }) {
  return (
    <div className="rounded-xl bg-[#E6EDE9] p-4 text-[#2D4A3E]" data-testid="curator-result">
      <p className="flex items-center gap-2 font-medium"><CheckCircle2 className="h-5 w-5" />
        {input.status === "applied" ? `Saved ${input.applied_changes.length} change(s).` : input.status === "cancelled" ? "Cancelled — your original message is still kept." : "Kept your message without applying changes."}
      </p>
      <ul className="mt-2 list-disc pl-6 text-sm">
        {input.applied_changes.map((a) => <li key={a.change_id}>{a.type.replace(/_/g, " ")}</li>)}
      </ul>
    </div>
  );
}

export function CuratorSheet({ contextRef, prefill, onClose }: { contextRef?: CuratorRef; prefill?: string; onClose: () => void }) {
  const [text, setText] = useState(prefill || "");
  const [busy, setBusy] = useState(false);
  const [input, setInput] = useState<CuratorInput | null>(null);
  const [edits, setEdits] = useState<Edits>({});
  const qc = useQueryClient();
  const ref = useRef<HTMLTextAreaElement>(null);
  useEffect(() => {
    ref.current?.focus();
  }, []);

  const run = async (fn: () => Promise<CuratorInput>) => {
    setBusy(true);
    try {
      const r = await fn();
      setInput(r);
      setEdits(initialEdits(r));
      if (r.status === "applied") qc.invalidateQueries();
    } catch (e) {
      toast.error(errorMessage(e));
    } finally {
      setBusy(false);
    }
  };
  const submit = () => run(() => post("/inputs", { text, context_ref: contextRef?.batch_item_id ? { batch_item_id: contextRef.batch_item_id } : null }));
  const confirm = () => run(() => post(`/inputs/${input!.id}/confirm`, {
    changes: Object.entries(edits).map(([id, e]) => ({ id, selected: e.selected, payload: e.payload })),
  }));
  const done = input && ["applied", "saved_unapplied", "cancelled"].includes(input.status);

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-stone-900/40 sm:items-center" role="dialog" aria-modal="true" aria-label="Tell the curator">
      <div className="max-h-[92vh] w-full max-w-lg overflow-y-auto rounded-t-3xl bg-[#FDFBF7] p-6 shadow-xl sm:rounded-3xl sheet-up" data-testid="curator-sheet">
        <div className="mb-4 flex items-start justify-between">
          <div>
            <p className="eyebrow">Tell the curator</p>
            <h2 className="font-serif text-2xl text-stone-900">What's on your mind?</h2>
            {contextRef?.title && <p className="text-sm text-stone-600">About: {contextRef.title}</p>}
          </div>
          <button data-testid="curator-close-btn" aria-label="Close" onClick={onClose} className="flex h-11 w-11 items-center justify-center rounded-full hover:bg-stone-100"><X className="h-5 w-5" /></button>
        </div>
        {!input && (
          <div className="space-y-3">
            <textarea ref={ref} data-testid="curator-input" value={text} onChange={(e) => setText(e.target.value)} maxLength={2000}
              className="input min-h-[120px] text-base" placeholder="Plain words or a link — e.g. “Nothing expensive today.”" />
            <div className="flex flex-wrap gap-2">
              {EXAMPLES.map((ex) => (
                <button key={ex} className="chip" onClick={() => setText(ex)} data-testid="curator-example-chip">{ex}</button>
              ))}
            </div>
            <p className="text-xs text-stone-500">Phase 1 uses a guided, rule-based reader — not live AI. Nothing changes until you confirm.</p>
            <button data-testid="curator-submit-btn" disabled={!text.trim() || busy} onClick={submit} className="btn-primary w-full">
              {busy ? <Loader2 className="h-5 w-5 animate-spin" /> : <Sparkles className="h-5 w-5" />} Show me what you understood
            </button>
          </div>
        )}
        {input && input.status === "needs_clarification" && (
          <div className="space-y-4">
            <ProposalView input={input} edits={edits} setEdits={setEdits} />
            <Clarify input={input} onPick={(id) => run(() => post(`/inputs/${input.id}/clarify`, { choice_id: id }))} />
          </div>
        )}
        {input && input.status === "awaiting_confirmation" && (
          <div className="space-y-4">
            <ProposalView input={input} edits={edits} setEdits={setEdits} />
            <div className="grid grid-cols-2 gap-2">
              <button data-testid="curator-confirm-btn" disabled={busy} onClick={confirm} className="btn-primary">Confirm & save</button>
              <button data-testid="curator-cancel-btn" disabled={busy} onClick={() => run(() => post(`/inputs/${input.id}/cancel`))} className="btn-ghost">Cancel</button>
            </div>
          </div>
        )}
        {done && (
          <div className="space-y-3">
            <Result input={input!} />
            <button data-testid="curator-new-btn" className="btn-secondary w-full" onClick={() => { setInput(null); setText(""); }}>Tell it something else</button>
          </div>
        )}
      </div>
    </div>
  );
}
