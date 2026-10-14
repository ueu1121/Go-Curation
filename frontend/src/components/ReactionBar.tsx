import React, { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Check, Clock, X } from "lucide-react";
import { errorMessage, post } from "@/api/client";
import type { BatchItem, Reaction } from "@/api/types";
import { useAuth, useMe } from "@/context/AuthContext";
import { toast } from "sonner";

const OPTIONS: { value: Reaction; label: string; icon: React.ReactNode }[] = [
  { value: "interested", label: "Interested", icon: <Check className="h-4 w-4" /> },
  { value: "not_today", label: "Not today", icon: <Clock className="h-4 w-4" /> },
  { value: "not_for_us", label: "Not for us", icon: <X className="h-4 w-4" /> },
];
const LABEL: Record<Reaction, string> = { interested: "Interested", not_today: "Not today", not_for_us: "Not for us" };

export function ReactionSummary({ item }: { item: BatchItem }) {
  const { members } = useMe();
  return (
    <div className="flex flex-wrap gap-2" data-testid={`reaction-summary-${item.id}`}>
      {members.map((m) => {
        const r = item.reactions[m.id];
        return (
          <span key={m.id} className={`rounded-full px-2.5 py-1 text-xs ${r ? "bg-[#E6EDE9] text-[#2D4A3E]" : "bg-stone-100 text-stone-500"}`}>
            {m.display_name}: {r ? LABEL[r.reaction] : "no reaction yet"}
          </span>
        );
      })}
    </div>
  );
}

export function ReactionBar({ item }: { item: BatchItem }) {
  const { me } = useAuth();
  const qc = useQueryClient();
  const [reason, setReason] = useState("");
  const [askReason, setAskReason] = useState(false);
  const mine = me ? item.reactions[me.member.id]?.reaction : undefined;

  const send = async (reaction: Reaction, why?: string) => {
    try {
      await post("/reactions", { batch_item_id: item.id, reaction, reason: why || null });
      setAskReason(false);
      await qc.invalidateQueries({ queryKey: ["today"] });
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };

  return (
    <div className="space-y-3">
      <p className="eyebrow">Your reaction</p>
      <div className="grid grid-cols-3 gap-2" role="group" aria-label="Your reaction">
        {OPTIONS.map((o) => (
          <button
            key={o.value}
            data-testid={`reaction-${o.value}-${item.id}`}
            aria-pressed={mine === o.value}
            onClick={() => (o.value === "not_for_us" ? setAskReason(true) : send(o.value))}
            className={`reaction-btn ${mine === o.value ? `reaction-on-${o.value}` : ""}`}
          >
            {o.icon}
            <span>{o.label}</span>
          </button>
        ))}
      </div>
      {askReason && (
        <div className="rounded-xl bg-[#F5F3ED] p-3 space-y-2 fade-up">
          <label className="text-sm text-stone-700" htmlFor={`reason-${item.id}`}>Optional reason (does not block it permanently)</label>
          <input id={`reason-${item.id}`} data-testid={`not-for-us-reason-${item.id}`} value={reason}
            onChange={(e) => setReason(e.target.value)} className="input" placeholder="e.g. too far for a weekday" />
          <div className="flex gap-2">
            <button data-testid={`not-for-us-confirm-${item.id}`} className="btn-primary" onClick={() => send("not_for_us", reason)}>Save “Not for us”</button>
            <button className="btn-ghost" onClick={() => setAskReason(false)}>Cancel</button>
          </div>
        </div>
      )}
    </div>
  );
}
