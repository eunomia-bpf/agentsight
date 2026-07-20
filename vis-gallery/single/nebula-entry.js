import { init, use } from "echarts/core";
import { ScatterChart } from "echarts/charts";
import { GraphicComponent, GridComponent, TooltipComponent } from "echarts/components";
import { SVGRenderer } from "echarts/renderers";
import { createBrowserRuntime } from "./browser-runtime.js";
import { helpers } from "./helpers.js";
import {
  nebulaPlaybackDuration, nebulaVisualMoments, repositoryNebula,
} from "./views/repository_nebula.js";

use([ScatterChart, GraphicComponent, GridComponent, TooltipComponent, SVGRenderer]);

const view = {
  id: "workspace-constellation",
  title: "Repository Nebula",
  note: "Files are stars. Directories are color and path attraction, never nodes.",
  timeMode: "endpoint-overlay",
  requirements: ["agent_events", "commits"],
  build: repositoryNebula,
  visualMoments: nebulaVisualMoments,
  playbackDuration: nebulaPlaybackDuration,
  playbackMoments(data) {
    const visual = nebulaVisualMoments(data);
    if (!visual.length) return [];
    const start = visual[0];
    const end = visual.at(-1);
    const commits = (data.commits ?? []).map((row) => Number(row.committed_at_ms))
      .filter((value) => Number.isFinite(value) && value >= start && value <= end);
    return [...visual, ...commits].sort((left, right) => left - right);
  },
};

const views = [view];
const requireView = (id) => {
  if (id !== view.id) throw new Error(`unknown view ${id}`);
  return view;
};

globalThis.AgentSightSingle = createBrowserRuntime({ init, helpers, requireView, views });
