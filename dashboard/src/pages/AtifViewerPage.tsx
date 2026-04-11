import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import type {
  AtifDocument, AtifStep, AtifToolCall, AtifObservation, AtifStepMetrics,
} from '../types';
import { fetchAtifByTrace, fetchAtifBySession } from '../utils/apiClient';

// ─── Helpers ──────────────────────────────────────────────────────────────────

function fmtTokens(n: number): string {
  return n.toLocaleString();
}

function fmtTimestamp(iso?: string): string {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleString('zh-CN', {
      month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
    });
  } catch {
    return iso;
  }
}

function shortId(id: string, len = 20): string {
  return id.length > len ? id.slice(0, len) + '\u2026' : id;
}

// ─── Source styling ───────────────────────────────────────────────────────────

const SOURCE_STYLES: Record<string, { dot: string; badge: string; border: string; label: string }> = {
  system: {
    dot: 'bg-purple-500',
    badge: 'bg-purple-100 text-purple-700',
    border: 'border-l-purple-400',
    label: '系统',
  },
  user: {
    dot: 'bg-blue-500',
    badge: 'bg-blue-100 text-blue-700',
    border: 'border-l-blue-400',
    label: '用户',
  },
  agent: {
    dot: 'bg-green-500',
    badge: 'bg-green-100 text-green-700',
    border: 'border-l-green-400',
    label: 'Agent',
  },
};

function getSourceStyle(source: string) {
  return SOURCE_STYLES[source] ?? {
    dot: 'bg-gray-400',
    badge: 'bg-gray-100 text-gray-600',
    border: 'border-l-gray-300',
    label: source,
  };
}

// ─── Collapsible Section ──────────────────────────────────────────────────────

interface CollapsibleProps {
  icon: string;
  title: string;
  count?: number;
  isOpen: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}

const Collapsible: React.FC<CollapsibleProps> = ({ icon, title, count, isOpen, onToggle, children }) => (
  <div className="mt-3">
    <button
      onClick={onToggle}
      className="w-full flex items-center justify-between px-4 py-2 bg-gray-50 hover:bg-gray-100 rounded-lg text-left text-sm transition-colors"
    >
      <span className="flex items-center gap-2">
        <span>{icon}</span>
        <span className="font-medium text-gray-700">{title}</span>
        {count !== undefined && (
          <span className="px-1.5 py-0.5 bg-gray-200 text-gray-600 rounded text-xs">{count}</span>
        )}
      </span>
      <span className="text-gray-400 text-xs">{isOpen ? '\u25b2' : '\u25bc'}</span>
    </button>
    {isOpen && <div className="mt-2 px-1">{children}</div>}
  </div>
);

// ─── ExpandableText ───────────────────────────────────────────────────────────

const TEXT_THRESHOLD = 300;

const ExpandableText: React.FC<{ text: string; className?: string }> = ({ text, className = '' }) => {
  const [expanded, setExpanded] = useState(false);
  const isLong = text.length > TEXT_THRESHOLD;
  const display = isLong && !expanded ? text.slice(0, TEXT_THRESHOLD) + '\u2026' : text;

  return (
    <div>
      <pre className={`text-sm whitespace-pre-wrap break-words rounded-lg p-3 max-h-80 overflow-y-auto ${className}`}>
        {display}
      </pre>
      {isLong && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-1 text-xs text-blue-600 hover:text-blue-800"
        >
          {expanded ? '← 收起' : '展开全部 →'}
        </button>
      )}
    </div>
  );
};

// ─── StepCard ─────────────────────────────────────────────────────────────────

interface StepCardProps {
  step: AtifStep;
  expandedSections: Set<string>;
  onToggleSection: (key: string) => void;
}

