// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

'use client';

import { useId, useMemo, useRef, useState } from 'react';

// Hand-authored SVG chart primitives. No chart library: this matches the
// existing visual language (see ResourceMetricsView), keeps the bundle small
// for a locally-run tool, and is less code than wiring up a dependency.
//
// Conventions shared by every chart:
//   - faint grid, an area fill, an emphasized endpoint, and a hover tooltip.
//   - tabular numerals everywhere digits line up.
//   - categorical color is only one encoding; callers always pair charts with
//     a legend and direct labels.

export interface ChartPoint {
  x: number; // 0..1 across the plot
  y: number; // 0..1 up the plot
  value: number; // raw value for tooltips
  label: string; // x-axis / time label for tooltips
}

interface Margin {
  top: number;
  right: number;
  bottom: number;
  left: number;
}

const DEFAULT_MARGIN: Margin = { top: 8, right: 10, bottom: 18, left: 34 };

// Build an SVG path for a polyline through normalized points mapped into the
// plot rectangle (width × height minus margins).
function linePath(
  points: { x: number; y: number }[],
  w: number,
  h: number,
  m: Margin,
): string {
  if (points.length === 0) return '';
  const plotW = w - m.left - m.right;
  const plotH = h - m.top - m.bottom;
  const coords = points.map((p) => {
    const px = m.left + Math.max(0, Math.min(1, p.x)) * plotW;
    const py = m.top + plotH - Math.max(0, Math.min(1, p.y)) * plotH;
    return [px, py] as const;
  });
  return coords
    .map(([px, py], i) => `${i === 0 ? 'M' : 'L'}${px.toFixed(2)},${py.toFixed(2)}`)
    .join(' ');
}

function areaPath(
  points: { x: number; y: number }[],
  w: number,
  h: number,
  m: Margin,
): string {
  if (points.length === 0) return '';
  const plotW = w - m.left - m.right;
  const plotH = h - m.top - m.bottom;
  const baseline = m.top + plotH;
  const top = linePath(points, w, h, m);
  const lastX = m.left + Math.max(0, Math.min(1, points[points.length - 1].x)) * plotW;
  const firstX = m.left + Math.max(0, Math.min(1, points[0].x)) * plotW;
  return `${top} L${lastX.toFixed(2)},${baseline.toFixed(2)} L${firstX.toFixed(2)},${baseline.toFixed(2)} Z`;
}

// ---------------------------------------------------------------------------
// LineArea: a single-series area+line chart with grid, endpoint, and tooltip.
// ---------------------------------------------------------------------------

export interface LineAreaProps {
  points: ChartPoint[];
  color: string;
  height?: number;
  width?: number; // viewbox width; responsive via 100% CSS width
  yMax?: number; // optional explicit max (in value units) for cross-chart parity
  formatValue?: (v: number) => string;
  ariaLabel?: string;
}

