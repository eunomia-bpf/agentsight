import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
} from 'recharts';
import { fetchTraceDetail, TraceEventDetail } from '../utils/apiClient';

// ─── Helpers ──────────────────────────────────────────────────────────────────

function nsToDate(ns: number): string {
  return new Date(ns / 1_000_000).toLocaleString('zh-CN', {
    month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  });
}

function fmtTokens(n: number): string {
  return n.toLocaleString();
}

function durationMs(ev: TraceEventDetail): string {
  if (!ev.end_timestamp_ns) return '—';
  const ms = (ev.end_timestamp_ns - ev.start_timestamp_ns) / 1_000_000;
  return ms >= 1000 ? `${(ms / 1000).toFixed(2)}s` : `${ms.toFixed(0)}ms`;
}

// ─── Pie chart colors ────────────────────────────────────────────────────────

const PIE_IO_COLORS = ['#3B82F6', '#10B981'];
const PIE_ROLE_COLORS = ['#34D399', '#6EE7B7', '#F59E0B', '#EF4444', '#8B5CF6'];

/** Luminance-adaptive label inside pie slice */
const renderInnerLabel = (colors: string[]) =>
  ({ cx, cy, midAngle, innerRadius, outerRadius, percent, index }: any) => {
    if (percent < 0.05) return null;
    const RADIAN = Math.PI / 180;
    const r = (innerRadius + outerRadius) / 2;
    const x = cx + r * Math.cos(-midAngle * RADIAN);
    const y = cy + r * Math.sin(-midAngle * RADIAN);
    const hex = colors[index % colors.length].replace('#', '');
    const ri = parseInt(hex.slice(0, 2), 16);
    const gi = parseInt(hex.slice(2, 4), 16);
    const bi = parseInt(hex.slice(4, 6), 16);
    const lum = (0.299 * ri + 0.587 * gi + 0.114 * bi) / 255;
    const fill = lum > 0.55 ? '#1F2937' : '#FFFFFF';
    return (
      <text x={x} y={y} fill={fill} stroke={lum > 0.55 ? 'rgba(255,255,255,0.5)' : 'rgba(0,0,0,0.3)'}
        strokeWidth={3} paintOrder="stroke" textAnchor="middle" dominantBaseline="central"
        fontSize={11} fontWeight={700}>
        {`${(percent * 100).toFixed(1)}%`}
      </text>
    );
  };

// ─── Token Distribution Charts ────────────────────────────────────────────────

interface TokenDistProps {
  events: TraceEventDetail[];
}

