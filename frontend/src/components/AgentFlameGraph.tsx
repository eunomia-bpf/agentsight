// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import {
  directFrameChildren,
  disjointMatchValue,
  isFrameDescendant,
  parseAgentFlameSvg,
  type AgentFlameSvgFrame,
  type AgentFlameSvgProfile,
} from '@/utils/agentflameSvg';
import { fetchAgentFlameArtifactText } from '@/utils/agentflame';

interface FlamegraphChoice {
  key: string;
  label: string;
  path: string;
  headline: string;
  question: string;
}

interface AgentFlameGraphProps {
  basePath: string;
  choices: FlamegraphChoice[];
  selectedKey: string;
  onSelect: (key: string) => void;
}

const FRAME_COLORS: Record<string, { fill: string; text: string }> = {
  project: { fill: '#334155', text: '#ffffff' },
  agent: { fill: '#4f46e5', text: '#ffffff' },
  session: { fill: '#7c3aed', text: '#ffffff' },
  prompt: { fill: '#b45309', text: '#ffffff' },
  phase: { fill: '#c2410c', text: '#ffffff' },
  kind: { fill: '#475569', text: '#ffffff' },
  op: { fill: '#475569', text: '#ffffff' },
  call: { fill: '#0369a1', text: '#ffffff' },
  model: { fill: '#0e7490', text: '#ffffff' },
  token: { fill: '#0f766e', text: '#ffffff' },
  tool: { fill: '#6d28d9', text: '#ffffff' },
  cmd: { fill: '#6d28d9', text: '#ffffff' },
  process: { fill: '#6d28d9', text: '#ffffff' },
  path: { fill: '#047857', text: '#ffffff' },
  file: { fill: '#047857', text: '#ffffff' },
  domain: { fill: '#2563eb', text: '#ffffff' },
  effect: { fill: '#be185d', text: '#ffffff' },
  status: { fill: '#15803d', text: '#ffffff' },
};

const FALLBACK_COLOR = { fill: '#64748b', text: '#ffffff' };
const CHART_WIDTH = 1200;
const FRAME_HEIGHT = 28;
const FRAME_GAP = 3;
const NUMBER_FORMAT = new Intl.NumberFormat();
const SECONDS_FORMAT = new Intl.NumberFormat(undefined, { maximumFractionDigits: 1 });

function formatNumber(value: number): string {
  return NUMBER_FORMAT.format(value);
}

function formatMetric(value: number, metric: string): string {
  if (metric.toLowerCase().includes('second')) {
    return `${SECONDS_FORMAT.format(value)} s`;
  }
  return `${formatNumber(value)} ${metric}`;
}

function frameColor(frame: AgentFlameSvgFrame): { fill: string; text: string } {
  if (frame.kind === 'status') {
    const status = frame.name.slice(frame.name.indexOf(':') + 1).toLowerCase();
    if (/(error|fail|denied|timeout|cancel)/.test(status)) return { fill: '#dc2626', text: '#ffffff' };
    if (/(warn|unknown|partial)/.test(status)) return { fill: '#a16207', text: '#ffffff' };
  }
  if (frame.kind === 'effect') {
    const effect = frame.name.slice(frame.name.indexOf(':') + 1).toLowerCase();
    if (/(read|inspect|list)/.test(effect)) return { fill: '#047857', text: '#ffffff' };
    if (/(test|build)/.test(effect)) return { fill: '#7c3aed', text: '#ffffff' };
  }
  return FRAME_COLORS[frame.kind] ?? FALLBACK_COLOR;
}

function truncateLabel(value: string, width: number): string {
  const max = Math.max(0, Math.floor((width - 14) / 7));
  if (max < 4) return '';
  return value.length <= max ? value : `${value.slice(0, Math.max(1, max - 1))}…`;
}

function frameValue(frame: AgentFlameSvgFrame): string {
  const separator = frame.name.indexOf(':');
  return separator >= 0 ? frame.name.slice(separator + 1) : frame.name;
}

