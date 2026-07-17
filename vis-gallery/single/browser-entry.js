import { init, use } from "echarts/core";
import {
  BarChart, GraphChart, HeatmapChart, LineChart, PieChart,
  SankeyChart, ScatterChart, ThemeRiverChart, TreemapChart,
} from "echarts/charts";
import {
  AxisPointerComponent, DataZoomComponent, GraphicComponent, GridComponent,
  LegendComponent, MarkLineComponent, SingleAxisComponent, TooltipComponent,
  VisualMapComponent,
} from "echarts/components";
import { SVGRenderer } from "echarts/renderers";
import { createBrowserRuntime } from "./browser-runtime.js";
import { helpers } from "./helpers.js";
import { requireView, views } from "./registry.js";

use([
  BarChart, GraphChart, HeatmapChart, LineChart, PieChart, SankeyChart,
  ScatterChart, ThemeRiverChart, TreemapChart, AxisPointerComponent,
  DataZoomComponent, GraphicComponent, GridComponent, LegendComponent,
  MarkLineComponent, SingleAxisComponent, TooltipComponent,
  VisualMapComponent, SVGRenderer,
]);

globalThis.AgentSightSingle = createBrowserRuntime({ init, helpers, requireView, views });
