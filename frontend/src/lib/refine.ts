import type { BatchItem } from "@/api/types";

export type RefineKey = "easier" | "quieter" | "less_driving" | "lower_cost" | "indoors" | "more_unusual";

export const REFINEMENTS: { key: RefineKey; label: string }[] = [
  { key: "easier", label: "Easier" },
  { key: "quieter", label: "Quieter" },
  { key: "less_driving", label: "Less driving" },
  { key: "lower_cost", label: "Lower cost" },
  { key: "indoors", label: "Indoors" },
  { key: "more_unusual", label: "More unusual" },
];

// true = matches, false = does not match, null = unknown (never treated as a match).
function test(item: BatchItem, key: RefineKey): boolean | null {
  const e = item.snapshot;
  switch (key) {
    case "easier":
      return e.effort == null ? null : e.effort === "easy";
    case "quieter":
      return e.crowd_level == null ? null : e.crowd_level === "low";
    case "less_driving": {
      const t = e.travel;
      if (t.driving_duration_min != null) return t.driving_duration_min <= 30;
      if (t.geo_distance_km != null) return t.geo_distance_km <= 25;
      return null;
    }
    case "lower_cost":
      return e.cost_for_two.status === "unknown" || e.cost_for_two.max == null ? null : e.cost_for_two.max <= 40;
    case "indoors":
      return e.indoor == null ? null : e.indoor;
    case "more_unusual":
      return e.score_components?.uniqueness == null ? null : e.score_components.uniqueness >= 20;
  }
}

export function applyRefinements(items: BatchItem[], active: RefineKey[]) {
  const kept: BatchItem[] = [];
  let unknown = 0;
  for (const item of items) {
    const results = active.map((k) => test(item, k));
    if (results.every((r) => r === true)) kept.push(item);
    else if (results.some((r) => r === null) && !results.some((r) => r === false)) unknown += 1;
  }
  return { kept, hiddenUnknown: unknown };
}