const TokenDistributionCharts: React.FC<TokenDistProps> = ({ events }) => {
  const totalInput = events.reduce((s, e) => s + e.input_tokens, 0);
  const totalOutput = events.reduce((s, e) => s + e.output_tokens, 0);

  // Count by model
  const modelMap: Record<string, number> = {};
  for (const ev of events) {
    const m = ev.model ?? 'unknown';
    modelMap[m] = (modelMap[m] ?? 0) + ev.total_tokens;
  }
  const modelData = Object.entries(modelMap).map(([name, value]) => ({ name, value }));

  // Count by role (from parsed output messages)
  const roleMap: Record<string, number> = {};
  for (const ev of events) {
    try {
      const msgs: any[] = ev.output_messages ? JSON.parse(ev.output_messages) : [];
      for (const m of msgs) {
        const role = m.role ?? 'unknown';
        roleMap[role] = (roleMap[role] ?? 0) + (ev.output_tokens / Math.max(msgs.length, 1));
      }
    } catch { /* ignore */ }
  }

  const ioData = [
    { name: '输入', value: totalInput },
    { name: '输出', value: totalOutput },
  ];

  const renderIo = renderInnerLabel(PIE_IO_COLORS);
  const renderRole = renderInnerLabel(PIE_ROLE_COLORS);

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Token 分布</h3>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 输入/输出 */}
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-1 text-center">输入/输出分布</h4>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={ioData} cx="50%" cy="50%" innerRadius={55} outerRadius={90}
                paddingAngle={2} dataKey="value" labelLine={false} label={renderIo}>
                {ioData.map((_, i) => (
                  <Cell key={i} fill={PIE_IO_COLORS[i % PIE_IO_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(v: number) => `${fmtTokens(v)} tokens`} />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex justify-center gap-4 mt-1">
            {ioData.map((d, i) => (
              <div key={d.name} className="flex items-center gap-1.5 text-sm">
                <span className="w-3 h-3 rounded-full" style={{ background: PIE_IO_COLORS[i] }} />
                <span>{d.name}: {fmtTokens(d.value)}</span>
              </div>
            ))}
          </div>
        </div>

        {/* 模型分布 */}
        <div className="border border-gray-200 rounded-lg p-3">
          <h4 className="text-sm font-medium text-gray-700 mb-1 text-center">模型分布</h4>
          <p className="text-xs text-gray-400 text-center mb-2">按 total_tokens 统计</p>
          {modelData.length === 0 ? (
            <div className="text-center text-gray-400 py-8 text-sm">暂无数据</div>
          ) : (
            <>
              <ResponsiveContainer width="100%" height={180}>
                <PieChart>
                  <Pie data={modelData} cx="50%" cy="50%" innerRadius={40} outerRadius={75}
                    paddingAngle={1} dataKey="value" labelLine={false}
                    label={renderInnerLabel(PIE_ROLE_COLORS)}>
                    {modelData.map((_, i) => (
                      <Cell key={i} fill={PIE_ROLE_COLORS[i % PIE_ROLE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v: number) => `${fmtTokens(v)} tokens`} />
                </PieChart>
              </ResponsiveContainer>
              <div className="mt-2 space-y-1">
                {modelData.map((d, i) => (
                  <div key={d.name} className="flex items-center gap-2 text-xs px-1">
                    <span className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                      style={{ background: PIE_ROLE_COLORS[i % PIE_ROLE_COLORS.length] }} />
                    <span className="flex-1 truncate text-gray-700" title={d.name}>{d.name}</span>
                    <span className="text-gray-400 tabular-nums">{fmtTokens(d.value)}</span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>

        {/* 调用统计 */}
        <div className="border border-gray-200 rounded-lg p-3 flex flex-col gap-4 justify-center">
          <h4 className="text-sm font-medium text-gray-700 text-center">调用统计</h4>
          {[
            { label: 'LLM 调用次数', value: events.length, color: 'text-indigo-600' },
            { label: '总输入 Token', value: fmtTokens(totalInput), color: 'text-blue-600' },
            { label: '总输出 Token', value: fmtTokens(totalOutput), color: 'text-green-600' },
            { label: '平均每次 Token', value: fmtTokens(Math.round((totalInput + totalOutput) / Math.max(events.length, 1))), color: 'text-purple-600' },
          ].map(({ label, value, color }) => (
            <div key={label} className="flex items-center justify-between px-2">
              <span className="text-sm text-gray-600">{label}</span>
              <span className={`text-lg font-bold ${color}`}>{value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// ─── Event Detail Panel ───────────────────────────────────────────────────────

interface EventPanelProps {
  ev: TraceEventDetail;
}

const EventDetailPanel: React.FC<EventPanelProps> = ({ ev }) => {
  const parseMessages = (raw: string | null): any[] => {
    if (!raw) return [];
    try { return JSON.parse(raw); } catch { return []; }
  };

  /**
   * Try to get output messages:
   * 1. from output_messages field (pre-extracted by backend)
   * 2. fallback: parse event_json and walk response.messages
   */
  const getOutputMessages = (): any[] => {
    if (ev.output_messages) return parseMessages(ev.output_messages);
    if (!ev.event_json) return [];
    try {
      const full = JSON.parse(ev.event_json);
      // GenAISemanticEvent::LLMCall is serialized as { LLMCall: { response: { messages: [...] } } }
      // or directly as { response: { messages: [...] } } depending on serde tagging
      const llm = full?.LLMCall ?? full;
      const msgs = llm?.response?.messages;
      if (Array.isArray(msgs) && msgs.length > 0) return msgs;
    } catch { /* ignore */ }
    return [];
  };

  const roleStyle = (role: string) => {
    switch (role) {
      case 'user':      return 'bg-blue-100 text-blue-700';
      case 'system':    return 'bg-purple-100 text-purple-700';
      case 'assistant': return 'bg-green-100 text-green-700';
      case 'tool':      return 'bg-orange-100 text-orange-700';
      default:          return 'bg-gray-100 text-gray-600';
    }
  };

  const renderContent = (msg: any): React.ReactNode => {
    if (Array.isArray(msg.parts)) {
      return (
        <div className="space-y-1">
          {msg.parts.map((part: any, pi: number) => {
            if (part.text) return (
              <pre key={pi} className="text-xs text-gray-700 whitespace-pre-wrap break-words bg-gray-50 rounded p-2 max-h-48 overflow-y-auto">
                {part.text.content}
              </pre>
            );
            if (part.reasoning) return (
              <pre key={pi} className="text-xs text-purple-700 whitespace-pre-wrap break-words bg-purple-50 rounded p-2 max-h-40 overflow-y-auto">
                💭 {part.reasoning.content}
              </pre>
            );
            if (part.tool_call) return (
              <pre key={pi} className="text-xs text-orange-700 whitespace-pre-wrap break-words bg-orange-50 rounded p-2 max-h-40 overflow-y-auto">
                🔧 {part.tool_call.name}({JSON.stringify(part.tool_call.arguments, null, 2)})
              </pre>
            );
            return (
              <pre key={pi} className="text-xs text-gray-500 whitespace-pre-wrap break-words bg-gray-50 rounded p-2">
                {JSON.stringify(part, null, 2)}
              </pre>
            );
          })}
        </div>
      );
    }
    const content = msg.content ?? msg.message;
    return (
      <pre className="text-xs text-gray-700 whitespace-pre-wrap break-words bg-gray-50 rounded p-2 max-h-40 overflow-y-auto">
        {typeof content === 'string' ? content : JSON.stringify(content, null, 2)}
      </pre>
    );
  };

  const inputMsgs = parseMessages(ev.input_messages);
  const outputMsgs = getOutputMessages();
  const allMsgs = [
    ...inputMsgs.map((m: any) => ({ ...m, _src: 'input' })),
    ...outputMsgs.map((m: any) => ({ ...m, _src: 'output' })),
  ];

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden h-full">
      {/* 头部 */}
      <div className="px-5 py-4 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center gap-3 flex-wrap">
          <span className="text-sm font-semibold text-gray-900">{ev.model ?? 'unknown model'}</span>
          <span className="text-xs text-gray-400">{nsToDate(ev.start_timestamp_ns)}</span>
          <span className="text-xs text-gray-400">耗时 {durationMs(ev)}</span>
          {ev.agent_name && (
            <span className="px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded-full text-xs">{ev.agent_name}</span>
          )}
        </div>
        <div className="flex gap-4 mt-2 text-xs">
          <span className="text-blue-600">输入 {fmtTokens(ev.input_tokens)}</span>
          <span className="text-green-600">输出 {fmtTokens(ev.output_tokens)}</span>
          <span className="text-gray-500">总计 {fmtTokens(ev.total_tokens)}</span>
        </div>
        {ev.user_query && (
          <div className="mt-2 text-xs text-gray-600 bg-blue-50 rounded px-3 py-1.5 border border-blue-100">
            <span className="font-medium text-blue-700 mr-1">用户请求:</span>
            <span className="break-words">{ev.user_query}</span>
          </div>
        )}
      </div>
      {/* 消息列表 */}
      <div className="p-4 space-y-3 overflow-y-auto max-h-[500px]">
        {allMsgs.length === 0 && (
          <p className="text-xs text-gray-400 text-center py-8">无消息数据</p>
        )}
        {allMsgs.map((msg: any, mi: number) => (
          <div key={mi} className="flex gap-3 items-start">
            <span className={`flex-shrink-0 mt-0.5 px-2 py-0.5 rounded text-xs font-medium ${roleStyle(msg.role)}`}>
              {msg.role ?? 'unknown'}
            </span>
            <div className="flex-1 min-w-0">{renderContent(msg)}</div>
          </div>
        ))}
      </div>
    </div>
  );
};

// ─── Main Page ────────────────────────────────────────────────────────────────

export const TraceDetailPage: React.FC = () => {
  const { traceId } = useParams<{ traceId: string }>();
  const navigate = useNavigate();

  const [events, setEvents] = useState<TraceEventDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null);

  useEffect(() => {
    if (!traceId) return;
    setLoading(true);
    setError(null);
    fetchTraceDetail(traceId)
      .then((data) => { setEvents(data); if (data.length > 0) setSelectedIdx(0); })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [traceId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin text-4xl mb-4">⏳</div>
          <p className="text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-500 mb-4">⚠️ {error}</p>
          <button onClick={() => navigate(-1)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            返回
          </button>
        </div>
      </div>
    );
  }

  const userQuery = events[0]?.user_query ?? null;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-screen-xl mx-auto flex items-center gap-4">
          <button onClick={() => navigate(-1)}
            className="text-gray-500 hover:text-gray-800 text-xl transition-colors">
            ←
          </button>
          <div className="flex-1 min-w-0">
            <h1 className="text-lg font-bold text-gray-900">Trace 详情</h1>
            <p className="text-xs text-gray-400 font-mono mt-0.5 truncate">{traceId}</p>
            {userQuery && (
              <p className="text-sm text-gray-700 mt-1">
                <span className="text-blue-600 font-medium">用户请求: </span>
                {userQuery}
              </p>
            )}
          </div>
          <span className="ml-auto flex-shrink-0 px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm">
            {events.length} 次 LLM 调用
          </span>
        </div>
      </header>

      <main className="max-w-screen-xl mx-auto px-6 py-6 space-y-6">
        {/* Token 分布图 */}
        {events.length > 0 && <TokenDistributionCharts events={events} />}

        {/* 事件详情 */}
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">事件详情</h2>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* 左侧列表 */}
            <div className="lg:col-span-1 space-y-2 max-h-[600px] overflow-y-auto pr-1">
              {events.length === 0 && (
                <p className="text-gray-400 text-sm text-center py-8">暂无事件</p>
              )}
              {events.map((ev, idx) => {
                const isReq = ev.input_tokens > 0;
                const isSelected = selectedIdx === idx;
                return (
                  <div key={ev.id}
                    onClick={() => setSelectedIdx(idx)}
                    className={`rounded-lg border cursor-pointer transition-all ${
                      isSelected
                        ? 'border-blue-500 ring-2 ring-blue-200'
                        : isReq
                          ? 'border-blue-200 hover:border-blue-300'
                          : 'border-green-200 hover:border-green-300'
                    }`}
                  >
                    <div className={`flex items-center gap-3 px-4 py-3 rounded-lg ${
                      isReq ? 'bg-blue-50 text-blue-700' : 'bg-green-50 text-green-700'
                    }`}>
                      <span className="text-xl flex-shrink-0">{isReq ? '📤' : '📥'}</span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-sm truncate">{ev.model ?? 'unknown'}</span>
                          <span className={`flex-shrink-0 px-1.5 py-0.5 text-xs rounded ${
                            isReq ? 'bg-blue-100 text-blue-700' : 'bg-green-100 text-green-700'
                          }`}>
                            {isReq ? '请求' : '响应'}
                          </span>
                        </div>
                        <div className="text-xs mt-0.5 opacity-75">
                          {fmtTokens(ev.total_tokens)} tokens · {durationMs(ev)}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* 右侧详情 */}
            <div className="lg:col-span-2">
              {selectedIdx !== null && events[selectedIdx] ? (
                <EventDetailPanel ev={events[selectedIdx]} />
              ) : (
                <div className="bg-gray-50 rounded-xl border border-gray-200 p-8 text-center flex items-center justify-center h-full">
                  <div>
                    <span className="text-4xl">👈</span>
                    <p className="mt-2 text-gray-500">点击左侧事件查看详情</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};