const StepCard: React.FC<StepCardProps> = ({ step, expandedSections, onToggleSection }) => {
  const style = getSourceStyle(step.source);
  const sectionKey = (name: string) => `${step.step_id}-${name}`;
  const isOpen = (name: string) => expandedSections.has(sectionKey(name));
  const toggle = (name: string) => onToggleSection(sectionKey(name));

  const hasReasoning = !!step.reasoning_content;
  const hasToolCalls = !!step.tool_calls && step.tool_calls.length > 0;
  const hasObservation = !!step.observation && step.observation.results.length > 0;
  const hasMetrics = !!step.metrics && (
    step.metrics.prompt_tokens != null ||
    step.metrics.completion_tokens != null
  );

  return (
    <div className="relative pl-8 mb-4">
      {/* Timeline dot */}
      <div className={`absolute left-0 top-4 w-3 h-3 rounded-full ring-2 ring-white ${style.dot}`} />

      {/* Card */}
      <div className={`bg-white rounded-xl shadow-sm border border-gray-200 border-l-4 ${style.border} overflow-hidden`}>
        {/* Header */}
        <div className="px-5 py-3 flex items-center gap-3 flex-wrap">
          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${style.badge}`}>
            {style.label}
          </span>
          <span className="text-sm font-medium text-gray-900">Step {step.step_id}</span>
          {step.timestamp && (
            <span className="text-xs text-gray-400">{fmtTimestamp(step.timestamp)}</span>
          )}
          {step.model_name && (
            <span className="px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded-full text-xs">
              {step.model_name}
            </span>
          )}
        </div>

        {/* Body */}
        <div className="px-5 pb-4">
          {/* Message */}
          {step.message ? (
            <ExpandableText text={step.message} className="text-gray-700 bg-gray-50" />
          ) : (
            <span className="text-xs text-gray-400 italic">无消息内容</span>
          )}

          {/* Agent-only sections */}
          {step.source === 'agent' && (
            <>
              {/* Reasoning */}
              {hasReasoning && (
                <Collapsible
                  icon="💭"
                  title="推理过程"
                  isOpen={isOpen('reasoning')}
                  onToggle={() => toggle('reasoning')}
                >
                  <pre className="text-xs text-purple-700 whitespace-pre-wrap break-words bg-purple-50 rounded-lg p-3 border border-purple-100 max-h-64 overflow-y-auto">
                    {step.reasoning_content}
                  </pre>
                </Collapsible>
              )}

              {/* Tool Calls */}
              {hasToolCalls && (
                <Collapsible
                  icon="🔧"
                  title="工具调用"
                  count={step.tool_calls!.length}
                  isOpen={isOpen('toolcalls')}
                  onToggle={() => toggle('toolcalls')}
                >
                  <div className="space-y-2">
                    {step.tool_calls!.map((tc, i) => (
                      <ToolCallItem key={tc.tool_call_id || i} tc={tc} />
                    ))}
                  </div>
                </Collapsible>
              )}

              {/* Observation */}
              {hasObservation && (
                <Collapsible
                  icon="📋"
                  title="观察结果"
                  count={step.observation!.results.length}
                  isOpen={isOpen('observation')}
                  onToggle={() => toggle('observation')}
                >
                  <div className="space-y-2">
                    {step.observation!.results.map((r, i) => (
                      <div key={i} className="border border-teal-100 rounded-lg overflow-hidden">
                        {r.source_call_id && (
                          <div className="px-3 py-1 bg-teal-50 border-b border-teal-100">
                            <span className="text-xs text-gray-400 font-mono">call: {shortId(r.source_call_id, 16)}</span>
                          </div>
                        )}
                        {r.content ? (
                          <div className="p-2">
                            <ExpandableText text={r.content} className="text-xs text-gray-700 bg-teal-50 font-mono" />
                          </div>
                        ) : (
                          <div className="px-3 py-2 text-xs text-gray-400 italic">无输出内容</div>
                        )}
                      </div>
                    ))}
                  </div>
                </Collapsible>
              )}

              {/* Metrics */}
              {hasMetrics && (
                <div className="flex flex-wrap gap-2 mt-3 pt-3 border-t border-gray-100">
                  {step.metrics!.prompt_tokens != null && (
                    <span className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs">
                      输入: {fmtTokens(step.metrics!.prompt_tokens!)}
                    </span>
                  )}
                  {step.metrics!.completion_tokens != null && (
                    <span className="px-2 py-1 bg-green-50 text-green-700 rounded text-xs">
                      输出: {fmtTokens(step.metrics!.completion_tokens!)}
                    </span>
                  )}
                  {step.metrics!.cached_tokens != null && step.metrics!.cached_tokens! > 0 && (
                    <span className="px-2 py-1 bg-yellow-50 text-yellow-700 rounded text-xs">
                      缓存: {fmtTokens(step.metrics!.cached_tokens!)}
                    </span>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

// ─── ToolCallItem ─────────────────────────────────────────────────────────────

const ToolCallItem: React.FC<{ tc: AtifToolCall }> = ({ tc }) => {
  const [showArgs, setShowArgs] = useState(false);
  const argsStr = typeof tc.arguments === 'string'
    ? tc.arguments
    : JSON.stringify(tc.arguments, null, 2);
  const isLongArgs = argsStr.length > 200;

  return (
    <div className="border border-orange-100 rounded-lg overflow-hidden">
      <div className="px-3 py-2 bg-orange-50 flex items-center gap-2 flex-wrap">
        <span className="px-2 py-0.5 bg-orange-100 text-orange-700 rounded text-xs font-mono font-medium">
          {tc.function_name}
        </span>
        <span className="text-xs text-gray-400 font-mono">{shortId(tc.tool_call_id, 16)}</span>
        {isLongArgs && (
          <button
            onClick={() => setShowArgs(!showArgs)}
            className="ml-auto text-xs text-blue-600 hover:text-blue-800"
          >
            {showArgs ? '收起参数' : '展开参数'}
          </button>
        )}
      </div>
      {(!isLongArgs || showArgs) && (
        <pre className="text-xs text-gray-700 whitespace-pre-wrap break-words bg-white p-3 max-h-48 overflow-y-auto font-mono">
          {argsStr}
        </pre>
      )}
    </div>
  );
};

// ─── AgentInfoCard ────────────────────────────────────────────────────────────

const AgentInfoCard: React.FC<{ doc: AtifDocument }> = ({ doc }) => {
  const { agent } = doc;
  const toolCount = agent.tool_definitions?.length ?? 0;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 lg:col-span-2">
      <h3 className="text-sm font-semibold text-gray-900 mb-3">Agent 信息</h3>
      <div className="space-y-2 text-sm">
        {[
          { label: '名称', value: agent.name },
          { label: '版本', value: agent.version },
          { label: '模型', value: agent.model_name ?? '—' },
          { label: '工具定义', value: `${toolCount} 个` },
        ].map(({ label, value }) => (
          <div key={label} className="flex items-center justify-between">
            <span className="text-gray-500">{label}</span>
            <span className="text-gray-900 font-medium font-mono">{value}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

// ─── MetricCard ───────────────────────────────────────────────────────────────

const MetricCard: React.FC<{ label: string; value: string; color: string; sub?: string }> = ({ label, value, color, sub }) => (
  <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 flex flex-col justify-center">
    <span className="text-sm text-gray-500 mb-1">{label}</span>
    <span className={`text-2xl font-bold ${color}`}>{value}</span>
    {sub && <span className="text-xs text-gray-400 mt-1">{sub}</span>}
  </div>
);

// ─── Main Page ────────────────────────────────────────────────────────────────

export const AtifViewerPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  // Input state
  const [queryType, setQueryType] = useState<'trace' | 'session'>(
    (searchParams.get('type') as 'trace' | 'session') || 'trace'
  );
  const [queryId, setQueryId] = useState(searchParams.get('id') || '');

  // Data state
  const [doc, setDoc] = useState<AtifDocument | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // UI state
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());
  const fileInputRef = useRef<HTMLInputElement>(null);

  const toggleSection = useCallback((key: string) => {
    setExpandedSections(prev => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }, []);

  // Load data
  const handleLoad = useCallback(async (type?: 'trace' | 'session', id?: string) => {
    const t = type ?? queryType;
    const i = id ?? queryId;
    if (!i.trim()) return;

    setSearchParams({ type: t, id: i.trim() }, { replace: true });
    setLoading(true);
    setError(null);
    setDoc(null);
    setExpandedSections(new Set());

    try {
      const data = t === 'trace'
        ? await fetchAtifByTrace(i.trim())
        : await fetchAtifBySession(i.trim());
      setDoc(data);
    } catch (e: any) {
      setError(e.message ?? '加载失败');
    } finally {
      setLoading(false);
    }
  }, [queryType, queryId, setSearchParams]);

  // Auto-load from URL on mount
  useEffect(() => {
    const urlType = searchParams.get('type') as 'trace' | 'session' | null;
    const urlId = searchParams.get('id');
    if (urlType && urlId) {
      setQueryType(urlType);
      setQueryId(urlId);
      handleLoad(urlType, urlId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // JSON file import
  const handleFileImport = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      try {
        const parsed = JSON.parse(ev.target?.result as string);
        if (!parsed.schema_version || !String(parsed.schema_version).startsWith('ATIF')) {
          setError('JSON 解析失败：缺少 schema_version 字段或非 ATIF 格式');
          return;
        }
        setDoc(parsed as AtifDocument);
        setError(null);
        setQueryId(parsed.session_id ?? '');
      } catch {
        setError('JSON 解析失败，请检查文件格式');
      }
    };
    reader.readAsText(file);
    e.target.value = '';
  }, []);

  // JSON download
  const handleDownload = useCallback(() => {
    if (!doc) return;
    const blob = new Blob([JSON.stringify(doc, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `atif-${doc.session_id.slice(0, 16)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [doc]);

  // Compute metrics (fallback when final_metrics is partial)
  const computedMetrics = doc ? (() => {
    const fm = doc.final_metrics;
    let promptSum = 0, completionSum = 0, cachedSum = 0;
    for (const s of doc.steps) {
      if (s.metrics) {
        promptSum += s.metrics.prompt_tokens ?? 0;
        completionSum += s.metrics.completion_tokens ?? 0;
        cachedSum += s.metrics.cached_tokens ?? 0;
      }
    }
    return {
      steps: fm?.total_steps ?? doc.steps.length,
      prompt: fm?.total_prompt_tokens ?? promptSum,
      completion: fm?.total_completion_tokens ?? completionSum,
      cached: fm?.total_cached_tokens ?? cachedSum,
    };
  })() : null;

  return (
    <>
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-screen-xl mx-auto flex items-center gap-4">
          <button
            onClick={() => navigate(-1)}
            className="flex-shrink-0 flex items-center gap-1 px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm transition-colors"
            title="返回上一页"
          >
            ← 返回
          </button>
          <div className="flex-1 min-w-0">
            <h1 className="text-lg font-bold text-gray-900">ATIF 轨迹查看器</h1>
            {doc && (
              <div className="flex items-center gap-2 mt-0.5">
                <span className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">
                  {doc.schema_version}
                </span>
                <span className="text-xs text-gray-400 font-mono truncate">{doc.session_id}</span>
              </div>
            )}
          </div>
          {doc && (
            <button onClick={handleDownload}
              className="flex-shrink-0 px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm transition-colors">
              ⬇️ 下载 JSON
            </button>
          )}
        </div>
      </header>

      <main className="max-w-screen-xl mx-auto px-6 py-6 space-y-6">
        {/* Input Controls */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 flex flex-wrap items-end gap-4">
          {/* Type toggle */}
          <div className="flex gap-1">
            {(['trace', 'session'] as const).map(t => (
              <button
                key={t}
                onClick={() => setQueryType(t)}
                className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                  queryType === t
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                按 {t === 'trace' ? 'Trace' : 'Session'}
              </button>
            ))}
          </div>

          {/* ID input */}
          <div className="flex-1 min-w-[240px]">
            <input
              type="text"
              value={queryId}
              onChange={e => setQueryId(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') handleLoad(); }}
              placeholder={queryType === 'trace' ? '输入 Trace ID...' : '输入 Session ID...'}
              className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-400"
            />
          </div>

          {/* Load button */}
          <button
            onClick={() => handleLoad()}
            disabled={loading || !queryId.trim()}
            className="px-4 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? '加载中...' : '加载'}
          </button>

          {/* File import */}
          <input
            ref={fileInputRef}
            type="file"
            accept=".json"
            onChange={handleFileImport}
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm rounded-lg transition-colors"
          >
            📁 导入 JSON
          </button>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-600 text-sm">
            ⚠️ {error}
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-16">
            <div className="text-center">
              <div className="animate-spin text-4xl mb-4">\u23f3</div>
              <p className="text-gray-600">加载中...</p>
            </div>
          </div>
        )}

        {/* Empty state */}
        {!loading && !doc && !error && (
          <div className="flex items-center justify-center py-24">
            <div className="text-center">
              <div className="text-5xl mb-4">🔍</div>
              <p className="text-gray-500">请输入 Trace 或 Session ID，然后点击「加载」</p>
              <p className="text-gray-400 text-sm mt-1">或导入本地 ATIF JSON 文件</p>
            </div>
          </div>
        )}

        {/* Loaded content */}
        {doc && !loading && (
          <>
            {/* Agent info + Metrics */}
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
              <AgentInfoCard doc={doc} />
              {computedMetrics && (
                <>
                  <MetricCard
                    label="总步骤数"
                    value={String(computedMetrics.steps)}
                    color="text-indigo-600"
                  />
                  <MetricCard
                    label="总输入 Token"
                    value={fmtTokens(computedMetrics.prompt)}
                    color="text-blue-600"
                    sub={computedMetrics.cached > 0 ? `其中缓存: ${fmtTokens(computedMetrics.cached)}` : undefined}
                  />
                  <MetricCard
                    label="总输出 Token"
                    value={fmtTokens(computedMetrics.completion)}
                    color="text-green-600"
                  />
                </>
              )}
            </div>

            {/* Step Timeline */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                交互轨迹
                <span className="ml-2 text-sm font-normal text-gray-400">
                  共 {doc.steps.length} 步
                </span>
              </h2>

              {doc.steps.length === 0 ? (
                <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
                  <div className="text-4xl mb-2">\ud83d\udced</div>
                  <p className="text-gray-400">该轨迹暂无步骤数据</p>
                </div>
              ) : (
                <div className="relative pl-4">
                  {/* Vertical line */}
                  <div className="absolute left-[5px] top-4 bottom-4 w-0.5 bg-gray-200" />

                  {doc.steps.map(step => (
                    <StepCard
                      key={step.step_id}
                      step={step}
                      expandedSections={expandedSections}
                      onToggleSection={toggleSection}
                    />
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </main>
    </>
  );
};
