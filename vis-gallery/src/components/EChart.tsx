import { useEffect, useRef } from "react";
import * as echarts from "echarts";
import type { EChartsOption } from "echarts";

interface Props {
  option: EChartsOption;
  className?: string;
  onClick?: (params: unknown) => void;
}

export default function EChart({ option, className, onClick }: Props) {
  const container = useRef<HTMLDivElement>(null);
  const callback = useRef(onClick);
  callback.current = onClick;

  useEffect(() => {
    if (!container.current) return;
    const chart = echarts.init(container.current, undefined, {
      renderer: "canvas",
      useDirtyRect: true,
    });
    chart.setOption(option, { notMerge: true });
    chart.on("click", (params) => callback.current?.(params));
    const observer = new ResizeObserver(() => chart.resize());
    observer.observe(container.current);
    return () => {
      observer.disconnect();
      chart.dispose();
    };
  }, [option]);

  return <div ref={container} className={className ?? "chart"} />;
}
