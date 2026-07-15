import type { EChartsOption } from "echarts";

export const colors = {
  claude: "#f0a06b",
  codex: "#6ad4ff",
  gemini: "#a78bfa",
  read: "#5eb5ff",
  write: "#ff7b72",
  test: "#66d9a3",
  commit: "#f4d35e",
  grid: "rgba(148, 163, 184, 0.13)",
  text: "#d9e2f2",
  muted: "#78869d",
  background: "transparent",
};

export const baseChart: EChartsOption = {
  backgroundColor: "transparent",
  animationDuration: 420,
  textStyle: {
    color: colors.text,
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif",
  },
  tooltip: {
    backgroundColor: "rgba(8, 12, 21, .96)",
    borderColor: "rgba(122, 150, 190, .3)",
    textStyle: { color: colors.text, fontSize: 12 },
    extraCssText: "box-shadow: 0 16px 48px rgba(0,0,0,.45); border-radius: 10px;",
  },
};

export function axisStyle() {
  return {
    axisLine: { lineStyle: { color: colors.grid } },
    axisTick: { show: false },
    axisLabel: { color: colors.muted, fontSize: 10 },
    splitLine: { lineStyle: { color: colors.grid } },
  };
}

export function vendorColor(vendor: string): string {
  return colors[vendor as keyof typeof colors] ?? "#b7c3d7";
}

export function stateColor(state: string): string {
  if (state === "unique_candidate") return "#67d7a8";
  if (state === "ambiguous_candidates") return "#f4b860";
  if (state === "no_candidate") return "#ff6b7a";
  return "#56647a";
}
