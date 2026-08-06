// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

'use client';

/**
 * Agent Nebula web view — render only.
 *
 * Layout (positions, colors, frame downsample, star caps) is computed by the
 * collector at GET /api/v1/nebula. This component owns playback cursor, hover,
 * and chart drawing.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { init, use as registerEcharts, type EChartsType } from 'echarts/core';
import { ScatterChart } from 'echarts/charts';
import { GraphicComponent, GridComponent, TooltipComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import { useTranslation } from '@/i18n';
import type { NebulaDocument, NebulaFrame, NebulaStar } from '@/types/nebula';

// echarts tree-shaken registry (not a React hook)
registerEcharts([ScatterChart, GraphicComponent, GridComponent, TooltipComponent, CanvasRenderer]);

const basePath = process.env.NEXT_PUBLIC_BASE_PATH || '';
const PLAYBACK_FRAME_MS = 140;
const SPEEDS = [0.5, 1, 2, 4] as const;

export type NebulaNavigateTarget = 'log' | 'timeline' | 'process-tree';

interface NebulaViewProps {
  onNavigate?: (view: NebulaNavigateTarget, opts?: { path?: string }) => void;
}

function restingSize(visits: number, visibleCount: number): number {
  const density = Math.sqrt(480 / Math.max(480, visibleCount));
  const base = Math.max(0.85, Math.min(6, 6 * density));
  const weight = Math.max(0.62, Math.min(1.4, 0.62 + 0.38 * Math.min(4, Math.sqrt(visits)) / 2));
  return Math.max(0.85, Math.min(10.5, base * weight));
}

function timeLabel(ms: number): string {
  return new Date(ms).toISOString().replace('T', ' ').replace(/\.\d{3}Z$/, ' UTC');
}

function buildOption(
  doc: NebulaDocument,
  frame: NebulaFrame,
  frameIndex: number,
  selectedPath: string | null,
) {
  const activeMap = new Map(frame.active.map((a) => [a.id, a]));
  const visible = doc.stars.filter((s) => s.birth_frame <= frameIndex);
  const points = visible.map((star) => {
    const hit = activeMap.get(star.id);
    const size = restingSize(star.visits, visible.length);
    const boosted = hit ? size + 3.5 * hit.strength : size;
    const isSelected = selectedPath === star.path;
    return {
      value: [star.x, 1 - star.y],
      path: star.path,
      area: star.area,
      visits: star.visits,
      access: hit?.access ?? null,
      symbolSize: isSelected ? boosted + 3 : boosted,
      itemStyle: {
        color: star.color,
        opacity: hit ? 0.95 : 0.72,
        borderColor: isSelected ? '#ffffff' : hit ? '#f7ffff' : 'transparent',
        borderWidth: isSelected || hit ? 1.4 : 0,
        shadowBlur: hit ? 12 * (hit.strength ?? 0.5) : 0,
        shadowColor: star.color,
      },
    };
  });

  const ripples = frame.active
    .map((a) => {
      const star = doc.stars.find((s) => s.id === a.id);
      if (!star || star.birth_frame > frameIndex) return null;
      const size = restingSize(star.visits, visible.length) + 8 + 10 * a.strength;
      const color =
        a.access === 'delete'
          ? '#ff647c'
          : a.access === 'create'
            ? '#75f0a9'
            : a.access === 'rename'
              ? '#63dfff'
              : a.access === 'read'
                ? '#f7ffff'
                : '#ff9678';
      return {
        value: [star.x, 1 - star.y],
        symbolSize: size,
        itemStyle: {
          color: 'transparent',
          borderColor: color,
          borderWidth: 1.25,
          opacity: 0.15 + 0.55 * a.strength,
          shadowBlur: 10,
          shadowColor: color,
        },
        silent: true,
      };
    })
    .filter(Boolean);

  return {
    backgroundColor: 'transparent',
    animation: false,
    textStyle: { color: '#dce8f7', fontFamily: 'Inter, system-ui, sans-serif' },
    grid: { left: 8, right: 8, top: 8, bottom: 8 },
    xAxis: { type: 'value' as const, min: 0, max: 1, show: false },
    yAxis: { type: 'value' as const, min: 0, max: 1, show: false },
    tooltip: {
      trigger: 'item' as const,
      backgroundColor: '#0b121c',
      borderColor: 'rgba(135,160,190,.28)',
      textStyle: { color: '#dce8f7', fontSize: 12 },
      formatter: (params: { data?: { path?: string; area?: string; visits?: number; access?: string | null } }) => {
        const row = params?.data;
        if (!row?.path) return '';
        const lines = [
          row.path,
          `area: ${row.area}`,
          `${row.visits ?? 0} recorded file actions`,
          row.access ? `this moment: ${row.access}` : 'visible (not active this moment)',
        ];
        return lines.join('<br/>');
      },
    },
    graphic: [
      {
        type: 'group',
        left: 12,
        top: 12,
        silent: true,
        z: 100,
        children: [
          {
            type: 'rect',
            shape: { x: 0, y: 0, width: 520, height: 56, r: 8 },
            style: {
              fill: 'rgba(5,10,18,.78)',
              stroke: 'rgba(120,155,190,.18)',
              lineWidth: 1,
            },
          },
          {
            type: 'text',
            style: {
              x: 14,
              y: 12,
              text: frame.summary,
              fill: '#dce8f7',
              font: '13px ui-monospace, monospace',
              width: 490,
              overflow: 'truncate',
            },
          },
          {
            type: 'text',
            style: {
              x: 14,
              y: 34,
              text: `${timeLabel(frame.t_ms)} · frame ${frameIndex + 1}/${doc.frames.length} · ${visible.length} files`,
              fill: '#74869c',
              font: '10px ui-monospace, monospace',
            },
          },
        ],
      },
      areaLegend(doc, frame, visible),
    ],
    series: [
      {
        id: 'files',
        name: 'files',
        type: 'scatter',
        z: 3,
        data: points,
        emphasis: { scale: 1.6 },
      },
      {
        id: 'ripples',
        name: 'activity',
        type: 'scatter',
        silent: true,
        z: 5,
        data: ripples,
      },
    ],
  };
}

function areaLegend(
  doc: NebulaDocument,
  frame: NebulaFrame,
  visible: NebulaStar[],
) {
  const counts = new Map<string, number>();
  for (const star of visible) {
    counts.set(star.area, (counts.get(star.area) ?? 0) + 1);
  }
  const activeAreas = new Set(
    frame.active
      .map((a) => doc.stars.find((s) => s.id === a.id)?.area)
      .filter((a): a is string => !!a),
  );
  const rows = doc.areas
    .filter((a) => counts.has(a.name) && a.name !== '(root)')
    .slice(0, 8);
  const height = 40 + 18 * rows.length;
  const children: object[] = [
    {
      type: 'rect',
      shape: { x: 0, y: 0, width: 200, height, r: 8 },
      style: {
        fill: 'rgba(5,10,18,.78)',
        stroke: 'rgba(120,155,190,.18)',
        lineWidth: 1,
      },
    },
    {
      type: 'text',
      style: {
        x: 12,
        y: 10,
        text: 'AREAS',
        fill: '#91a6bd',
        font: '10px ui-monospace, monospace',
      },
    },
  ];
  rows.forEach((row, index) => {
    const y = 28 + 18 * index;
    const on = activeAreas.has(row.name);
    children.push(
      {
        type: 'circle',
        shape: { cx: 14, cy: y + 4, r: on ? 4.5 : 3.5 },
        style: {
          fill: row.color,
          stroke: on ? '#ffffff' : 'transparent',
          lineWidth: on ? 1.2 : 0,
        },
      },
      {
        type: 'text',
        style: {
          x: 26,
          y,
          text: row.name,
          width: 120,
          overflow: 'truncate',
          fill: on ? '#f4f8ff' : '#b4c2d2',
          font: '11px ui-monospace, monospace',
        },
      },
      {
        type: 'text',
        style: {
          x: 184,
          y,
          text: String(counts.get(row.name) ?? 0),
          textAlign: 'right',
          fill: '#71849a',
          font: '10px ui-monospace, monospace',
        },
      },
    );
  });
  return {
    type: 'group',
    right: 12,
    top: 12,
    silent: true,
    z: 100,
    children,
  };
}

export function NebulaView({ onNavigate }: NebulaViewProps) {
  const { t } = useTranslation();
  const chartRef = useRef<HTMLDivElement | null>(null);
  const chart = useRef<EChartsType | null>(null);
  const playRef = useRef(0);
  const [doc, setDoc] = useState<NebulaDocument | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [frameIndex, setFrameIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState<(typeof SPEEDS)[number]>(1);
  const [selectedPath, setSelectedPath] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${basePath}/api/v1/nebula`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = (await response.json()) as NebulaDocument;
      setDoc(payload);
      // Land on the final frame so the full star field is visible; Play rewinds.
      setFrameIndex(Math.max(0, (payload.frames?.length ?? 1) - 1));
      setSelectedPath(null);
    } catch (err) {
      setDoc(null);
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const frame = useMemo(() => {
    if (!doc || doc.frames.length === 0) return null;
    return doc.frames[Math.max(0, Math.min(doc.frames.length - 1, frameIndex))] ?? null;
  }, [doc, frameIndex]);

  // Chart container only mounts after loading finishes — re-init when the
  // document is ready so we do not bind to a missing ref on first paint.
  useEffect(() => {
    if (!doc || doc.meta.empty || !chartRef.current) return;
    if (chart.current) {
      chart.current.dispose();
      chart.current = null;
    }
    chart.current = init(chartRef.current, undefined, { renderer: 'canvas' });
    chart.current.on('click', (params) => {
      const path = (params.data as { path?: string } | undefined)?.path;
      if (!path) return;
      setSelectedPath(path);
    });
    const onResize = () => chart.current?.resize();
    window.addEventListener('resize', onResize);
    // Draw the current frame immediately after init.
    const current = doc.frames[Math.max(0, Math.min(doc.frames.length - 1, frameIndex))];
    if (current) {
      chart.current.setOption(buildOption(doc, current, frameIndex, selectedPath), {
        notMerge: true,
        lazyUpdate: false,
      });
    }
    // Ensure layout after flex/min-height settles.
    requestAnimationFrame(() => chart.current?.resize());
    return () => {
      window.removeEventListener('resize', onResize);
      chart.current?.dispose();
      chart.current = null;
    };
    // Only re-init when a new document loads; frame updates use the effect below.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [doc]);

  useEffect(() => {
    if (!chart.current || !doc || !frame) return;
    chart.current.setOption(buildOption(doc, frame, frameIndex, selectedPath), {
      notMerge: true,
      lazyUpdate: false,
    });
  }, [doc, frame, frameIndex, selectedPath]);

  useEffect(() => {
    if (!playing || !doc || doc.frames.length < 2) {
      cancelAnimationFrame(playRef.current);
      playRef.current = 0;
      return;
    }
    // If we are already at the end (default landing), restart from the beginning.
    let nextIndex = frameIndex >= doc.frames.length - 1 ? 0 : frameIndex + 1;
    setFrameIndex(nextIndex);
    let nextAt = performance.now() + PLAYBACK_FRAME_MS / speed;
    const tick = (now: number) => {
      if (now < nextAt) {
        playRef.current = requestAnimationFrame(tick);
        return;
      }
      nextIndex += 1;
      if (nextIndex >= doc.frames.length) {
        setPlaying(false);
        return;
      }
      setFrameIndex(nextIndex);
      nextAt += PLAYBACK_FRAME_MS / speed;
      playRef.current = requestAnimationFrame(tick);
    };
    playRef.current = requestAnimationFrame(tick);
    return () => {
      cancelAnimationFrame(playRef.current);
      playRef.current = 0;
    };
    // Restart the loop when speed changes or play toggles; frameIndex is read at start.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [playing, speed, doc]);

  if (loading) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-12 text-center shadow-md">
        <div className="mx-auto mb-3 h-10 w-10 animate-spin rounded-full border-b-2 border-blue-600" />
        <p className="text-gray-600">{t('nebula.loading')}</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-8 text-center shadow-md">
        <p className="font-medium text-red-700">{t('nebula.error')}</p>
        <p className="mt-1 text-sm text-red-600">{error}</p>
        <button
          type="button"
          onClick={() => void load()}
          className="mt-4 rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
        >
          {t('nebula.retry')}
        </button>
      </div>
    );
  }

  if (!doc || doc.meta.empty || doc.frames.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-12 text-center shadow-md">
        <p className="text-lg font-medium text-gray-800">{t('nebula.emptyTitle')}</p>
        <p className="mt-2 text-sm text-gray-500">
          {doc?.meta.empty_reason ?? t('nebula.emptyHint')}
        </p>
        <p className="mt-4 text-xs text-gray-400">{t('nebula.emptySource')}</p>
      </div>
    );
  }

  const boundNote =
    doc.meta.shown_stars < doc.meta.total_unique_files ||
    doc.meta.shown_frames < doc.meta.total_file_events
      ? t('nebula.showing', {
          stars: doc.meta.shown_stars,
          totalStars: doc.meta.total_unique_files,
          frames: doc.meta.shown_frames,
          totalEvents: doc.meta.total_file_events,
        })
      : t('nebula.full', {
          stars: doc.meta.shown_stars,
          frames: doc.meta.shown_frames,
        });

  return (
    <div className="space-y-3">
      <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-md">
        <div className="flex flex-col gap-2 lg:flex-row lg:items-start lg:justify-between">
          <div className="min-w-0">
            <h2 className="text-lg font-semibold text-gray-900">{t('nebula.title')}</h2>
            <p className="mt-0.5 text-sm text-gray-600">{t('nebula.subtitle')}</p>
            <p className="mt-1 text-xs text-gray-500" title={doc.meta.bounding_policy}>
              {boundNote}
              {' · '}
              {t('nebula.repository')}: {doc.meta.repository}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => setPlaying((p) => !p)}
              className="rounded-md border border-gray-200 px-3 py-1.5 text-sm font-medium text-gray-800 hover:bg-gray-50"
            >
              {playing ? t('nebula.pause') : t('nebula.play')}
            </button>
            <label className="flex items-center gap-1 text-xs text-gray-600">
              {t('nebula.speed')}
              <select
                value={speed}
                onChange={(e) => setSpeed(Number(e.target.value) as (typeof SPEEDS)[number])}
                className="rounded border border-gray-200 bg-white px-1.5 py-1 text-sm"
              >
                {SPEEDS.map((s) => (
                  <option key={s} value={s}>
                    {s}×
                  </option>
                ))}
              </select>
            </label>
            <button
              type="button"
              onClick={() => void load()}
              className="rounded-md border border-gray-200 px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-50"
            >
              {t('nebula.reload')}
            </button>
          </div>
        </div>

        <div className="mt-3 flex items-center gap-3">
          <input
            type="range"
            min={0}
            max={Math.max(0, doc.frames.length - 1)}
            step={1}
            value={frameIndex}
            onChange={(e) => {
              setPlaying(false);
              setFrameIndex(Number(e.target.value));
            }}
            className="h-2 w-full cursor-pointer accent-teal-600"
            aria-label={t('nebula.scrub')}
          />
          <span
            className="shrink-0 text-xs text-gray-500"
            style={{ fontVariantNumeric: 'tabular-nums' }}
          >
            {frame ? timeLabel(frame.t_ms) : '—'}
          </span>
        </div>
      </div>

      <div className="overflow-hidden rounded-lg border border-gray-800 bg-[#070b12] shadow-md">
        <div
          ref={chartRef}
          className="w-full"
          style={{ height: 560, minHeight: 420 }}
        />
      </div>

      {selectedPath && (
        <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-gray-200 bg-white px-4 py-3 text-sm shadow-md">
          <div className="min-w-0">
            <span className="text-gray-500">{t('nebula.selected')}</span>{' '}
            <code className="break-all font-mono text-gray-900">{selectedPath}</code>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => onNavigate?.('log', { path: selectedPath })}
              className="rounded-md border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50"
            >
              {t('nebula.openLogs')}
            </button>
            <button
              type="button"
              onClick={() => onNavigate?.('timeline', { path: selectedPath })}
              className="rounded-md border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50"
            >
              {t('nebula.openTimeline')}
            </button>
            <button
              type="button"
              onClick={() => setSelectedPath(null)}
              className="rounded-md px-2 py-1.5 text-xs text-gray-500 hover:bg-gray-50"
            >
              {t('nebula.clearSelection')}
            </button>
          </div>
        </div>
      )}

      <div className="flex flex-wrap gap-x-4 gap-y-1 px-1 text-[11px] text-gray-500">
        <LegendSwatch color="#f7ffff" label={t('nebula.legend.read')} />
        <LegendSwatch color="#ff9678" label={t('nebula.legend.write')} />
        <LegendSwatch color="#75f0a9" label={t('nebula.legend.create')} />
        <LegendSwatch color="#63dfff" label={t('nebula.legend.rename')} />
        <LegendSwatch color="#ff647c" label={t('nebula.legend.delete')} />
      </div>
    </div>
  );
}

function LegendSwatch({ color, label }: { color: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className="inline-block h-0.5 w-3 rounded" style={{ background: color }} />
      {label}
    </span>
  );
}
