import { views as overviewPixelsMatrix } from "./views/overview_pixels_matrix.js";
import { views as mapsAnimationRivers } from "./views/maps_animation_rivers.js";
import { views as forensicStoryLongitudinal } from "./views/forensic_story_longitudinal.js";

export const views = [
  ...overviewPixelsMatrix,
  ...mapsAnimationRivers,
  ...forensicStoryLongitudinal,
];

export const registry = new Map(views.map((view) => [view.id, view]));

export function requireView(id) {
  const view = registry.get(id);
  if (!view) {
    throw new Error(`unknown view ${id}; choose one of: ${views.map((row) => row.id).join(", ")}`);
  }
  return view;
}