function firstDiagnosticFrame(profile: AgentFlameSvgProfile): AgentFlameSvgFrame {
  const prompts = profile.frames.filter(frame => frame.kind === 'prompt');
  return [...(prompts.length > 0 ? prompts : profile.frames)]
    .sort((left, right) => right.value - left.value || right.depth - left.depth)[0];
}

function parentFrame(profile: AgentFlameSvgProfile, frame: AgentFlameSvgFrame): AgentFlameSvgFrame | null {
  if (frame.path.length <= 1) return null;
  const parentId = frame.path.slice(0, -1).join('\u0000');
  return profile.frames.find(candidate => candidate.id === parentId) ?? null;
}

function Inspector({
  profile,
  frame,
  focus,
  onFocus,
  onSelect,
}: {
  profile: AgentFlameSvgProfile;
  frame: AgentFlameSvgFrame;
  focus: AgentFlameSvgFrame;
  onFocus: (frame: AgentFlameSvgFrame) => void;
  onSelect: (frame: AgentFlameSvgFrame) => void;
}) {
  const children = directFrameChildren(profile.frames, frame);
  const parent = parentFrame(profile, frame);
  return (
    <aside className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm lg:sticky lg:top-4 lg:self-start">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">Selected frame</div>
          <h4 className="mt-1 break-words text-lg font-semibold text-slate-900">{frameValue(frame)}</h4>
          <div className="mt-1 text-xs font-medium text-slate-500">{frame.kind}</div>
        </div>
        <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-600">
          {frame.totalPct.toFixed(1)}%
        </span>
      </div>

      <div className="mt-4 rounded-xl bg-slate-950 p-3 text-white">
        <div className="text-xs text-slate-400">Inclusive weight</div>
        <div className="mt-1 text-xl font-semibold">{formatMetric(frame.value, frame.metric)}</div>
        <div className="mt-1 text-xs text-slate-400">
          {(frame.value * 100 / Math.max(1, focus.value)).toFixed(1)}% of the current focus
        </div>
      </div>

      <div className="mt-4">
        <div className="text-xs font-semibold uppercase tracking-wide text-slate-400">Stack path</div>
        <ol className="mt-2 space-y-1.5 text-xs text-slate-600">
          {frame.path.map((part, index) => (
            <li key={`${part}-${index}`} className="flex gap-2">
              <span className="text-slate-300">{index + 1}</span>
              <span className="min-w-0 break-all">{part}</span>
            </li>
          ))}
        </ol>
      </div>

      {children.length > 0 && (
        <div className="mt-4">
          <div className="text-xs font-semibold uppercase tracking-wide text-slate-400">Breakdown</div>
          <div className="mt-2 space-y-2">
            {children.slice(0, 5).map(child => (
              <button
                key={child.id}
                type="button"
                onClick={() => onSelect(child)}
                className="block w-full text-left"
              >
                <div className="mb-1 flex items-center justify-between gap-2 text-xs">
                  <span className="truncate font-medium text-slate-700">{frameValue(child)}</span>
                  <span className="shrink-0 text-slate-400">{(child.value * 100 / frame.value).toFixed(0)}%</span>
                </div>
                <div className="h-1.5 overflow-hidden rounded-full bg-slate-100">
                  <div
                    className="h-full rounded-full bg-sky-500"
                    style={{ width: `${Math.max(2, child.value * 100 / frame.value)}%` }}
                  />
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="mt-5 flex gap-2">
        <button
          type="button"
          onClick={() => onFocus(frame)}
          disabled={frame.id === focus.id}
          className="flex-1 rounded-lg bg-slate-900 px-3 py-2 text-sm font-semibold text-white transition hover:bg-slate-700 disabled:cursor-default disabled:bg-slate-200 disabled:text-slate-500"
        >
          Focus branch
        </button>
        {parent && (
          <button
            type="button"
            onClick={() => onSelect(parent)}
            className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-50"
          >
            Parent
          </button>
        )}
      </div>
    </aside>
  );
}

export function AgentFlameGraph({ basePath, choices, selectedKey, onSelect }: AgentFlameGraphProps) {
  const [profile, setProfile] = useState<AgentFlameSvgProfile | null>(null);
  const [selectedId, setSelectedId] = useState('');
  const [focusId, setFocusId] = useState('');
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const searchRef = useRef<HTMLInputElement>(null);
  const activeChoice = choices.find(choice => choice.key === selectedKey) ?? choices[0];

  useEffect(() => {
    if (!activeChoice) return;
    let cancelled = false;
    setLoading(true);
    setError('');
    fetchAgentFlameArtifactText(basePath, activeChoice.path)
      .then(source => {
        if (cancelled) return;
        const next = parseAgentFlameSvg(source);
        if (!next) throw new Error('This artifact is not a supported AgentSight flamegraph.');
        const diagnostic = firstDiagnosticFrame(next);
        const root = [...next.frames].sort((left, right) => left.depth - right.depth || right.value - left.value)[0];
        setProfile(next);
        setSelectedId(diagnostic.id);
        setFocusId(root.id);
        setQuery('');
      })
      .catch(reason => {
        if (!cancelled) {
          setProfile(null);
          setError(reason instanceof Error ? reason.message : 'Flamegraph unavailable.');
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [activeChoice, basePath]);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const active = document.activeElement as HTMLElement | null;
      if (event.key === '/' && !['INPUT', 'TEXTAREA', 'SELECT'].includes(active?.tagName ?? '') && !active?.isContentEditable) {
        event.preventDefault();
        searchRef.current?.focus();
      }
      if (event.key === 'Escape') {
        if (query) {
          setQuery('');
        } else if (profile) {
          const profileRoot = [...profile.frames]
            .sort((left, right) => left.depth - right.depth || right.value - left.value)[0];
          setFocusId(profileRoot.id);
          setSelectedId(profileRoot.id);
        }
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [profile, query]);

  const root = useMemo(() => {
    if (!profile) return null;
    return [...profile.frames].sort((left, right) => left.depth - right.depth || right.value - left.value)[0];
  }, [profile]);
  const focus = profile?.frames.find(frame => frame.id === focusId) ?? root;
  const selected = profile?.frames.find(frame => frame.id === selectedId) ?? focus;
  const normalizedQuery = query.trim().toLowerCase();
  if (choices.length === 0) return null;

  const visible = profile && focus
    ? profile.frames.filter(frame => isFrameDescendant(frame, focus))
    : [];
  const matchingIds = new Set(
    visible
      .filter(frame => !normalizedQuery || frame.name.toLowerCase().includes(normalizedQuery))
      .map(frame => frame.id),
  );
  const maxDepth = visible.reduce((max, frame) => Math.max(max, frame.depth), focus?.depth ?? 0);
  const chartHeight = Math.max(72, (maxDepth - (focus?.depth ?? 0) + 1) * (FRAME_HEIGHT + FRAME_GAP) + 18);
  const matchValue = profile && normalizedQuery ? disjointMatchValue(profile.frames, matchingIds) : 0;

  const setFocus = (frame: AgentFlameSvgFrame) => {
    setFocusId(frame.id);
    setSelectedId(frame.id);
  };

  const selectWithKeyboard = (frame: AgentFlameSvgFrame) => {
    setSelectedId(frame.id);
    requestAnimationFrame(() => {
      const index = visible.findIndex(candidate => candidate.id === frame.id);
      document.querySelector<SVGGElement>(`[data-flame-frame="${index}"]`)?.focus();
    });
  };

  return (
    <section
      className="overflow-hidden rounded-2xl border border-slate-200 bg-gradient-to-b from-white to-slate-50 shadow-sm"
      data-agentflame-interactive="true"
      data-profile-frame-count={profile?.frames.length ?? 0}
      data-selected-frame={selected?.name ?? ''}
      data-focused-frame={focus?.name ?? ''}
    >
      <div className="border-b border-slate-200 px-5 py-5">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-sky-600">Interactive profile</div>
            <h3 className="mt-1 text-2xl font-semibold tracking-tight text-slate-950">{activeChoice?.headline}</h3>
            <p className="mt-1 text-sm text-slate-500">{activeChoice?.question} Width is inclusive weight; move upward to follow the observed stack.</p>
          </div>
          <div className="inline-flex self-start rounded-xl bg-slate-100 p-1">
            {choices.map(choice => (
              <button
                key={choice.key}
                type="button"
                aria-pressed={choice.key === activeChoice?.key}
                onClick={() => onSelect(choice.key)}
                className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${
                  choice.key === activeChoice?.key
                    ? 'bg-white text-slate-900 shadow-sm'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                {choice.label}
              </button>
            ))}
          </div>
        </div>

        <div className="mt-5 flex flex-col gap-3 md:flex-row md:items-center">
          <label className="relative min-w-0 flex-1">
            <span className="sr-only">Search flamegraph frames</span>
            <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-slate-400">⌕</span>
            <input
              ref={searchRef}
              value={query}
              onChange={event => setQuery(event.target.value)}
              onKeyDown={event => {
                if (event.key !== 'Enter' || !normalizedQuery) return;
                const firstMatch = profile?.frames.find(frame => matchingIds.has(frame.id));
                if (firstMatch) setSelectedId(firstMatch.id);
              }}
              placeholder="Search prompts, tools, files, models…  /"
              className="w-full rounded-xl border border-slate-200 bg-white py-2.5 pl-9 pr-3 text-sm text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-sky-400 focus:ring-4 focus:ring-sky-100"
            />
          </label>
          <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
            {profile && (
              <>
                <span className="rounded-lg border border-slate-200 bg-white px-3 py-2">
                  {formatMetric(profile.total, profile.metric)} total
                </span>
                {normalizedQuery && (
                  <span className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-amber-800">
                    {matchingIds.size} matches · {(matchValue * 100 / Math.max(1, focus?.value ?? profile.total)).toFixed(1)}% of focus
                  </span>
                )}
              </>
            )}
            {root && focus && focus.id !== root.id && (
              <button
                type="button"
                onClick={() => setFocus(root)}
                className="rounded-lg border border-slate-200 bg-white px-3 py-2 font-semibold text-slate-700 transition hover:bg-slate-50"
              >
                Reset zoom
              </button>
            )}
          </div>
        </div>
      </div>

      {loading && (
        <div className="grid min-h-72 place-items-center text-sm text-slate-500">Loading profile…</div>
      )}
      {error && (
        <div className="m-5 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">{error}</div>
      )}

      {!loading && profile && focus && selected && (
        <div className="grid gap-5 p-5 lg:grid-cols-[minmax(0,1fr)_19rem]">
          <div className="min-w-0">
            <div className="mb-3 flex flex-wrap items-center gap-1.5 text-xs text-slate-500">
              <span className="mr-1 font-semibold text-slate-400">Focus</span>
              {focus.path.map((part, index) => {
                const id = focus.path.slice(0, index + 1).join('\u0000');
                const frame = profile.frames.find(candidate => candidate.id === id);
                return (
                  <span key={`${part}-${index}`} className="flex items-center gap-1.5">
                    {index > 0 && <span className="text-slate-300">›</span>}
                    <button
                      type="button"
                      onClick={() => frame && setFocus(frame)}
                      className="max-w-40 truncate rounded-md px-1.5 py-1 font-medium text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                    >
                      {frameValue(frame ?? focus)}
                    </button>
                  </span>
                );
              })}
            </div>

            <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950 p-3 shadow-inner">
              <svg
                viewBox={`0 0 ${CHART_WIDTH} ${chartHeight}`}
                role="group"
                aria-label={`${profile.title}, ${visible.length} visible frames`}
                className="w-full min-w-[720px]"
              >
                <style>{'.agent-flame-frame:focus-visible rect{stroke:#fff;stroke-width:4px}'}</style>
                {visible.map((frame, frameIndex) => {
                  const x = (frame.x - focus.x) * CHART_WIDTH / focus.width;
                  const width = frame.width * CHART_WIDTH / focus.width;
                  const y = 8 + (maxDepth - frame.depth) * (FRAME_HEIGHT + FRAME_GAP);
                  const matches = !normalizedQuery || matchingIds.has(frame.id);
                  const color = frameColor(frame);
                  const isSelected = frame.id === selected.id;
                  return (
                    <g
                      key={frame.id}
                      role="button"
                      data-flame-frame={frameIndex}
                      tabIndex={isSelected ? 0 : -1}
                      aria-label={`${frame.name}, ${formatMetric(frame.value, frame.metric)}, ${frame.totalPct.toFixed(1)} percent`}
                      onClick={event => {
                        event.currentTarget.focus();
                        setSelectedId(frame.id);
                      }}
                      onDoubleClick={() => setFocus(frame)}
                      onKeyDown={event => {
                        if (event.key === 'Enter' || event.key === ' ') {
                          event.preventDefault();
                          setSelectedId(frame.id);
                        }
                        if (event.key === 'ArrowUp') {
                          const child = directFrameChildren(profile.frames, frame)[0];
                          if (child) {
                            event.preventDefault();
                            selectWithKeyboard(child);
                          }
                        }
                        if (event.key === 'ArrowDown') {
                          const parent = parentFrame(profile, frame);
                          if (parent && isFrameDescendant(parent, focus)) {
                            event.preventDefault();
                            selectWithKeyboard(parent);
                          }
                        }
                        if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
                          const parent = parentFrame(profile, frame);
                          const siblings = (parent ? directFrameChildren(profile.frames, parent) : visible)
                            .filter(candidate => candidate.depth === frame.depth)
                            .sort((left, right) => left.x - right.x);
                          const offset = event.key === 'ArrowLeft' ? -1 : 1;
                          const sibling = siblings[siblings.findIndex(candidate => candidate.id === frame.id) + offset];
                          if (sibling) {
                            event.preventDefault();
                            selectWithKeyboard(sibling);
                          }
                        }
                      }}
                      className="agent-flame-frame cursor-pointer outline-none"
                      opacity={matches ? 1 : 0.14}
                    >
                      <title>{`${frame.path.join(' → ')}\n${formatMetric(frame.value, frame.metric)} (${frame.totalPct.toFixed(2)}%)`}</title>
                      <rect
                        x={x + 0.7}
                        y={y}
                        width={Math.max(0, width - 1.4)}
                        height={FRAME_HEIGHT}
                        rx={5}
                        fill={color.fill}
                        stroke={isSelected ? '#fbbf24' : normalizedQuery && matches ? '#fde68a' : '#0f172a'}
                        strokeWidth={isSelected ? 3 : normalizedQuery && matches ? 2 : 1}
                        className="transition-all duration-150 hover:brightness-110"
                      />
                      {width >= 42 && (
                        <text
                          x={x + 8}
                          y={y + 18.5}
                          fill={color.text}
                          fontSize={12}
                          fontWeight={600}
                          className="pointer-events-none select-none"
                        >
                          {truncateLabel(frameValue(frame), width)}
                        </text>
                      )}
                    </g>
                  );
                })}
              </svg>
            </div>
            <div className="mt-3 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-400">
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                <span>Click to inspect · double-click to focus · arrows navigate · / searches</span>
                {[
                  ['Context', '#4f46e5'],
                  ['Prompt', '#b45309'],
                  ['LLM', '#0369a1'],
                  ['Tool', '#6d28d9'],
                  ['Effect', '#047857'],
                  ['Failure', '#dc2626'],
                ].map(([label, color]) => (
                  <span key={label} className="inline-flex items-center gap-1">
                    <span className="h-2 w-2 rounded-sm" style={{ backgroundColor: color }} />
                    {label}
                  </span>
                ))}
              </div>
              <span>{visible.length} visible frames{profile.hiddenTiny > 0 ? ` · ${formatNumber(profile.hiddenTiny)} tiny frames omitted by exporter` : ''}</span>
            </div>
          </div>

          <Inspector
            profile={profile}
            frame={selected}
            focus={focus}
            onFocus={setFocus}
            onSelect={frame => setSelectedId(frame.id)}
          />
        </div>
      )}
    </section>
  );
}
