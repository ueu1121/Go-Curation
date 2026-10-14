import React, { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Lightbulb } from "lucide-react";
import { toast } from "sonner";
import { errorMessage, post } from "@/api/client";
import type { Idea, IdeaStatus } from "@/api/types";
import { EmptyState, ErrorState, Loading, PageHeader, Pill } from "@/components/Bits";
import { useAuth } from "@/context/AuthContext";
import { formatLocalDate, formatLocalDateTime, humanize } from "@/lib/format";
import { useGet } from "@/lib/useGet";

const TONE: Record<IdeaStatus, "neutral" | "forest" | "clay" | "warn" | "muted"> = {
  queued: "neutral", researching: "warn", eligible: "forest", not_selected: "clay", needs_information: "warn", expired: "muted",
};

function IdeaForm() {
  const qc = useQueryClient();
  const [f, setF] = useState({ description: "", url: "", location: "", preferred_date: "" });
  const [error, setError] = useState("");
  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setF({ ...f, [k]: e.target.value });
  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await post("/ideas", { description: f.description, url: f.url || null, location: f.location || null,
        preferred_date: f.preferred_date || null });
      setF({ description: "", url: "", location: "", preferred_date: "" });
      toast.success("Idea queued for research");
      qc.invalidateQueries({ queryKey: ["ideas"] });
    } catch (err) {
      setError(errorMessage(err).replace(/^Value error, /, ""));
    }
  };
  return (
    <form onSubmit={submit} className="card space-y-3" data-testid="idea-form">
      <label className="block text-sm font-medium text-stone-700" htmlFor="idea-desc">Your idea</label>
      <textarea id="idea-desc" data-testid="idea-description-input" required minLength={3} maxLength={2000} className="input min-h-[90px]"
        value={f.description} onChange={set("description")} placeholder="e.g. That maple syrup demonstration we heard about" />
      <input data-testid="idea-url-input" className="input" type="text" inputMode="url" placeholder="Link (optional)" value={f.url} onChange={set("url")} />
      <div className="grid grid-cols-2 gap-2">
        <input data-testid="idea-location-input" className="input" placeholder="Location (optional)" value={f.location} onChange={set("location")} />
        <input data-testid="idea-date-input" className="input" type="date" aria-label="Preferred date (optional)" value={f.preferred_date} onChange={set("preferred_date")} />
      </div>
      {error && <p data-testid="idea-error" role="alert" className="text-sm text-red-700">Not saved: {error}</p>}
      <button data-testid="idea-submit-btn" className="btn-primary w-full" disabled={f.description.trim().length < 3}>Add to our ideas</button>
      <p className="text-xs text-stone-500">Ideas are never discarded. Research target: 24–48 hours once research is connected (Phase 2).</p>
    </form>
  );
}

function IdeaRow({ idea }: { idea: Idea }) {
  const { nameOf } = useAuth();
  return (
    <li className="card" data-testid={`idea-row-${idea.id}`}>
      <div className="flex flex-wrap items-center gap-2">
        <Pill tone={TONE[idea.status]} testId={`idea-status-${idea.id}`}>{humanize(idea.status)}</Pill>
        {idea.kind !== "idea" && <Pill tone="neutral">{humanize(idea.kind)}</Pill>}
        {idea.overdue && <Pill tone="clay" testId={`idea-overdue-${idea.id}`}>Research overdue</Pill>}
      </div>
      <p className="mt-2 text-[15px] text-stone-800">{idea.description}</p>
      {idea.url && <p className="mt-1 break-all text-sm text-stone-600">Link (unverified): {idea.url}</p>}
      <p className="mt-2 text-xs text-stone-500">
        {nameOf(idea.submitted_by)} · {formatLocalDateTime(idea.submitted_at)} · due by {formatLocalDateTime(idea.research_due_at)}
        {idea.preferred_date && ` · preferred ${formatLocalDate(idea.preferred_date)}`}
      </p>
      {idea.outcome && (
        <p className="mt-2 rounded-lg bg-[#F5F3ED] p-2 text-sm text-stone-700" data-testid={`idea-outcome-${idea.id}`}>
          Outcome: {humanize(idea.outcome.status)}{idea.outcome.reason ? ` — ${idea.outcome.reason}` : ""}
        </p>
      )}
    </li>
  );
}

export default function Ideas() {
  const q = useGet<{ items: Idea[] }>("ideas", "/ideas");
  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Queue" title="Our ideas">Things you'd like the curator to look into.</PageHeader>
      <IdeaForm />
      {q.isLoading && <Loading />}
      {q.error && <ErrorState message={errorMessage(q.error)} onRetry={() => q.refetch()} />}
      {q.data && q.data.items.length === 0 && (
        <EmptyState testId="ideas-empty" icon={<Lightbulb className="h-6 w-6" />} title="No ideas yet">Add one above, or tell the curator.</EmptyState>
      )}
      <ul className="space-y-4">{q.data?.items.map((i) => <IdeaRow key={i.id} idea={i} />)}</ul>
    </div>
  );
}
