import React, { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Sparkles } from "lucide-react";
import { toast } from "sonner";
import { errorMessage, patch } from "@/api/client";
import type { Insight } from "@/api/types";
import { EmptyState, ErrorState, Loading, PageHeader, Pill } from "@/components/Bits";
import { useAuth } from "@/context/AuthContext";
import { formatLocalDateTime } from "@/lib/format";
import { useGet } from "@/lib/useGet";

function InsightCard({ ins }: { ins: Insight }) {
  const qc = useQueryClient();
  const { nameOf, me } = useAuth();
  const [editing, setEditing] = useState(false);
  const [text, setText] = useState(ins.text);
  const act = async (action: "accept" | "dismiss" | "edit") => {
    try {
      await patch(`/insights/${ins.id}`, { action, text: action === "edit" ? text : null });
      setEditing(false);
      qc.invalidateQueries({ queryKey: ["insights"] });
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };
  const mineProposal = me && ins.member_id === me.member.id;
  const canAccept = ins.kind === "tentative" || (ins.status === "awaiting_partner" && !mineProposal);
  return (
    <li className="card" data-testid={`insight-${ins.id}`}>
      <div className="flex flex-wrap gap-2">
        <Pill tone={ins.audience === "shared" ? "forest" : "neutral"}>{ins.audience === "shared" ? "Both of us" : `Just ${nameOf(ins.member_id)}`}</Pill>
        {ins.status === "awaiting_partner" && <Pill tone="warn" testId={`insight-awaiting-${ins.id}`}>Awaiting the other participant</Pill>}
        {ins.expired && <Pill tone="muted">Expired</Pill>}
      </div>
      {editing ? (
        <input data-testid={`insight-edit-input-${ins.id}`} className="input mt-2" value={text} onChange={(e) => setText(e.target.value)} />
      ) : <p className="mt-2 text-[15px] text-stone-800">{ins.text}</p>}
      <p className="mt-1 text-xs text-stone-500">
        From {nameOf(ins.member_id)} · {formatLocalDateTime(ins.created_at)}{ins.reason ? ` · Why: ${ins.reason}` : ""}
        {ins.expires_at && ` · until ${formatLocalDateTime(ins.expires_at)}`}
      </p>
      <div className="mt-3 flex flex-wrap gap-2">
        {canAccept && <button data-testid={`insight-accept-${ins.id}`} className="btn-primary" onClick={() => act("accept")}>Accept</button>}
        {editing ? <button data-testid={`insight-save-${ins.id}`} className="btn-secondary" onClick={() => act("edit")}>Save</button>
          : <button data-testid={`insight-edit-${ins.id}`} className="btn-ghost" onClick={() => setEditing(true)}>Edit</button>}
        <button data-testid={`insight-dismiss-${ins.id}`} className="btn-ghost" onClick={() => act("dismiss")}>{ins.kind === "tentative" ? "Dismiss" : "Remove"}</button>
      </div>
    </li>
  );
}

function Group({ title, note, items, testId }: { title: string; note: string; items: Insight[]; testId: string }) {
  return (
    <section data-testid={testId}>
      <h2 className="font-serif text-xl text-stone-900">{title}</h2>
      <p className="mb-3 text-sm text-stone-600">{note}</p>
      {items.length ? <ul className="space-y-3">{items.map((i) => <InsightCard key={i.id} ins={i} />)}</ul>
        : <p className="text-sm italic text-stone-500">Nothing here yet.</p>}
    </section>
  );
}

export default function Learned() {
  const q = useGet<{ items: Insight[] }>("insights", "/insights");
  const items = q.data?.items ?? [];
  return (
    <div className="space-y-8">
      <PageHeader eyebrow="Explainable memory" title="What the curator has learned">
        Every entry comes from something one of you said and confirmed. Nothing is learned from demo cards.
      </PageHeader>
      {q.isLoading && <Loading />}
      {q.error && <ErrorState message={errorMessage(q.error)} onRetry={() => q.refetch()} />}
      {q.data && items.length === 0 && (
        <EmptyState testId="learned-empty" icon={<Sparkles className="h-6 w-6" />} title="Nothing learned yet">
          Tell the curator about a preference or an outing, then confirm it.
        </EmptyState>
      )}
      {items.length > 0 && <>
        <Group testId="learned-confirmed" title="Confirmed preferences" note="Explicit and ongoing. These take priority over anything inferred."
          items={items.filter((i) => i.kind === "confirmed")} />
        <Group testId="learned-temporary" title="Temporary constraints" note="Today-only requests. They expire on their own."
          items={items.filter((i) => i.kind === "temporary")} />
        <Group testId="learned-tentative" title="Tentative observations" note="Possible patterns. Not rules until you accept them."
          items={items.filter((i) => i.kind === "tentative")} />
      </>}
    </div>
  );
}
