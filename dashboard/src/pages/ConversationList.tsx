import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  LineChart, Line, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import {
  fetchSessions,
  fetchTraces,
  fetchAgentNames,
  fetchTimeseries,
  fetchTraceDetail,
  SessionSummary,
  TraceSummary,
  TimeseriesBucket,
  ModelTimeseriesBucket,
  TraceEventDetail,
} from '../utils/apiClient';

// ─── Helpers ──────────────────────────────────────────────────────────────────

/** Convert nanoseconds to a display string */
function nsToDate(ns: number): string {
  return new Date(ns / 1_000_000).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

/** Truncate a long ID for display */
function shortId(id: string, len = 16): string {
  return id.length > len ? id.slice(0, len) + '…' : id;
}

/** 复制按钮组件，点击后短暂显示「已复制」反馈 */
const CopyButton: React.FC<{ text: string }> = ({ text }) => {
  const [copied, setCopied] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const handleCopy = (e: React.MouseEvent) => {
    e.stopPropagation();
    const done = () => {
      setCopied(true);
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => setCopied(false), 1500);
    };
    // HTTP 环境下 clipboard API 可能不可用，使用 execCommand fallback
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(done).catch(() => fallbackCopy(text, done));
    } else {
      fallbackCopy(text, done);
    }
  };
  return (
    <button
      onClick={handleCopy}
      className={`flex-shrink-0 px-1.5 py-0.5 rounded text-xs transition-colors ${
        copied
          ? 'bg-green-100 text-green-600'
          : 'bg-gray-100 hover:bg-gray-200 text-gray-500 hover:text-gray-700'
      }`}
      title="复制完整 ID"
    >
      {copied ? '✓ 已复制' : '复制'}
    </button>
  );
};

function fallbackCopy(text: string, done: () => void) {
  const el = document.createElement('textarea');
  el.value = text;
  el.style.position = 'fixed';
  el.style.opacity = '0';
  document.body.appendChild(el);
  el.focus();
  el.select();
  try { document.execCommand('copy'); } catch {}
  document.body.removeChild(el);
  done();
}

