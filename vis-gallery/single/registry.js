import { views as overviewPixelsMatrix } from "./views/overview_pixels_matrix.js";
import { views as mapsAnimationRivers } from "./views/maps_animation_rivers.js";
import { views as forensicStoryLongitudinal } from "./views/forensic_story_longitudinal.js";

const rawViews = [
  ...overviewPixelsMatrix,
  ...mapsAnimationRivers,
  ...forensicStoryLongitudinal,
];

function agentVisualMoments(data, nebula = false) {
  const primaryEvents = nebula && data.agent_events?.length ? data.agent_events : (data.events ?? []);
  const agentTimes = [...primaryEvents, ...(nebula ? [] : (data.verification_events ?? []))]
    .map((row) => Number(row.ts_ms))
    .filter(Number.isFinite)
    .sort((left, right) => left - right);
  if (!agentTimes.length) return [];
  const start = agentTimes[0];
  const end = agentTimes.at(-1);
  const attentionDecay = agentTimes.flatMap((value) => [value + 5 * 60_000, value + 30 * 60_000])
    .filter((value) => value <= end);
  const birthTravel = nebula ? primaryEvents
    .filter((row) => row.paths?.length)
    .flatMap((row) => [row.ts_ms + 20_000, row.ts_ms + 60_000, row.ts_ms + 3 * 60_000])
    .filter((value) => value <= end) : [];
  const writeRipples = nebula ? primaryEvents
    .filter((row) => row.effect === "write" || row.write_paths?.length)
    .flatMap((row) => [row.ts_ms + 30_000, row.ts_ms + 90_000, row.ts_ms + 3 * 60_000])
    .filter((value) => value <= end) : [];
  const contextReveal = nebula
    ? [start + 5 * 60_000, start + 15 * 60_000].filter((value) => value <= end)
    : [];
  return [
    ...(nebula ? [start - 1] : []), ...agentTimes, ...birthTravel, ...writeRipples,
    ...contextReveal, ...attentionDecay,
  ].sort((left, right) => left - right);
}

function commitFlashMoments(data, visualMoments) {
  if (!visualMoments.length) return [];
  const start = visualMoments[0];
  const end = visualMoments.at(-1);
  return (data.commits ?? [])
    .map((row) => Number(row.committed_at_ms))
    .filter((value) => Number.isFinite(value) && value >= start && value <= end);
}

export const views = rawViews.map((view) => {
  if (view.timeMode === "static") return view;
  const visualMoments = (data) => agentVisualMoments(data, view.id === "workspace-constellation");
  const timelineRequirements = view.id === "workspace-constellation"
    ? ["commits"] : ["events", "verification_events", "commits"];
  return {
    ...view,
    requirements: [...new Set([...view.requirements, ...timelineRequirements])],
    visualMoments,
    playbackMoments(data) {
      const visual = visualMoments(data);
      return [...visual, ...commitFlashMoments(data, visual)].sort((left, right) => left - right);
    },
  };
});

export const registry = new Map(views.map((view) => [view.id, view]));

export function requireView(id) {
  const view = registry.get(id);
  if (!view) {
    throw new Error(`unknown view ${id}; choose one of: ${views.map((row) => row.id).join(", ")}`);
  }
  return view;
}
