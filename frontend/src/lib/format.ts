import type { Cost, Experience, Travel } from "@/api/types";

const TZ = "America/Toronto";

export function formatLocalDate(isoDate: string | null | undefined): string {
  if (!isoDate) return "Date unknown";
  const [y, m, d] = isoDate.slice(0, 10).split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d, 12)).toLocaleDateString("en-CA", {
    weekday: "short", month: "short", day: "numeric", timeZone: TZ,
  });
}

export function formatLocalDateTime(ts: string | null | undefined): string {
  if (!ts) return "Unknown";
  return new Date(ts).toLocaleString("en-CA", {
    month: "short", day: "numeric", hour: "numeric", minute: "2-digit", timeZone: TZ, timeZoneName: "short",
  });
}

export function costLabel(c: Cost | undefined): string {
  if (!c || c.status === "unknown" || (c.min == null && c.max == null)) return "Cost unknown";
  const range = c.min === c.max || c.max == null ? `$${c.min}` : `$${c.min ?? 0}–${c.max}`;
  return `${range} for two (${c.status})`;
}

export function travelLabel(t: Travel | undefined): string {
  if (!t) return "Travel unknown";
  if (t.driving_duration_min != null) return `~${Math.round(t.driving_duration_min)} min drive (${t.status})`;
  if (t.driving_distance_km != null) return `~${t.driving_distance_km} km by road (${t.status})`;
  if (t.geo_distance_km != null) return `~${t.geo_distance_km} km straight-line (${t.status})`;
  return "Travel unknown";
}

export function whenLabel(e: Experience): string {
  const occ = e.occurrences?.[0];
  if (occ) {
    const end = occ.end_date && occ.end_date !== occ.start_date ? ` – ${formatLocalDate(occ.end_date)}` : "";
    return `${formatLocalDate(occ.start_date)}${end}`;
  }
  return e.kind === "evergreen" ? "Available most days (unconfirmed)" : e.kind === "seasonal" ? "Seasonal window" : "Date unknown";
}

export const humanize = (s: string | null | undefined) => (s ? s.replace(/_/g, " ") : "");