export function LineArea({
  points,
  color,
  height = 160,
  width = 640,
  yMax,
  formatValue = (v) => v.toFixed(0),
  ariaLabel,
}: LineAreaProps) {
  const gradId = useId();
  const containerRef = useRef<HTMLDivElement>(null);
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);
  const m = DEFAULT_MARGIN;

  const valueMax = useMemo(() => {
    if (yMax != null && Number.isFinite(yMax)) return yMax;
    const max = Math.max(...points.map((p) => p.value), 0);
    return max <= 0 ? 1 : max * 1.1;
  }, [points, yMax]);

  if (points.length === 0) {
    return (
      <div
        className="flex items-center justify-center text-sm text-gray-400"
        style={{ height }}
      >
        No samples
      </div>
    );
  }

  const plotH = height - m.top - m.bottom;

  const onMove = (e: React.MouseEvent) => {
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;
    const rel = (e.clientX - rect.left) / rect.width;
    const idx = Math.round(rel * (points.length - 1));
    setHoverIdx(Math.max(0, Math.min(points.length - 1, idx)));
  };

  const yTicks = 4;
  const tickValues = Array.from({ length: yTicks + 1 }, (_, i) => (valueMax * i) / yTicks);

  const guide = hoverIdx != null ? points[hoverIdx] : null;
  const guideLeftPct = (guide ? guide.x : 0) * 100;

  return (
    <div
      ref={containerRef}
      className="relative w-full"
      style={{ height }}
      onMouseMove={onMove}
      onMouseLeave={() => setHoverIdx(null)}
      role="img"
      aria-label={ariaLabel}
    >
      <svg
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="none"
        className="block h-full w-full"
        style={{ fontVariantNumeric: 'tabular-nums' }}
      >
        <defs>
          <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.28} />
            <stop offset="100%" stopColor={color} stopOpacity={0.04} />
          </linearGradient>
        </defs>

        {/* faint horizontal grid */}
        {tickValues.map((tv, i) => {
          const y = m.top + plotH - (i / yTicks) * plotH;
          return (
            <g key={i}>
              <line
                x1={m.left}
                y1={y}
                x2={width - m.right}
                y2={y}
                stroke="currentColor"
                className="text-gray-200"
                strokeWidth={1}
              />
              <text
                x={m.left - 6}
                y={y + 3}
                textAnchor="end"
                className="fill-gray-400"
                fontSize={9}
              >
                {formatValue(tv)}
              </text>
            </g>
          );
        })}

        {/* baseline */}
        <line
          x1={m.left}
          y1={m.top + plotH}
          x2={width - m.right}
          y2={m.top + plotH}
          stroke="currentColor"
          className="text-gray-300"
          strokeWidth={1}
        />

        <path d={areaPath(points, width, height, m)} fill={`url(#${gradId})`} />
        <path
          d={linePath(points, width, height, m)}
          fill="none"
          stroke={color}
          strokeWidth={1.75}
          strokeLinejoin="round"
          strokeLinecap="round"
        />

        {/* emphasized endpoint */}
        {(() => {
          const last = points[points.length - 1];
          const px = m.left + last.x * (width - m.left - m.right);
          const py = m.top + plotH - last.y * plotH;
          return (
            <>
              <circle cx={px} cy={py} r={3.5} fill={color} />
              <circle cx={px} cy={py} r={3.5} fill="none" stroke={color} strokeOpacity={0.25} strokeWidth={4} />
            </>
          );
        })()}

        {/* hover guide + marker */}
        {guide && (
          <>
            <line
              x1={m.left + guide.x * (width - m.left - m.right)}
              y1={m.top}
              x2={m.left + guide.x * (width - m.left - m.right)}
              y2={m.top + plotH}
              stroke="currentColor"
              className="text-gray-400"
              strokeWidth={1}
              strokeDasharray="3 3"
            />
            <circle
              cx={m.left + guide.x * (width - m.left - m.right)}
              cy={m.top + plotH - guide.y * plotH}
              r={3.5}
              fill="white"
              stroke={color}
              strokeWidth={2}
            />
          </>
        )}
      </svg>

      {guide && (
        <div
          className="pointer-events-none absolute top-1 z-10 rounded-md border border-gray-200 bg-white px-2 py-1 text-xs text-gray-700 shadow-md"
          style={{
            left: `${Math.min(Math.max(guideLeftPct, 8), 84)}%`,
            fontVariantNumeric: 'tabular-nums',
          }}
        >
          <div className="font-medium text-gray-900">{formatValue(guide.value)}</div>
          <div className="text-gray-500">{guide.label}</div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// StackedArea: multi-series stacked area for the activity strip.
// ---------------------------------------------------------------------------

export interface StackedLayer {
  key: string;
  label: string;
  color: string;
}

export interface StackedAreaProps {
  layers: StackedLayer[];
  // values[layerIdx][bucketIdx] -> count
  values: number[][];
  bucketCount: number;
  height?: number;
  width?: number;
  formatBucketLabel?: (bucketIdx: number) => string;
  ariaLabel?: string;
}

export function StackedArea({
  layers,
  values,
  bucketCount,
  height = 120,
  width = 720,
  formatBucketLabel = (i) => `${i}`,
  ariaLabel,
}: StackedAreaProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);
  const m = { top: 6, right: 8, bottom: 6, left: 8 };

  const totalsPerBucket = useMemo(() => {
    const arr = new Array(bucketCount).fill(0);
    for (const layer of values) {
      for (let i = 0; i < bucketCount; i += 1) {
        arr[i] += layer[i] ?? 0;
      }
    }
    return arr;
  }, [values, bucketCount]);

  const maxTotal = Math.max(1, ...totalsPerBucket);

  // Build cumulative normalized y per layer per bucket. We produce, per layer,
  // a top envelope and bottom envelope so the area band is filled.
  const plotW = width - m.left - m.right;
  const plotH = height - m.top - m.bottom;

  const bands = useMemo(() => {
    // running cumulative stack
    const cum = new Array(bucketCount).fill(0);
    return layers.map((layer, li) => {
      const layerVals = values[li] ?? new Array(bucketCount).fill(0);
      const bottom = [...cum];
      const top = new Array(bucketCount);
      for (let i = 0; i < bucketCount; i += 1) {
        cum[i] = bottom[i] + (layerVals[i] ?? 0);
        top[i] = cum[i];
      }
      return { layer, bottom, top };
    });
  }, [layers, values, bucketCount]);

  const xFor = (i: number) => m.left + (bucketCount <= 1 ? plotW / 2 : (i / (bucketCount - 1)) * plotW);
  const yFor = (v: number) => m.top + plotH - (v / maxTotal) * plotH;

  const onMove = (e: React.MouseEvent) => {
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;
    const rel = (e.clientX - rect.left) / rect.width;
    const x = rel * width;
    const idx = bucketCount <= 1 ? 0 : Math.round(((x - m.left) / plotW) * (bucketCount - 1));
    setHoverIdx(Math.max(0, Math.min(bucketCount - 1, idx)));
  };

  const hover = hoverIdx ?? null;

  return (
    <div
      ref={containerRef}
      className="relative w-full overflow-hidden rounded-md"
      style={{ height }}
      onMouseMove={onMove}
      onMouseLeave={() => setHoverIdx(null)}
      role="img"
      aria-label={ariaLabel}
    >
      <svg
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="none"
        className="block h-full w-full"
        style={{ fontVariantNumeric: 'tabular-nums' }}
      >
        {bands.map(({ layer, bottom, top }) => {
          // Build a band path: along the top envelope left->right, then bottom
          // envelope right->left.
          let d = '';
          for (let i = 0; i < bucketCount; i += 1) {
            d += `${i === 0 ? 'M' : 'L'}${xFor(i).toFixed(2)},${yFor(top[i]).toFixed(2)} `;
          }
          for (let i = bucketCount - 1; i >= 0; i -= 1) {
            d += `L${xFor(i).toFixed(2)},${yFor(bottom[i]).toFixed(2)} `;
          }
          d += 'Z';
          return <path key={layer.key} d={d} fill={layer.color} fillOpacity={0.92} stroke={layer.color} strokeWidth={0.5} />;
        })}

        {hover != null && (
          <line
            x1={xFor(hover)}
            y1={m.top}
            x2={xFor(hover)}
            y2={m.top + plotH}
            stroke="#6B7280"
            strokeWidth={1}
            strokeDasharray="3 3"
          />
        )}
      </svg>

      {hover != null && (
        <div
          className="pointer-events-none absolute top-1 z-10 min-w-[8rem] rounded-md border border-gray-200 bg-white px-2 py-1.5 text-xs shadow-md"
          style={{ left: '50%', transform: 'translateX(-50%)' }}
        >
          <div className="mb-0.5 font-medium text-gray-900">{formatBucketLabel(hover)}</div>
          <div className="space-y-0.5">
            {layers.map((l, li) => {
              const v = values[li]?.[hover] ?? 0;
              if (v <= 0) return null;
              return (
                <div key={l.key} className="flex items-center justify-between gap-3">
                  <span className="flex items-center gap-1.5 capitalize text-gray-600">
                    <span className="inline-block h-2 w-2 rounded-full" style={{ background: l.color }} />
                    {l.label}
                  </span>
                  <span className="font-medium text-gray-900" style={{ fontVariantNumeric: 'tabular-nums' }}>
                    {v}
                  </span>
                </div>
              );
            })}
            <div className="mt-0.5 flex items-center justify-between gap-3 border-t border-gray-100 pt-0.5">
              <span className="text-gray-500">Total</span>
              <span className="font-semibold text-gray-900" style={{ fontVariantNumeric: 'tabular-nums' }}>
                {totalsPerBucket[hover]}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// SegmentedBar: horizontal stacked bar for proportional breakdowns.
// ---------------------------------------------------------------------------

export interface Segment {
  label: string;
  value: number;
  color: string;
}

export function SegmentedBar({ segments, height = 14 }: { segments: Segment[]; height?: number }) {
  const total = segments.reduce((s, x) => s + Math.max(0, x.value), 0);
  const gradId = useId();
  return (
    <div
      className="flex w-full overflow-hidden rounded-full bg-gray-100"
      style={{ height }}
      role="img"
      aria-label="proportional breakdown"
    >
      {total <= 0 ? (
        <div className="flex h-full w-full items-center justify-center text-[10px] text-gray-400">No data</div>
      ) : (
        segments
          .filter((s) => s.value > 0)
          .map((s, i) => {
            const pct = (s.value / total) * 100;
            const width = pct < 0.4 ? 0.4 : pct;
            return (
              <div
                key={`${s.label}-${i}`}
                data-grad={gradId}
                className="h-full first:rounded-l-full last:rounded-r-full"
                style={{ width: `${width}%`, background: s.color }}
                title={`${s.label}: ${pct.toFixed(1)}%`}
              />
            );
          })
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Legend: always present for categorical charts.
// ---------------------------------------------------------------------------

export interface LegendItem {
  label: string;
  color: string;
  value?: string;
}

export function Legend({ items, className = '' }: { items: LegendItem[]; className?: string }) {
  return (
    <ul className={`flex flex-wrap gap-x-3 gap-y-1 text-xs text-gray-600 ${className}`}>
      {items.map((it) => (
        <li key={it.label} className="flex items-center gap-1.5">
          <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ background: it.color }} />
          <span className="capitalize">{it.label}</span>
          {it.value && (
            <span className="text-gray-400" style={{ fontVariantNumeric: 'tabular-nums' }}>
              {it.value}
            </span>
          )}
        </li>
      ))}
    </ul>
  );
}
