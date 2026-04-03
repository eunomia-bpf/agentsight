import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { TraceData, TraceEvent, TraceEventChild } from '../types';

interface TraceEventsPageProps {
  data?: TraceData;
}

export const TraceEventsPage: React.FC<TraceEventsPageProps> = ({ data }) => {
  const navigate = useNavigate();
  const [traceData, setTraceData] = useState<TraceData | null>(data || null);
  const [selectedEventIndex, setSelectedEventIndex] = useState<number | null>(null);
  const [loading, setLoading] = useState(!data);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);

  // 如果没有传入数据，尝试从本地加载
  useEffect(() => {
    if (!data) {
      loadTraceData();
    }
  }, [data]);

  const loadTraceData = async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const response = await fetch('/data/trace.json');
      if (response.ok) {
        const json = await response.json();
        setTraceData(json);
      }
    } catch (error) {
      console.error('加载 trace 数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 从本地文件导入 JSON
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setLoadError(null);
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const json = JSON.parse(e.target?.result as string);
        setTraceData(json);
        setFileName(file.name);
        setSelectedEventIndex(null);
      } catch {
        setLoadError('JSON 解析失败，请检查文件格式');
      }
    };
    reader.onerror = () => setLoadError('文件读取失败');
    reader.readAsText(file);
    // 重置 input，允许重复选同一个文件
    event.target.value = '';
  };

  const handleSelectEvent = (index: number) => {
    setSelectedEventIndex(index === selectedEventIndex ? null : index);
  };

  const getEventIcon = (type: TraceEvent['type']) => {
    switch (type) {
      case 'request':
        return '📤';
      case 'response':
        return '📥';
      case 'toolcall':
        return '🔧';
      default:
        return '📋';
    }
  };

  const getEventColor = (type: TraceEvent['type']) => {
    switch (type) {
      case 'request':
        return 'bg-blue-50 border-blue-200 text-blue-700';
      case 'response':
        return 'bg-green-50 border-green-200 text-green-700';
      case 'toolcall':
        return 'bg-orange-50 border-orange-200 text-orange-700';
      default:
        return 'bg-gray-50 border-gray-200 text-gray-700';
    }
  };

  const getChildIcon = (name: string) => {
    switch (name) {
      case 'system_prompt':
        return '⚙️';
      case 'user_message':
        return '👤';
      case 'tool_call':
        return '🔧';
      case 'tool_response':
        return '📄';
      case 'assistant_response':
        return '🤖';
      case 'content':
        return '📝';
      case 'reasoning_content':
        return '💭';
      case 'tool_calls':
        return '🔨';
      default:
        return '📄';
    }
  };

  const formatContent = (content: string, maxLength: number = 100) => {
    if (content.length > maxLength) {
      return content.substring(0, maxLength) + '...';
    }
    return content;
  };

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

  if (!traceData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <span className="text-6xl">📭</span>
          <p className="mt-4 text-xl text-gray-700">暂无数据</p>
          <button
            onClick={() => navigate('/')}
            className="mt-6 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            返回首页
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/')}
                className="text-gray-600 hover:text-gray-900 transition-colors"
              >
                <span className="text-2xl">←</span>
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">事件列表</h1>
                <p className="text-sm text-gray-600 mt-1">
                  模型: {traceData.model_name} · 总 Tokens: {traceData.total_tokens.toLocaleString()}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {/* 文件导入按钮 */}
              <input
                type="file"
                accept=".json"
                onChange={handleFileSelect}
                className="hidden"
                id="trace-json-file-input"
              />
              <label
                htmlFor="trace-json-file-input"
                className="px-3 py-1.5 bg-white border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50 cursor-pointer transition-colors"
              >
                📁 导入 JSON
              </label>

              {fileName && (
                <span className="px-2 py-1 bg-green-50 text-green-700 border border-green-200 rounded text-xs max-w-[160px] truncate" title={fileName}>
                  ✅ {fileName}
                </span>
              )}

              {loadError && (
                <span className="px-2 py-1 bg-red-50 text-red-600 border border-red-200 rounded text-xs">
                  ⚠️ {loadError}
                </span>
              )}

              <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm">
                {traceData.events.length} 个事件
              </span>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* 二级饼图 - Token 分布 */}
        {traceData && <TokenDistributionCharts traceData={traceData} />}

        {/* Events List - 左右布局 */}
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">事件详情</h2>
          
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* 左侧：事件列表 */}
            <div className="lg:col-span-1 space-y-3 max-h-[600px] overflow-y-auto">
              {traceData.events.map((event, index) => {
                const children = event.children || [];
                const isSelected = selectedEventIndex === index;
                
                return (
                  <div
                    key={index}
                    onClick={() => handleSelectEvent(index)}
                    className={`bg-white rounded-lg shadow-sm border cursor-pointer transition-all ${
                      isSelected 
                        ? 'border-blue-500 ring-2 ring-blue-200' 
                        : event.type === 'request' 
                          ? 'border-blue-200 hover:border-blue-300' 
                          : event.type === 'response' 
                            ? 'border-green-200 hover:border-green-300'
                            : 'border-orange-200 hover:border-orange-300'
                    }`}
                  >
                    <div className={`flex items-center gap-3 px-4 py-3 ${getEventColor(event.type)}`}>
                      <div className="flex-shrink-0 text-xl">{getEventIcon(event.type)}</div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-sm">{event.label}</span>
                          <span className={`px-1.5 py-0.5 text-xs rounded ${getEventColor(event.type)}`}>
                            {event.type === 'request' ? '请求' : event.type === 'response' ? '响应' : '工具调用'}
                          </span>
                        </div>
                        {event.type !== 'toolcall' && (
                          <div className="text-xs mt-0.5 opacity-75">
                            {event.tokens?.toLocaleString() ?? 0} tokens · {children.length} 个子项
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* 右侧：选中事件的详细内容 */}
            <div className="lg:col-span-2">
              {selectedEventIndex !== null ? (
                <EventDetailView event={traceData.events[selectedEventIndex]} />
              ) : (
                <div className="bg-gray-50 rounded-lg border border-gray-200 p-8 text-center h-full flex items-center justify-center">
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

// 统计摘要饼图颜色
const SUMMARY_COLORS = [
  '#3B82F6', // 蓝色
  '#10B981', // 绿色
  '#F59E0B', // 橙色
  '#EF4444', // 红色
  '#8B5CF6', // 紫色
  '#EC4899', // 粉色
  '#06B6D4', // 青色
  '#84CC16', // 黄绿色
];

// 事件详情视图组件
const EventDetailView: React.FC<{ event: TraceEvent }> = ({ event }) => {
  const getChildIcon = (name: string) => {
    switch (name) {
      case 'system_prompt':
        return '⚙️';
      case 'user_message':
        return '👤';
      case 'tool_call':
        return '🔧';
      case 'tool_response':
        return '📄';
      case 'assistant_response':
        return '🤖';
      case 'content':
        return '📝';
      case 'reasoning_content':
        return '💭';
      case 'tool_calls':
        return '🔨';
      default:
        return '📄';
    }
  };

  const getChildColor = (name: string) => {
    switch (name) {
      case 'system_prompt':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      case 'user_message':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'tool_call':
        return 'bg-orange-50 text-orange-700 border-orange-200';
      case 'tool_response':
        return 'bg-teal-50 text-teal-700 border-teal-200';
      case 'assistant_response':
        return 'bg-green-50 text-green-700 border-green-200';
      case 'content':
        return 'bg-indigo-50 text-indigo-700 border-indigo-200';
      case 'reasoning_content':
        return 'bg-pink-50 text-pink-700 border-pink-200';
      case 'tool_calls':
        return 'bg-yellow-50 text-yellow-700 border-yellow-200';
      default:
        return 'bg-gray-50 text-gray-700 border-gray-200';
    }
  };

  // 获取事件类型标签
  const getEventTypeLabel = (type: TraceEvent['type']) => {
    switch (type) {
      case 'request': return '请求';
      case 'response': return '响应';
      case 'toolcall': return '工具调用';
      default: return type;
    }
  };

  // 获取事件头部背景色
  const getEventHeaderBg = (type: TraceEvent['type']) => {
    switch (type) {
      case 'request': return 'bg-blue-50 border-blue-200';
      case 'response': return 'bg-green-50 border-green-200';
      case 'toolcall': return 'bg-orange-50 border-orange-200';
      default: return 'bg-gray-50 border-gray-200';
    }
  };

  // 获取事件类型标签样式
  const getEventTypeBadge = (type: TraceEvent['type']) => {
    switch (type) {
      case 'request': return 'bg-blue-100 text-blue-700';
      case 'response': return 'bg-green-100 text-green-700';
      case 'toolcall': return 'bg-orange-100 text-orange-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  // 获取事件图标
  const getEventDetailIcon = (type: TraceEvent['type']) => {
    switch (type) {
      case 'request': return '📤';
      case 'response': return '📥';
      case 'toolcall': return '🔧';
      default: return '📋';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {/* 事件头部信息 */}
      <div className={`px-6 py-4 border-b ${getEventHeaderBg(event.type)}`}>
        <div className="flex items-center gap-3">
          <span className="text-2xl">{getEventDetailIcon(event.type)}</span>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">{event.label}</h3>
            {event.type !== 'toolcall' && (
              <p className="text-sm text-gray-600">
                {event.tokens?.toLocaleString() ?? 0} tokens · {event.percentage?.toFixed(1) ?? '0.0'}% · {event.char_count ?? 0} 字符
              </p>
            )}
          </div>
          <span className={`ml-auto px-3 py-1 text-sm rounded-full ${getEventTypeBadge(event.type)}`}>
            {getEventTypeLabel(event.type)}
          </span>
        </div>
      </div>

      {/* 统计摘要 - 饼图 */}
      {event.summary && (() => {
        // 新格式：event.summary.by_role；兼容旧格式：直接是 Record
        const summaryEntries = event.summary.by_role
          ? Object.entries(event.summary.by_role)
          : Object.entries(event.summary as any).filter(([k]) => k !== 'by_history');
        const summaryData = summaryEntries.map(([key, value]: [string, any]) => ({
          name: key, value: value.tokens, percentage: value.percentage, count: value.count
        }));
        if (summaryData.length === 0) return null;
        return (
        <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
          <h4 className="text-sm font-medium text-gray-700 mb-3">统计摘要</h4>
          <div className="flex flex-col sm:flex-row items-center gap-6">
            {/* 饼图 */}
            <div className="w-full sm:w-48 h-48">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={summaryData}
                    cx="50%"
                    cy="50%"
                    innerRadius={35}
                    outerRadius={70}
                    paddingAngle={2}
                    dataKey="value"
                    label={({ name, percent }) => percent > 0.1 ? `${(percent * 100).toFixed(0)}%` : ''}
                    labelLine={false}
                  >
                    {summaryData.map((_, idx) => (
                      <Cell key={`cell-${idx}`} fill={SUMMARY_COLORS[idx % SUMMARY_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    formatter={(value: number, name: string, props: any) => {
                      const payload = props?.payload;
                      return [`${value.toLocaleString()} tokens (${payload?.percentage?.toFixed(1) ?? 0}%) · ${payload?.count ?? 0} 条`, name];
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            {/* 图例 */}
            <div className="flex-1 grid grid-cols-2 gap-2">
              {summaryData.map((item, idx) => (
                <div key={item.name} className="flex items-center gap-2 text-sm">
                  <span 
                    className="w-3 h-3 rounded-full flex-shrink-0" 
                    style={{ backgroundColor: SUMMARY_COLORS[idx % SUMMARY_COLORS.length] }}
                  />
                  <div className="min-w-0">
                    <span className="text-gray-700 truncate block" title={item.name}>{item.name}</span>
                    <span className="text-xs text-gray-400">
                      {item.value.toLocaleString()} ({item.percentage.toFixed(1)}%) · {item.count}条
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
        );
      })()}

      {/* toolcall 类型特有展示 */}
      {event.type === 'toolcall' && (
        <div className="divide-y divide-gray-100">
          {event.cmdline && (
            <div className="p-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">命令行</h4>
              <div className="bg-gray-900 rounded-lg p-3 border border-gray-700">
                <pre className="text-sm text-green-400 font-mono whitespace-pre-wrap break-all">
                  {event.cmdline}
                </pre>
              </div>
            </div>
          )}
          {event.stdout && (
            <div className="p-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">标准输出</h4>
              <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                <pre className="text-sm text-gray-700 font-mono whitespace-pre-wrap break-all max-h-64 overflow-y-auto">
                  {event.stdout}
                </pre>
              </div>
            </div>
          )}
          {event.stderr && (
            <div className="p-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">标准错误</h4>
              <div className="bg-red-50 rounded-lg p-3 border border-red-200">
                <pre className="text-sm text-red-700 font-mono whitespace-pre-wrap break-all max-h-48 overflow-y-auto">
                  {event.stderr}
                </pre>
              </div>
            </div>
          )}
        </div>
      )}

      {/* 子项列表 */}
      {(() => {
        const children = event.children || [];
        if (children.length === 0) return null;
        return (
      <div className="divide-y divide-gray-100">
        <div className="px-6 py-3 bg-gray-50">
          <h4 className="text-sm font-medium text-gray-700">子项详情 ({children.length} 个)</h4>
        </div>
        {children.map((child, index) => (
          <div key={index} className="p-4 hover:bg-gray-50 transition-colors">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 text-xl">{getChildIcon(child.name)}</div>
              
              <div className="flex-1 min-w-0">
                {/* 子项头部 */}
                <div className="flex items-center gap-2 flex-wrap mb-2">
                  <span className="font-medium text-gray-900">{child.label}</span>
                  <span className={`px-2 py-0.5 text-xs rounded border ${getChildColor(child.name)}`}>
                    {child.tokens} tokens
                  </span>
                  {child.is_history && (
                    <span className="px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded">
                      历史
                    </span>
                  )}
                </div>

                <div className="text-xs text-gray-500 mb-2">
                  {child.percentage.toFixed(1)}% · {child.char_count} 字符
                </div>

                {/* 内容 */}
                {child.content && (
                  <div className="bg-gray-50 rounded-lg p-3 border border-gray-200 mt-2">
                    <pre className="text-sm text-gray-700 font-mono whitespace-pre-wrap break-all max-h-48 overflow-y-auto">
                      {child.content}
                    </pre>
                  </div>
                )}

                {/* Response Items */}
                {child.response_items && child.response_items.length > 0 && (
                  <div className="mt-3 space-y-2">
                    {child.response_items.map((item, idx) => (
                      <div key={idx} className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-xs font-medium text-gray-500">#{item.index}</span>
                          <span className="text-xs text-gray-400">{item.tokens} tokens · {item.char_count} 字符</span>
                        </div>
                        <pre className="text-sm text-gray-700 font-mono whitespace-pre-wrap break-all">
                          {item.content}
                        </pre>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
        );
      })()}
    </div>
  );
};

// 子项组件
const ChildItem: React.FC<{ child: TraceEventChild }> = ({ child }) => {
  const [showFullContent, setShowFullContent] = useState(false);

  const getChildIcon = (name: string) => {
    switch (name) {
      case 'system_prompt':
        return '⚙️';
      case 'user_message':
        return '👤';
      case 'tool_call':
        return '🔧';
      case 'tool_response':
        return '📄';
      case 'assistant_response':
        return '🤖';
      case 'content':
        return '📝';
      case 'reasoning_content':
        return '💭';
      case 'tool_calls':
        return '🔨';
      default:
        return '📄';
    }
  };

  const getChildColor = (name: string) => {
    switch (name) {
      case 'system_prompt':
        return 'bg-purple-50 text-purple-700';
      case 'user_message':
        return 'bg-blue-50 text-blue-700';
      case 'tool_call':
        return 'bg-orange-50 text-orange-700';
      case 'tool_response':
        return 'bg-teal-50 text-teal-700';
      case 'assistant_response':
        return 'bg-green-50 text-green-700';
      default:
        return 'bg-gray-50 text-gray-700';
    }
  };

  const hasContent = child.content && child.content.length > 0;
  const hasResponseItems = child.response_items && child.response_items.length > 0;

  return (
    <div className="px-4 py-3 hover:bg-gray-50 transition-colors">
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 text-lg mt-0.5">{getChildIcon(child.name)}</div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium text-gray-900">{child.label}</span>
            <span className={`px-2 py-0.5 text-xs rounded ${getChildColor(child.name)}`}>
              {child.tokens} tokens
            </span>
            {child.is_history && (
              <span className="px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded">
                历史
              </span>
            )}
          </div>

          <div className="text-xs text-gray-500 mt-1">
            {child.percentage.toFixed(1)}% · {child.char_count} 字符
          </div>

          {/* Content Preview */}
          {hasContent && (
            <div className="mt-2">
              <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                <pre className="text-xs text-gray-700 font-mono whitespace-pre-wrap break-all">
                  {showFullContent ? child.content : formatContent(child.content!, 150)}
                </pre>
                {child.content!.length > 150 && (
                  <button
                    onClick={() => setShowFullContent(!showFullContent)}
                    className="mt-2 text-xs text-blue-600 hover:text-blue-800"
                  >
                    {showFullContent ? '收起' : '展开'}
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Response Items */}
          {hasResponseItems && (
            <div className="mt-2 space-y-2">
              {child.response_items!.map((item, idx) => (
                <div key={idx} className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs text-gray-500">#{item.index}</span>
                    <span className="text-xs text-gray-400">{item.tokens} tokens</span>
                  </div>
                  <pre className="text-xs text-gray-700 font-mono whitespace-pre-wrap break-all">
                    {item.content}
                  </pre>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const formatContent = (content: string, maxLength: number) => {
  if (content.length > maxLength) {
    return content.substring(0, maxLength) + '...';
  }
  return content;
};

// ==================== 二级饼图组件 ====================

interface TokenDistributionChartsProps {
  traceData: TraceData;
}

// 移除调试日志的辅助函数
const debugLog = (...args: any[]) => {
  if (process.env.NODE_ENV === 'development') {
    console.log(...args);
  }
};

const TokenDistributionCharts: React.FC<TokenDistributionChartsProps> = ({ traceData }) => {
  const [selectedSegment, setSelectedSegment] = useState<'input' | 'output'>('input');

  // 调试原始数据
  debugLog('TokenDistributionCharts - traceData.summary:', traceData.summary);

  // 新格式：summary.input / summary.output；兼容旧格式：summary.by_history / summary.by_role
  const summaryInput = traceData.summary?.input;
  const summaryOutput = traceData.summary?.output;

  // by_history：优先取 top level summary.by_history，其次 summary.input.by_history
  const byHistory = traceData.summary?.by_history || summaryInput?.by_history || {};
  // by_role：优先取 top level summary.by_role，其次 summary.input.by_role
  const byRole = traceData.summary?.by_role || summaryInput?.by_role || {};

  // 输入/输出总量：优先取新格式 summary，回退 events
  const requestEvent = traceData.events?.find(e => e.type === 'request');
  const responseEvent = traceData.events?.find(e => e.type === 'response');
  const inputTotal = summaryInput?.tokens ?? requestEvent?.tokens ?? 0;
  const outputTotal = summaryOutput?.tokens ?? responseEvent?.tokens ?? 0;

  // 一级饼图数据：输入 vs 输出
  const level1Data = [
    { name: '输入', value: inputTotal, color: '#3B82F6', type: 'input' as const },
    { name: '输出', value: outputTotal, color: '#10B981', type: 'output' as const },
  ];

  // 二级饼图数据：by_history 分类细分
  const historyColors = ['#60A5FA', '#93C5FD', '#BFDBFE', '#DBEAFE', '#1D4ED8'];
  const historyDetailData = Object.entries(byHistory).map(([key, value], index) => ({
    name: key,
    value: value?.tokens || 0,
    percentage: value?.percentage || 0,
    color: historyColors[index % historyColors.length],
  }));

  // 二级饼图数据：by_role 分类细分（输出时切换到 output.by_role）
  const activeByRole = selectedSegment === 'output'
    ? (summaryOutput?.by_role || {})
    : byRole;
  const roleColors = ['#34D399', '#6EE7B7', '#A7F3D0', '#059669', '#F59E0B', '#EF4444', '#8B5CF6'];
  const roleDetailData = Object.entries(activeByRole).map(([key, value], index) => ({
    name: key,
    value: value?.tokens || 0,
    percentage: value?.percentage || 0,
    color: roleColors[index % roleColors.length],
  }));

  // 调试日志（在变量定义之后）
  debugLog('TokenDistributionCharts - inputTotal:', inputTotal, 'outputTotal:', outputTotal);
  debugLog('TokenDistributionCharts - byHistory:', byHistory, 'byRole:', byRole);
  debugLog('TokenDistributionCharts - historyDetailData:', historyDetailData);
  debugLog('TokenDistributionCharts - roleDetailData:', roleDetailData);
  debugLog('TokenDistributionCharts - level1Data:', level1Data);

  // 根据扇区填充色亮度决定 label 文字颜色（深色背景用白字，浅色背景用深灰字）
  const getLabelColor = (fill: string): string => {
    const hex = fill.replace('#', '');
    const r = parseInt(hex.substring(0, 2), 16);
    const g = parseInt(hex.substring(2, 4), 16);
    const b = parseInt(hex.substring(4, 6), 16);
    // 感知亮度公式
    const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
    return luminance > 0.55 ? '#1F2937' : '#FFFFFF';
  };

  // 饼图 label：只显示百分比，避免长文字溢出；颜色根据背景自适应
  // 位置固定在扇区厚度中点（innerRadius 和 outerRadius 的均值），避免落入中空区域
  const makeRenderPercentLabel = (colors: string[]) =>
    ({ cx, cy, midAngle, innerRadius, outerRadius, percent, index }: any) => {
      if (percent < 0.05) return null; // 小于 5% 不显示
      const RADIAN = Math.PI / 180;
      // 固定放在扇区厚度正中间
      const radius = (innerRadius + outerRadius) / 2;
      const x = cx + radius * Math.cos(-midAngle * RADIAN);
      const y = cy + radius * Math.sin(-midAngle * RADIAN);
      const fill = colors[index % colors.length];
      const textColor = getLabelColor(fill);
      // 用描边做保底，确保在任何背景上都清晰
      const strokeColor = textColor === '#FFFFFF' ? 'rgba(0,0,0,0.4)' : 'rgba(255,255,255,0.6)';
      return (
        <text
          x={x} y={y}
          fill={textColor}
          stroke={strokeColor}
          strokeWidth={3}
          paintOrder="stroke"
          textAnchor="middle"
          dominantBaseline="central"
          fontSize={11}
          fontWeight={700}
        >
          {`${(percent * 100).toFixed(1)}%`}
        </text>
      );
    };

  const level1Colors = level1Data.map(d => d.color);
  const renderLevel1Label = makeRenderPercentLabel(level1Colors);
  const renderHistoryLabel = makeRenderPercentLabel(historyColors);
  const renderRoleLabel = makeRenderPercentLabel(roleColors);

  const handleLevel1Click = (data: any) => {
    if (data && data.type) {
      setSelectedSegment(data.type);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Token 分布</h3>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 一级饼图：输入输出分布 */}
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2 text-center">输入/输出分布</h4>
          <p className="text-xs text-gray-500 mb-2 text-center">点击扇区切换</p>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={level1Data}
                cx="50%"
                cy="50%"
                innerRadius={55}
                outerRadius={90}
                paddingAngle={2}
                dataKey="value"
                onClick={handleLevel1Click}
                labelLine={false}
                label={renderLevel1Label}
              >
                {level1Data.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={entry.color}
                    stroke={selectedSegment === entry.type ? '#1F2937' : 'none'}
                    strokeWidth={selectedSegment === entry.type ? 3 : 0}
                    style={{ cursor: 'pointer' }}
                  />
                ))}
              </Pie>
              <Tooltip 
                formatter={(value: number, name: string) => {
                  const total = level1Data.reduce((s, d) => s + d.value, 0);
                  const pct = total > 0 ? (value / total * 100).toFixed(1) : '0.0';
                  return [`${value.toLocaleString()} tokens (${pct}%)`, name];
                }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex justify-center gap-4 mt-2">
            {level1Data.map((item) => (
              <button
                key={item.name}
                onClick={() => handleLevel1Click(item)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-colors ${
                  selectedSegment === item.type
                    ? 'bg-gray-100 ring-2 ring-gray-300'
                    : 'hover:bg-gray-50'
                }`}
              >
                <span 
                  className="w-3 h-3 rounded-full flex-shrink-0" 
                  style={{ backgroundColor: item.color }}
                />
                <span>{item.name}: {item.value.toLocaleString()}</span>
              </button>
            ))}
          </div>
        </div>

        {/* 二级饼图：by_history 分布 */}
        <div style={{ border: '1px solid #e5e7eb', borderRadius: '8px', padding: '12px' }}>
          <h4 className="text-sm font-medium text-gray-700 mb-1 text-center">by_history 分布</h4>
          <p className="text-xs text-gray-500 mb-2 text-center">历史消息 / 实时消息 / 系统提示词</p>
          {historyDetailData.length === 0 ? (
            <div className="text-center text-gray-400 py-8">暂无数据</div>
          ) : (
          <>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={historyDetailData}
                cx="50%"
                cy="50%"
                innerRadius={40}
                outerRadius={75}
                paddingAngle={1}
                dataKey="value"
                labelLine={false}
                label={renderHistoryLabel}
              >
                {historyDetailData.map((entry, index) => (
                  <Cell 
                    key={`history-cell-${index}`} 
                    fill={historyColors[index % historyColors.length]}
                  />
                ))}
              </Pie>
              <Tooltip 
                formatter={(value: number, name: string, props: any) => {
                  const percentage = props?.payload?.percentage;
                  return [`${value.toLocaleString()} tokens (${percentage?.toFixed(1) ?? 0}%)`, name];
                }}
              />
            </PieChart>
          </ResponsiveContainer>
          {/* 图例 */}
          <div className="mt-2 space-y-1">
            {historyDetailData.map((item, index) => (
              <div key={item.name} className="flex items-center gap-2 text-xs px-1">
                <span
                  className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                  style={{ backgroundColor: historyColors[index % historyColors.length] }}
                />
                <span className="text-gray-700 flex-1 truncate" title={item.name}>{item.name}</span>
                <span className="text-gray-400 flex-shrink-0 tabular-nums">{item.value.toLocaleString()}</span>
                <span className="text-gray-400 flex-shrink-0 tabular-nums w-10 text-right">{item.percentage.toFixed(1)}%</span>
              </div>
            ))}
          </div>
          </>
          )}
        </div>

        {/* 二级饼图：by_role 分布 */}
        <div style={{ border: '1px solid #e5e7eb', borderRadius: '8px', padding: '12px' }}>
          <h4 className="text-sm font-medium text-gray-700 mb-1 text-center">by_role 分布</h4>
          <p className="text-xs text-gray-500 mb-2 text-center">{selectedSegment === 'output' ? '输出角色分布' : '输入角色分布'}</p>
          {roleDetailData.length === 0 ? (
            <div className="text-center text-gray-400 py-8">暂无数据</div>
          ) : (
          <>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={roleDetailData}
                cx="50%"
                cy="50%"
                innerRadius={40}
                outerRadius={75}
                paddingAngle={1}
                dataKey="value"
                labelLine={false}
                label={renderRoleLabel}
              >
                {roleDetailData.map((entry, index) => (
                  <Cell 
                    key={`role-cell-${index}`} 
                    fill={roleColors[index % roleColors.length]}
                  />
                ))}
              </Pie>
              <Tooltip 
                formatter={(value: number, name: string, props: any) => {
                  const percentage = props?.payload?.percentage;
                  return [`${value.toLocaleString()} tokens (${percentage?.toFixed(1) ?? 0}%)`, name];
                }}
              />
            </PieChart>
          </ResponsiveContainer>
          {/* 图例 */}
          <div className="mt-2 space-y-1">
            {roleDetailData.map((item, index) => (
              <div key={item.name} className="flex items-center gap-2 text-xs px-1">
                <span
                  className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                  style={{ backgroundColor: roleColors[index % roleColors.length] }}
                />
                <span className="text-gray-700 flex-1 truncate" title={item.name}>{item.name}</span>
                <span className="text-gray-400 flex-shrink-0 tabular-nums">{item.value.toLocaleString()}</span>
                <span className="text-gray-400 flex-shrink-0 tabular-nums w-10 text-right">{item.percentage.toFixed(1)}%</span>
              </div>
            ))}
          </div>
          </>
          )}
        </div>
      </div>
    </div>
  );
};
