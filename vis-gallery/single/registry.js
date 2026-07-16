import { views as overviewPixelsMatrix } from "./views/overview_pixels_matrix.js";
import { views as mapsAnimationRivers } from "./views/maps_animation_rivers.js";
import { views as forensicStoryLongitudinal } from "./views/forensic_story_longitudinal.js";

const rawViews = [
  ...overviewPixelsMatrix,
  ...mapsAnimationRivers,
  ...forensicStoryLongitudinal,
];

function agentPlaybackMoments(data) {
  const agentTimes = [...(data.events ?? []), ...(data.verification_events ?? [])]
    .map((row) => Number(row.ts_ms))
    .filter(Number.isFinite)
    .sort((left, right) => left - right);
  if (!agentTimes.length) return [];
  const start = agentTimes[0];
  const end = agentTimes.at(-1);
  const attentionDecay = agentTimes.flatMap((value) => [value + 5 * 60_000, value + 30 * 60_000])
    .filter((value) => value <= end);
  const commits = (data.commits ?? [])
    .map((row) => Number(row.committed_at_ms))
    .filter((value) => Number.isFinite(value) && value >= start && value <= end);
  return [...agentTimes, ...attentionDecay, ...commits].sort((left, right) => left - right);
}

export const views = rawViews.map((view) => view.timeMode === "static" ? view : ({
  ...view,
  requirements: [...new Set([...view.requirements, "events", "verification_events", "commits"])],
  playbackMoments: agentPlaybackMoments,
}));

export const registry = new Map(views.map((view) => [view.id, view]));

export function requireView(id) {
  const view = registry.get(id);
  if (!view) {
    throw new Error(`unknown view ${id}; choose one of: ${views.map((row) => row.id).join(", ")}`);
  }
  return view;
}
