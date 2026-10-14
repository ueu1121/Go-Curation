import React, { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { CalendarCheck, Star } from "lucide-react";
import { toast } from "sonner";
import { errorMessage, post } from "@/api/client";
import type { BatchItem } from "@/api/types";
import { useMe } from "@/context/AuthContext";

function SharedState({ item }: { item: BatchItem }) {
  const { members } = useMe();
  if (item.shared_state === "both_interested")
    return <p data-testid={`shared-state-${item.id}`} className="state-banner bg-[#E6EDE9] text-[#2D4A3E]">Both interested</p>;
  if (item.shared_state === "disagreement") {
    const views = members.map((m) => `${m.display_name}: ${item.reactions[m.id]?.reaction.replace(/_/g, " ") ?? "—"}`);
    return (
      <p data-testid={`shared-state-${item.id}`} className="state-banner bg-[#F7E7E0] text-[#8E4229]">
        Different views — {views.join(" · ")}. No automatic winner; decide together.
      </p>
    );
  }
  return null;
}

export function RatingForm({ visitId, onDone }: { visitId: string; onDone?: () => void }) {
  const [rating, setRating] = useState(0);
  const [notes, setNotes] = useState("");
  const save = async () => {
    try {
      await post(`/visits/${visitId}/feedback`, { rating: rating || null, notes: notes || null });
      toast.success("Your feedback is saved");
      onDone?.();
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };
  return (
    <div className="space-y-2 rounded-xl bg-[#F5F3ED] p-3" data-testid={`rating-form-${visitId}`}>
      <p className="text-sm text-stone-700">Your rating (each participant rates separately)</p>
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((n) => (
          <button key={n} data-testid={`rating-star-${n}-${visitId}`} aria-label={`${n} of 5`} onClick={() => setRating(n)}
            className="flex h-11 w-11 items-center justify-center rounded-full hover:bg-white">
            <Star className={`h-6 w-6 ${n <= rating ? "fill-[#C76B4B] text-[#C76B4B]" : "text-stone-400"}`} />
          </button>
        ))}
      </div>
      <textarea data-testid={`rating-notes-${visitId}`} className="input min-h-[72px]" placeholder="Notes (optional)"
        value={notes} onChange={(e) => setNotes(e.target.value)} />
      <button data-testid={`rating-save-${visitId}`} className="btn-primary" onClick={save}>Save feedback</button>
    </div>
  );
}

function CompleteForm({ planId, onDone }: { planId: string; onDone: (visitId: string) => void }) {
  const { environment } = useMe();
  const [date, setDate] = useState(environment.local_date);
  const [notes, setNotes] = useState("");
  const submit = async () => {
    try {
      const v = await post<{ id: string }>("/visits", { plan_id: planId, visit_date: date || null, notes: notes || null });
      onDone(v.id);
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };
  return (
    <div className="space-y-2 rounded-xl bg-[#F5F3ED] p-3 fade-up">
      <label className="text-sm text-stone-700" htmlFor={`visit-date-${planId}`}>When did you go? (leave empty if unsure)</label>
      <input id={`visit-date-${planId}`} data-testid={`visit-date-${planId}`} type="date" className="input" value={date}
        onChange={(e) => setDate(e.target.value)} />
      <textarea data-testid={`visit-notes-${planId}`} className="input min-h-[64px]" placeholder="Completion notes (optional)"
        value={notes} onChange={(e) => setNotes(e.target.value)} />
      <button data-testid={`visit-submit-${planId}`} className="btn-primary" onClick={submit}>Confirm we went</button>
    </div>
  );
}

export function PlanControls({ item }: { item: BatchItem }) {
  const qc = useQueryClient();
  const [completing, setCompleting] = useState(false);
  const [visitId, setVisitId] = useState<string | null>(null);
  const refresh = () => qc.invalidateQueries({ queryKey: ["today"] });
  const act = async (fn: () => Promise<unknown>, msg: string) => {
    try {
      await fn();
      toast.success(msg);
      await refresh();
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };
  const plan = item.plan;
  return (
    <div className="space-y-3">
      <SharedState item={item} />
      {!plan && (
        <button data-testid={`select-plan-${item.id}`} className="btn-primary w-full"
          onClick={() => act(() => post("/plans", { batch_item_id: item.id }), "Selected as your plan — not booked or completed")}>
          <CalendarCheck className="h-5 w-5" /> Select as our plan
        </button>
      )}
      {plan?.status === "selected" && (
        <div className="space-y-2">
          <p data-testid={`plan-status-${item.id}`} className="state-banner bg-[#2D4A3E] text-white">Our plan · selected (not completed, nothing booked)</p>
          <div className="grid grid-cols-2 gap-2">
            <button data-testid={`complete-plan-${item.id}`} className="btn-secondary" onClick={() => setCompleting(true)}>Mark completed</button>
            <button data-testid={`cancel-plan-${item.id}`} className="btn-ghost"
              onClick={() => act(() => post(`/plans/${plan.id}/cancel`), "Plan cancelled")}>Cancel plan</button>
          </div>
          {completing && <CompleteForm planId={plan.id} onDone={(id) => { setVisitId(id); setCompleting(false); refresh(); }} />}
        </div>
      )}
      {plan?.status === "completed" && (
        <div className="space-y-2">
          <p data-testid={`plan-status-${item.id}`} className="state-banner bg-[#E6EDE9] text-[#2D4A3E]">Completed — recorded in History</p>
          {(visitId || plan.visit_id) && <RatingForm visitId={(visitId || plan.visit_id) as string} />}
        </div>
      )}
    </div>
  );
}
