import React from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Bookmark, CalendarDays } from "lucide-react";
import { toast } from "sonner";
import { errorMessage, post } from "@/api/client";
import type { Experience, Occurrence } from "@/api/types";
import { DemoBadge, EmptyState, ErrorState, Loading, PageHeader, Pill } from "@/components/Bits";
import { useMe } from "@/context/AuthContext";
import { costLabel, formatLocalDate, humanize, travelLabel } from "@/lib/format";
import { useGet } from "@/lib/useGet";

interface UpItem { occurrence: Occurrence; experience: Experience; saved_by: string[] }

function UpcomingCard({ it }: { it: UpItem }) {
  const { member, members } = useMe();
  const qc = useQueryClient();
  const e = it.experience;
  const o = it.occurrence;
  const saved = it.saved_by.includes(member.id);
  const toggle = async () => {
    try {
      await post("/interests", { experience_id: e.id });
      qc.invalidateQueries({ queryKey: ["upcoming"] });
    } catch (err) {
      toast.error(errorMessage(err));
    }
  };
  const savers = members.filter((m) => it.saved_by.includes(m.id)).map((m) => m.display_name);
  return (
    <article className="card" data-testid={`upcoming-card-${o.id}`}>
      <div className="flex flex-wrap gap-2">
        {e.dataset === "demo" && <DemoBadge />}
        <Pill tone="forest">{humanize(e.category)}</Pill>
      </div>
      <h3 className="mt-3 font-serif text-xl text-stone-900">{e.title}</h3>
      <p className="mt-1 text-sm text-stone-700">{e.why_now}</p>
      <dl className="mt-3 grid grid-cols-2 gap-3 text-sm">
        <div><dt className="eyebrow">Event date</dt><dd data-testid={`upcoming-date-${o.id}`}>{formatLocalDate(o.start_date)}{o.end_date && o.end_date !== o.start_date ? ` – ${formatLocalDate(o.end_date)}` : ""}</dd></div>
        <div><dt className="eyebrow">Booking deadline</dt><dd data-testid={`upcoming-deadline-${o.id}`}>{o.booking_deadline ? formatLocalDate(o.booking_deadline) : <span className="italic text-stone-500">Unknown</span>}</dd></div>
        <div><dt className="eyebrow">Cost</dt><dd>{costLabel(e.cost_for_two)}</dd></div>
        <div><dt className="eyebrow">Travel</dt><dd>{travelLabel(e.travel)}</dd></div>
      </dl>
      <div className="mt-4 flex items-center justify-between">
        <span className="text-xs text-stone-500">{savers.length ? `Saved by ${savers.join(" & ")}` : "Not saved yet"}</span>
        <button data-testid={`upcoming-save-${o.id}`} aria-pressed={saved} onClick={toggle} className="btn-secondary">
          <Bookmark className={`h-4 w-4 ${saved ? "fill-[#2D4A3E]" : ""}`} /> {saved ? "Saved" : "Save interest"}
        </button>
      </div>
    </article>
  );
}

export default function Upcoming() {
  const q = useGet<{ items: UpItem[] }>("upcoming", "/upcoming");
  return (
    <div>
      <PageHeader eyebrow="Ahead" title="Upcoming">Dated opportunities. Saving shows interest only — it isn't a plan or a booking.</PageHeader>
      {q.isLoading && <Loading />}
      {q.error && <ErrorState message={errorMessage(q.error)} onRetry={() => q.refetch()} />}
      {q.data && q.data.items.length === 0 && (
        <EmptyState testId="upcoming-empty" icon={<CalendarDays className="h-6 w-6" />} title="Nothing upcoming yet">
          Researched future events will appear here with their dates and booking deadlines.
        </EmptyState>
      )}
      <div className="space-y-5">{q.data?.items.map((it) => <UpcomingCard key={it.occurrence.id} it={it} />)}</div>
    </div>
  );
}