/** datetime-local input value from a timestamp (ms) — uses local timezone */
function toDatetimeLocal(ms: number): string {
  const d = new Date(ms);
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/** Parse a datetime-local value back to ms timestamp */
function fromDatetimeLocal(val: string): number {
  return new Date(val).getTime();
}

/** Format token number */
function fmtTokens(n: number): string {
  return n.toLocaleString();
}

// ─── Trace Detail Modal ───────────────────────────────────────────────────────

interface TraceDetailModalProps {
  traceId: string;
  onClose: () => void;
}

const TraceDetailModal: React.FC<TraceDetailModalProps> = ({ traceId, onClose }) => {
  const [events, setEvents] = useState<TraceEventDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchTraceDetail(traceId)
      .then(setEvents)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [traceId]);

  const parseMessages = (raw: string | null): any[] => {
    if (!raw) return [];
    try { return JSON.parse(raw); } catch { return []; }
  };

  /** Extract display text from a parts-based message (new format) or legacy content field */
  const renderMsgContent = (msg: any): React.ReactNode => {
    // New format: { role, parts: [{text:{content}}, {tool_call:{...}}, ...] }
    if (Array.isArray(msg.parts) && msg.parts.length > 0) {
      return (
        <div className="space-y-1">
          {msg.parts.map((part: any, pi: number) => {
            if (part.text) {
              return (
                <pre key={pi} className="text-xs text-gray-700 whitespace-pre-wrap break-words bg-gray-50 rounded p-2 max-h-64 overflow-y-auto">
                  {part.text.content}
                </pre>
              );
            }
            if (part.reasoning) {
              return (
                <pre key={pi} className="text-xs text-purple-700 whitespace-pre-wrap break-words bg-purple-50 rounded p-2 max-h-48 overflow-y-auto">
                  💭 {part.reasoning.content}
                </pre>
              );
            }
            if (part.tool_call) {
              return (
                <pre key={pi} className="text-xs text-orange-700 whitespace-pre-wrap break-words bg-orange-50 rounded p-2 max-h-48 overflow-y-auto">
                  🔧 {part.tool_call.name}({JSON.stringify(part.tool_call.arguments, null, 2)})
                </pre>
              );
            }
            if (part.tool_call_response) {
              return (
                <pre key={pi} className="text-xs text-teal-700 whitespace-pre-wrap break-words bg-teal-50 rounded p-2 max-h-48 overflow-y-auto">
                  📤 {JSON.stringify(part.tool_call_response.response, null, 2)}
                </pre>
              );
            }
            return (
              <pre key={pi} className="text-xs text-gray-500 whitespace-pre-wrap break-words bg-gray-50 rounded p-2">
                {JSON.stringify(part, null, 2)}
              </pre>
            );
          })}
        </div>
      );
    }
    // Legacy format: { role, content: string | object }
    const content = msg.content ?? msg.message;
    return (
      <pre className="text-xs text-gray-700 whitespace-pre-wrap break-words bg-gray-50 rounded p-2 max-h-48 overflow-y-auto">
        {typeof content === 'string' ? content : JSON.stringify(content, null, 2)}
      </pre>
    );
  };

  const roleStyle = (role: string): string => {
    switch (role) {
      case 'user':      return 'bg-blue-100 text-blue-700';
      case 'system':    return 'bg-purple-100 text-purple-700';
      case 'assistant': return 'bg-green-100 text-green-700';
      case 'tool':      return 'bg-orange-100 text-orange-700';
      default:          return 'bg-gray-100 text-gray-600';
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <div>
            <h2 className="text-lg font-bold text-gray-900">Trace 详情</h2>
            <p className="text-xs text-gray-400 font-mono mt-0.5">{traceId}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-gray-100 text-gray-500 transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading && (
            <div className="flex items-center justify-center py-12 text-gray-400">
              加载中...
            </div>
          )}
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
              ⚠️ {error}
            </div>
          )}
          {!loading && !error && events.length === 0 && (
            <div className="text-center py-12 text-gray-400">该 Trace 暂无数据</div>
          )}
          {events.map((ev, idx) => {
            const inputMsgs = parseMessages(ev.input_messages);
            const outputMsgs = parseMessages(ev.output_messages);
            // Merge all messages in order: input first, then output
            const allMsgs = [
              ...inputMsgs.map((m: any) => ({ ...m, _src: 'input' })),
              ...outputMsgs.map((m: any) => ({ ...m, _src: 'output' })),
            ];
            const isExpanded = expandedIdx === idx;

            return (
              <div
                key={ev.id}
                className="mb-4 border border-gray-200 rounded-lg overflow-hidden"
              >
                {/* Event summary row */}
                <button
                  className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors text-left"
                  onClick={() => setExpandedIdx(isExpanded ? null : idx)}
                >
                  <div className="flex items-center gap-4">
                    <span className="text-xs text-gray-400 font-mono w-4">{idx + 1}</span>
                    <div>
                      <span className="text-sm font-medium text-gray-900">
                        {ev.model ?? 'unknown model'}
                      </span>
                      <span className="ml-3 text-xs text-gray-400">
                        {nsToDate(ev.start_timestamp_ns)}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-xs text-blue-600">
                      输入 {fmtTokens(ev.input_tokens)}
                    </span>
                    <span className="text-xs text-green-600">
                      输出 {fmtTokens(ev.output_tokens)}
                    </span>
                    <span className="text-xs text-gray-500">
                      总计 {fmtTokens(ev.total_tokens)}
                    </span>
                    <span className="text-gray-400 text-xs">{isExpanded ? '▲' : '▼'}</span>
                  </div>
                </button>

                {/* Expanded messages */}
                {isExpanded && (
                  <div className="p-4 space-y-2">
                    {allMsgs.length === 0 && (
                      <p className="text-xs text-gray-400">无消息数据</p>
                    )}
                    {allMsgs.map((msg: any, mi: number) => (
                      <div key={mi} className="flex gap-3 items-start">
                        <span
                          className={`flex-shrink-0 mt-1 px-2 py-0.5 rounded text-xs font-medium ${roleStyle(msg.role)}`}
                        >
                          {msg.role ?? 'unknown'}
                        </span>
                        <div className="flex-1 min-w-0">
                          {renderMsgContent(msg)}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

// ─── Trace sub-table ──────────────────────────────────────────────────────────

interface TraceSubTableProps {
  sessionId: string;
}

const PAGE_SIZE = 10;

const TraceSubTable: React.FC<TraceSubTableProps> = ({ sessionId }) => {
  const navigate = useNavigate();
  const [traces, setTraces] = useState<TraceSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0); // 0-based

  useEffect(() => {
    setLoading(true);
    setPage(0);
    fetchTraces(sessionId)
      .then(setTraces)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [sessionId]);

  if (loading)
    return (
      <tr>
        <td colSpan={8} className="px-8 py-4 text-sm text-gray-400 bg-blue-50">
          加载 Trace 列表...
        </td>
      </tr>
    );
  if (error)
    return (
      <tr>
        <td colSpan={8} className="px-8 py-4 text-sm text-red-500 bg-blue-50">
          ⚠️ {error}
        </td>
      </tr>
    );

  const totalPages = Math.max(1, Math.ceil(traces.length / PAGE_SIZE));
  const pageTraces = traces.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  return (
    <>
      {/* Sub-header */}
      <tr className="bg-blue-50 border-t border-blue-100">
        <td colSpan={8} className="px-8 py-2">
          <div className="grid grid-cols-8 text-xs font-semibold text-blue-700 uppercase tracking-wide">
            <div className="col-span-2">Trace ID</div>
            <div className="col-span-2">用户请求</div>
            <div>输入 Token</div>
            <div>输出 Token</div>
            <div>开始时间</div>
            <div className="text-right">操作</div>
          </div>
        </td>
      </tr>

      {traces.length === 0 && (
        <tr className="bg-blue-50">
          <td colSpan={8} className="px-8 py-3 text-sm text-gray-400">
            该 Session 下暂无 Trace
          </td>
        </tr>
      )}

      {pageTraces.map((tr) => (
        <tr key={tr.trace_id} className="bg-blue-50 hover:bg-blue-100 transition-colors">
          <td colSpan={8} className="px-8 py-2">
            <div className="grid grid-cols-8 items-center text-sm">
              {/* Col 1: Trace ID */}
              <div className="col-span-2 min-w-0 pr-2">
                <div className="flex items-center gap-1">
                  <span
                    className="font-mono text-xs text-blue-600 block truncate"
                    title={tr.trace_id}
                  >
                    {shortId(tr.trace_id, 20)}
                  </span>
                  <CopyButton text={tr.trace_id} />
                </div>
              </div>
              {/* Col 2: User query */}
              <div className="col-span-2 min-w-0 pr-2">
                {tr.user_query ? (
                  <div
                    className="text-sm text-gray-800 truncate max-w-xs"
                    title={tr.user_query}
                  >
                    {tr.user_query}
                  </div>
                ) : (
                  <span className="text-xs text-gray-400">—</span>
                )}
              </div>
              <div className="text-blue-600 font-semibold">
                {fmtTokens(tr.total_input_tokens)}
              </div>
              <div className="text-green-600 font-semibold">
                {fmtTokens(tr.total_output_tokens)}
              </div>
              <div className="text-xs text-gray-500">{nsToDate(tr.start_ns)}</div>
              <div className="text-right">
                <button
                  onClick={() => navigate(`/atif?type=trace&id=${encodeURIComponent(tr.trace_id)}`)}
                  className="px-3 py-1 bg-white border border-blue-300 text-blue-700 rounded-lg text-xs hover:bg-blue-50 transition-colors"
                >
                  详情
                </button>
              </div>
            </div>
          </td>
        </tr>
      ))}

      {/* 分页控制 */}
      {totalPages > 1 && (
        <tr className="bg-blue-50 border-t border-blue-100">
          <td colSpan={8} className="px-8 py-2">
            <div className="flex items-center gap-2 justify-end">
              <span className="text-xs text-gray-500">
                {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, traces.length)} / {traces.length} 条
              </span>
              <button
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
                className="px-2 py-0.5 text-xs border border-blue-300 text-blue-700 rounded hover:bg-blue-50 disabled:opacity-40 transition-colors"
              >
                &lsaquo; 上一页
              </button>
              {Array.from({ length: totalPages }, (_, i) => (
                <button
                  key={i}
                  onClick={() => setPage(i)}
                  className={`px-2 py-0.5 text-xs rounded transition-colors ${
                    i === page
                      ? 'bg-blue-600 text-white'
                      : 'border border-blue-300 text-blue-700 hover:bg-blue-50'
                  }`}
                >
                  {i + 1}
                </button>
              ))}
              <button
                onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={page === totalPages - 1}
                className="px-2 py-0.5 text-xs border border-blue-300 text-blue-700 rounded hover:bg-blue-50 disabled:opacity-40 transition-colors"
              >
                下一页 &rsaquo;
              </button>
            </div>
          </td>
        </tr>
      )}
    </>
  );
};

// ─── Time-series chart helpers ────────────────────────────────────────────────

/** Palette for model colors */
const MODEL_COLORS = [
  '#6366f1', '#10b981', '#f59e0b', '#ef4444', '#3b82f6',
  '#ec4899', '#14b8a6', '#8b5cf6', '#f97316', '#06b6d4',
];

/** Axis label: HH:MM for intra-day, MM-DD HH:MM for multi-day spans */
function nsToLabel(ns: number, spanMs: number): string {
  const d = new Date(ns / 1_000_000);
  const hm = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
  if (spanMs > 23 * 3600 * 1000) {
    return `${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${hm}`;
  }
  return hm;
}

/**
 * Fill sparse bucket array to a full dense series.
 * Backend only returns buckets that have events; missing ones become 0-value entries.
 */
function fillTokenBuckets(
  data: TimeseriesBucket[],
  startNs: number,
  endNs: number,
  bucketCount: number,
): TimeseriesBucket[] {
  const bucketNs = Math.floor((endNs - startNs) / Math.max(bucketCount, 1));
  if (bucketNs <= 0) return data;
  const byIdx = new Map<number, TimeseriesBucket>();
  for (const b of data) {
    const idx = Math.floor((b.bucket_start_ns - startNs) / bucketNs);
    byIdx.set(idx, b);
  }
  const result: TimeseriesBucket[] = [];
  for (let i = 0; i < bucketCount; i++) {
    result.push(byIdx.get(i) ?? {
      bucket_start_ns: startNs + i * bucketNs,
      input_tokens: 0,
      output_tokens: 0,
      total_tokens: 0,
    });
  }
  return result;
}

function fillModelBuckets(
  data: ModelTimeseriesBucket[],
  startNs: number,
  endNs: number,
  bucketCount: number,
  models: string[],
): ModelTimeseriesBucket[] {
  const bucketNs = Math.floor((endNs - startNs) / Math.max(bucketCount, 1));
  if (bucketNs <= 0) return data;
  const byIdxModel = new Map<number, Map<string, number>>();
  for (const b of data) {
    const idx = Math.floor((b.bucket_start_ns - startNs) / bucketNs);
    if (!byIdxModel.has(idx)) byIdxModel.set(idx, new Map());
    byIdxModel.get(idx)!.set(b.model, b.total_tokens);
  }
  const result: ModelTimeseriesBucket[] = [];
  for (let i = 0; i < bucketCount; i++) {
    const bucketStartNs = startNs + i * bucketNs;
    const modelMap = byIdxModel.get(i);
    for (const model of models) {
      result.push({ bucket_start_ns: bucketStartNs, model, total_tokens: modelMap?.get(model) ?? 0 });
    }
  }
  return result;
}

// ─── Token Time-series Chart ──────────────────────────────────────────────────

interface TokenChartData {
  label: string;
  input: number;
  output: number;
  total: number;
}

interface TokenTimeseriesChartProps {
  data: TimeseriesBucket[];
  startNs: number;
  endNs: number;
  bucketCount?: number;
}

const TOKEN_SERIES = [
  { key: 'input', name: '输入 Token', color: '#3b82f6' },
  { key: 'output', name: '输出 Token', color: '#10b981' },
  { key: 'total', name: '总 Token', color: '#6366f1' },
] as const;

const TokenTimeseriesChart: React.FC<TokenTimeseriesChartProps> = ({
  data, startNs, endNs, bucketCount = 30,
}) => {
  const spanMs = (endNs - startNs) / 1_000_000;
  const filled = fillTokenBuckets(data, startNs, endNs, bucketCount);
  const chartData: TokenChartData[] = filled.map((b) => ({
    label: nsToLabel(b.bucket_start_ns, spanMs),
    input: b.input_tokens,
    output: b.output_tokens,
    total: b.total_tokens,
  }));

  // Track which series are hidden; click legend item to toggle
  const [hidden, setHidden] = useState<Set<string>>(new Set());
  const toggleSeries = (key: string) => {
    setHidden((prev) => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });
  };

  if (filled.every((b) => b.total_tokens === 0)) {
    return (
      <div className="flex items-center justify-center h-32 text-gray-400 text-sm">
        暂无时序数据
      </div>
    );
  }

  const tickStep = Math.max(1, Math.floor(bucketCount / 6));
  const ticks = chartData.filter((_, i) => i % tickStep === 0).map((d) => d.label);

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={chartData} margin={{ top: 4, right: 16, left: 0, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="label" ticks={ticks} tick={{ fontSize: 10 }} />
        <YAxis tick={{ fontSize: 11 }} width={56} />
        <Tooltip formatter={(v: number) => v.toLocaleString()} />
        <Legend
          wrapperStyle={{ fontSize: 12, cursor: 'pointer' }}
          onClick={(e) => toggleSeries(e.dataKey as string)}
          formatter={(value, entry) => (
            <span style={{ color: hidden.has((entry as any).dataKey) ? '#aaa' : (entry as any).color }}>
              {value}
            </span>
          )}
        />
        {TOKEN_SERIES.map(({ key, name, color }) => (
          <Line
            key={key}
            type="monotone"
            dataKey={key}
            name={name}
            stroke={color}
            dot={false}
            strokeWidth={2}
            hide={hidden.has(key)}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
};

// ─── Model Token Time-series Chart ────────────────────────────────────────────

interface ModelTimeseriesChartProps {
  data: ModelTimeseriesBucket[];
  startNs: number;
  endNs: number;
  bucketCount?: number;
}

const ModelTimeseriesChart: React.FC<ModelTimeseriesChartProps> = ({
  data, startNs, endNs, bucketCount = 30,
}) => {
  const spanMs = (endNs - startNs) / 1_000_000;
  const models = Array.from(new Set(data.map((d) => d.model))).sort();
  const filled = fillModelBuckets(data, startNs, endNs, bucketCount, models);

  const bucketMap = new Map<number, Record<string, number>>();
  for (const d of filled) {
    if (!bucketMap.has(d.bucket_start_ns)) bucketMap.set(d.bucket_start_ns, {});
    bucketMap.get(d.bucket_start_ns)![d.model] = d.total_tokens;
  }
  const chartData = Array.from(bucketMap.entries())
    .sort(([a], [b]) => a - b)
    .map(([ns, tokens]) => ({ label: nsToLabel(ns, spanMs), ...tokens }));

  // Track which model bars are hidden
  const [hidden, setHidden] = useState<Set<string>>(new Set());
  const toggleModel = (key: string) => {
    setHidden((prev) => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });
  };

  if (models.length === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-gray-400 text-sm">
        暂无模型时序数据
      </div>
    );
  }

  const tickStep = Math.max(1, Math.floor(bucketCount / 6));
  const ticks = chartData.filter((_, i) => i % tickStep === 0).map((d) => d.label);

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={chartData} margin={{ top: 4, right: 16, left: 0, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="label" ticks={ticks} tick={{ fontSize: 10 }} />
        <YAxis tick={{ fontSize: 11 }} width={56} />
        <Tooltip formatter={(v: number) => v.toLocaleString()} />
        <Legend
          wrapperStyle={{ fontSize: 12, cursor: 'pointer' }}
          onClick={(e) => toggleModel(e.dataKey as string)}
          formatter={(value, entry) => {
            const color = hidden.has((entry as any).dataKey) ? '#aaa' : (entry as any).color;
            return <span style={{ color }}>{value}</span>;
          }}
        />
        {models.map((m, i) => (
          <Bar
            key={m}
            dataKey={m}
            name={m}
            stackId="model"
            fill={hidden.has(m) ? 'transparent' : MODEL_COLORS[i % MODEL_COLORS.length]}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
};

// ─── Main Component ───────────────────────────────────────────────────────────

// Accept (and ignore) optional legacy props so App.tsx can still compile
// while we transition data ownership into this component.
export interface ConversationListProps {
  conversations?: unknown[];
}

export const ConversationList: React.FC<ConversationListProps> = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  // Restore state from URL params (set when navigating to detail page)
  const now = Date.now();
  const initStart = Number(searchParams.get('start')) || (now - 24 * 3600 * 1000);
  const initEnd   = Number(searchParams.get('end'))   || now;
  const initAgent = searchParams.get('agent') ?? '';
  const initQueried = searchParams.get('q') === '1';

  // Time range state
  const [startMs, setStartMs] = useState(initStart);
  const [endMs, setEndMs] = useState(initEnd);

  // Agent name filter
  const [agentNames, setAgentNames] = useState<string[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string>(initAgent);
  const [agentNamesLoading, setAgentNamesLoading] = useState(false);

  // Sessions from backend
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Timeseries data
  const [tokenSeries, setTokenSeries] = useState<TimeseriesBucket[]>([]);
  const [modelSeries, setModelSeries] = useState<ModelTimeseriesBucket[]>([]);
  const [timeseriesLoading, setTimeseriesLoading] = useState(false);
  // The ns range actually used in the last query (for gap-filling in charts)
  const [queryRangeNs, setQueryRangeNs] = useState<[number, number]>([0, 1]);

  // Whether user has ever queried (controls showing charts/table)
  const [hasQueried, setHasQueried] = useState(false);

  // Which session row is expanded to show traces
  const [expandedSession, setExpandedSession] = useState<string | null>(null);

  // Sync filter state to URL so back-navigation restores it
  const syncParams = useCallback((sMs: number, eMs: number, agent: string) => {
    const p: Record<string, string> = {
      start: String(sMs),
      end: String(eMs),
      q: '1',
    };
    if (agent) p.agent = agent;
    setSearchParams(p, { replace: true });
  }, [setSearchParams]);

  // Load agent names whenever time range changes (for dropdown options)
  const loadAgentNames = useCallback(async (sMs: number, eMs: number) => {
    setAgentNamesLoading(true);
    try {
      const names = await fetchAgentNames(sMs * 1_000_000, eMs * 1_000_000);
      setAgentNames(names);
      // If currently selected agent is no longer in list, reset
      setSelectedAgent((prev) => (names.includes(prev) ? prev : ''));
    } catch {
      // silently ignore — agent name list is best-effort
    } finally {
      setAgentNamesLoading(false);
    }
  }, []);

  // Load agent names on mount and on time range changes
  useEffect(() => {
    loadAgentNames(startMs, endMs);
  }, [startMs, endMs, loadAgentNames]);

  const handleQuery = useCallback(async () => {
    const effectiveEnd = Date.now();
    setEndMs(effectiveEnd);
    setLoading(true);
    setTimeseriesLoading(true);
    setError(null);
    setHasQueried(true);

    const startNs = startMs * 1_000_000;
    const endNs = effectiveEnd * 1_000_000;
    const agent = selectedAgent || undefined;
    setQueryRangeNs([startNs, endNs]);
    syncParams(startMs, effectiveEnd, selectedAgent);

    try {
      // Run sessions and timeseries queries in parallel
      const [sessData, tsData] = await Promise.all([
        fetchSessions(startNs, endNs).then((data) =>
          agent ? data.filter((s) => s.agent_name === agent) : data
        ),
        fetchTimeseries(startNs, endNs, agent),
      ]);
      setSessions(sessData);
      setTokenSeries(tsData.token_series);
      setModelSeries(tsData.model_series);
    } catch (e: any) {
      setError(e.message ?? '查询失败');
    } finally {
      setLoading(false);
      setTimeseriesLoading(false);
    }
  }, [startMs, selectedAgent, syncParams]);

  // Auto-restore: if URL has q=1, replay the query on mount using URL params
  const hasRestoredRef = React.useRef(false);
  useEffect(() => {
    if (initQueried && !hasRestoredRef.current) {
      hasRestoredRef.current = true;
      const startNs = initStart * 1_000_000;
      const endNs = initEnd * 1_000_000;
      const agent = initAgent || undefined;
      setHasQueried(true);
      setLoading(true);
      setTimeseriesLoading(true);
      setQueryRangeNs([startNs, endNs]);
      Promise.all([
        fetchSessions(startNs, endNs).then((data) =>
          agent ? data.filter((s) => s.agent_name === agent) : data
        ),
        fetchTimeseries(startNs, endNs, agent),
      ]).then(([sessData, tsData]) => {
        setSessions(sessData);
        setTokenSeries(tsData.token_series);
        setModelSeries(tsData.model_series);
      }).catch((e: any) => {
        setError(e.message ?? '查询失败');
      }).finally(() => {
        setLoading(false);
        setTimeseriesLoading(false);
      });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const totalInputTokens = sessions.reduce((s, x) => s + x.total_input_tokens, 0);
  const totalOutputTokens = sessions.reduce((s, x) => s + x.total_output_tokens, 0);

  return (
    <>
      <main className="max-w-screen-xl mx-auto px-6 py-6 space-y-6">
        {/* ── Filter bar ── */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 flex flex-wrap items-end gap-4">
          {/* Time range */}
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-600 whitespace-nowrap">开始时间</label>
            <input
              type="datetime-local"
              className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
              value={toDatetimeLocal(startMs)}
              onChange={(e) => setStartMs(fromDatetimeLocal(e.target.value))}
            />
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-600 whitespace-nowrap">结束时间</label>
            <input
              type="datetime-local"
              className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
              value={toDatetimeLocal(endMs)}
              onChange={(e) => setEndMs(fromDatetimeLocal(e.target.value))}
            />
          </div>

          {/* Quick presets */}
          <div className="flex gap-2 flex-wrap">
            {[
              { label: '最近 1h', ms: 3600 * 1000 },
              { label: '最近 6h', ms: 6 * 3600 * 1000 },
              { label: '最近 24h', ms: 24 * 3600 * 1000 },
              { label: '最近 7d', ms: 7 * 24 * 3600 * 1000 },
            ].map(({ label, ms }) => (
              <button
                key={label}
                onClick={() => {
                  const n = Date.now();
                  setEndMs(n);
                  setStartMs(n - ms);
                }}
                className="px-3 py-1.5 text-xs bg-gray-100 hover:bg-gray-200 rounded-lg text-gray-600 transition-colors"
              >
                {label}
              </button>
            ))}
          </div>

          {/* Agent name selector */}
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-600 whitespace-nowrap">Agent</label>
            <select
              className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 min-w-[160px]"
              value={selectedAgent}
              onChange={(e) => setSelectedAgent(e.target.value)}
              disabled={agentNamesLoading}
            >
              <option value="">全部 Agent</option>
              {agentNames.map((n) => (
                <option key={n} value={n}>{n}</option>
              ))}
            </select>
            {agentNamesLoading && (
              <span className="text-xs text-gray-400">加载中...</span>
            )}
          </div>

          {/* Query button */}
          <button
            onClick={handleQuery}
            disabled={loading}
            className="ml-auto px-5 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {loading ? '查询中...' : '查询'}
          </button>
        </div>

        {/* ── Error banner ── */}
        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-600 text-sm">
            ⚠️ {error}
          </div>
        )}

        {/* ── Content shown only after first query ── */}
        {hasQueried && (
          <>
            {/* Summary cards */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
                <p className="text-sm text-gray-500">Sessions</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">{sessions.length}</p>
              </div>
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
                <p className="text-sm text-gray-500">总输入 Token</p>
                <p className="text-3xl font-bold text-blue-600 mt-1">
                  {fmtTokens(totalInputTokens)}
                </p>
              </div>
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
                <p className="text-sm text-gray-500">总输出 Token</p>
                <p className="text-3xl font-bold text-green-600 mt-1">
                  {fmtTokens(totalOutputTokens)}
                </p>
              </div>
            </div>

            {/* ── Time-series charts ── */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Token time-series */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
                <h2 className="text-sm font-semibold text-gray-700 mb-3">Token 时序（输入 / 输出 / 总计）</h2>
                {timeseriesLoading ? (
                  <div className="flex items-center justify-center h-32 text-gray-400 text-sm">加载中...</div>
                ) : (
                  <TokenTimeseriesChart data={tokenSeries} startNs={queryRangeNs[0]} endNs={queryRangeNs[1]} />
                )}
              </div>

              {/* Model token time-series */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
                <h2 className="text-sm font-semibold text-gray-700 mb-3">模型 Token 时序（堆叠）</h2>
                {timeseriesLoading ? (
                  <div className="flex items-center justify-center h-32 text-gray-400 text-sm">加载中...</div>
                ) : (
                  <ModelTimeseriesChart data={modelSeries} startNs={queryRangeNs[0]} endNs={queryRangeNs[1]} />
                )}
              </div>
            </div>

            {/* ── Session table ── */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wide">
                      Session ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wide">
                      Agent
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wide">
                      Model
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wide">
                      Traces
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wide">
                      输入 Token
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wide">
                      输出 Token
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wide">
                      最近活跃
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wide">
                      操作
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {!loading && sessions.length === 0 && (
                    <tr>
                      <td colSpan={8} className="px-6 py-12 text-center text-gray-400">
                        <div className="text-4xl mb-2">🔍</div>
                        <p>所选时间范围内暂无 Session 数据</p>
                        <p className="text-xs mt-1">请确认 agentsight 服务已启动并有数据写入</p>
                      </td>
                    </tr>
                  )}

                  {sessions.map((sess) => {
                    const isExpanded = expandedSession === sess.session_id;
                    return (
                      <React.Fragment key={sess.session_id}>
                        {/* Session row */}
                        <tr
                          className={`hover:bg-gray-50 transition-colors cursor-pointer ${
                            isExpanded ? 'bg-blue-50' : ''
                          }`}
                          onClick={() =>
                            setExpandedSession(isExpanded ? null : sess.session_id)
                          }
                        >
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-2">
                              <span className="text-gray-400 text-xs">
                                {isExpanded ? '▼' : '▶'}
                              </span>
                              <span
                                className="font-mono text-sm text-gray-800"
                                title={sess.session_id}
                              >
                                {shortId(sess.session_id, 24)}
                              </span>
                              <CopyButton text={sess.session_id} />
                            </div>
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-700">
                            {sess.agent_name ?? <span className="text-gray-400">—</span>}
                          </td>
                          <td className="px-6 py-4">
                            {sess.model ? (
                              <span className="px-2 py-0.5 bg-purple-100 text-purple-800 rounded-full text-xs font-medium">
                                {sess.model}
                              </span>
                            ) : (
                              <span className="text-gray-400 text-sm">—</span>
                            )}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-700">
                            {sess.trace_count}
                          </td>
                          <td className="px-6 py-4 text-sm font-semibold text-blue-600">
                            {fmtTokens(sess.total_input_tokens)}
                          </td>
                          <td className="px-6 py-4 text-sm font-semibold text-green-600">
                            {fmtTokens(sess.total_output_tokens)}
                          </td>
                          <td className="px-6 py-4 text-xs text-gray-500">
                            {nsToDate(sess.last_seen_ns)}
                          </td>
                          <td className="px-6 py-4">
                            <a
                              href={`#/atif?type=session&id=${encodeURIComponent(sess.session_id)}`}
                              onClick={(e) => e.stopPropagation()}
                              className="px-3 py-1 bg-white border border-blue-300 text-blue-700 rounded-lg text-xs hover:bg-blue-50 transition-colors whitespace-nowrap"
                            >
                              详情
                            </a>
                          </td>
                        </tr>

                        {/* Expanded trace sub-table */}
                        {isExpanded && (
                          <TraceSubTable
                            sessionId={sess.session_id}
                          />
                        )}
                      </React.Fragment>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </>
        )}

        {/* Prompt before first query */}
        {!hasQueried && !loading && (
          <div className="flex flex-col items-center justify-center py-20 text-gray-400">
            <div className="text-5xl mb-4">🔎</div>
            <p className="text-base">请选择时间范围和 Agent，然后点击「查询」</p>
          </div>
        )}
      </main>
    </>
  );
};
