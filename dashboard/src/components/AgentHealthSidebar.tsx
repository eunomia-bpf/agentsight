import React, { useState, useEffect, useRef, useCallback } from 'react';
import { fetchAgentHealth, deleteAgentHealth, restartAgentHealth } from '../utils/apiClient';
import type { AgentHealthStatus } from '../types';

/** Status dot color mapping */
const STATUS_COLORS: Record<string, string> = {
  healthy: 'bg-green-500',
  unhealthy: 'bg-red-500',
  hung: 'bg-orange-500',
  unknown: 'bg-yellow-400',
  no_port: 'bg-gray-400',
  offline: 'bg-red-600',
};

/** Status display label */
const STATUS_LABELS: Record<string, string> = {
  healthy: '正常',
  unhealthy: '异常',
  hung: '卡顿',
  unknown: '未知',
  no_port: '无端口',
  offline: '已下线',
};

/** Format relative time in Chinese */
function relativeTime(timestampMs: number): string {
  if (timestampMs === 0) return '—';
  const diff = Math.floor((Date.now() - timestampMs) / 1000);
  if (diff < 5) return '刚刚';
  if (diff < 60) return `${diff} 秒前`;
  if (diff < 3600) return `${Math.floor(diff / 60)} 分钟前`;
  return `${Math.floor(diff / 3600)} 小时前`;
}

/** Simple toast notification */
interface Toast {
  id: number;
  message: string;
}

const AgentCard: React.FC<{
  agent: AgentHealthStatus;
  onDelete: (pid: number) => void;
  onRestart: (pid: number) => void;
  restarting: boolean;
}> = ({ agent, onDelete, onRestart, restarting }) => {
  const dotColor = STATUS_COLORS[agent.status] || 'bg-gray-400';
  const label = STATUS_LABELS[agent.status] || agent.status;
  const isOffline = agent.status === 'offline';
  const isHung = agent.status === 'hung';
  const canRestart = isHung && !!agent.restart_cmd?.length;

  return (
    <div className={`px-3 py-2.5 border-b border-gray-100 last:border-b-0 ${
      isOffline ? 'bg-red-50' : isHung ? 'bg-orange-50' : ''
    }`}>
      <div className="flex items-center gap-2">
        <span className={`inline-block w-2 h-2 rounded-full flex-shrink-0 ${dotColor}`} />
        <span className={`font-medium text-sm truncate ${
          isOffline ? 'text-red-700' : isHung ? 'text-orange-700' : 'text-gray-900'
        }`}>
          {agent.agent_name}
        </span>
        <span className={`ml-auto text-xs flex-shrink-0 ${
          isOffline ? 'text-red-500 font-semibold' : isHung ? 'text-orange-500 font-semibold' : 'text-gray-400'
        }`}>
          {label}
        </span>
      </div>
      <div className="mt-1 ml-4 text-xs text-gray-500 space-y-0.5">
        <div>PID {agent.pid}</div>
        {agent.latency_ms !== null && agent.status === 'healthy' && (
          <span className="text-green-600">{agent.latency_ms}ms</span>
        )}
        {agent.error_message && (
          <div className={`truncate ${isHung ? 'text-orange-500' : 'text-red-500'}`} title={agent.error_message}>
            {agent.error_message}
          </div>
        )}
        <div className="text-gray-400">{relativeTime(agent.last_check_time)}</div>
        {isOffline && (
          <button
            onClick={() => onDelete(agent.pid)}
            className="mt-1 text-xs text-red-400 hover:text-red-600 underline"
          >
            确认下线并删除
          </button>
        )}
        {canRestart && (
          <button
            onClick={() => onRestart(agent.pid)}
            disabled={restarting}
            className="mt-1 text-xs text-orange-500 hover:text-orange-700 underline disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {restarting ? '重启中...' : '重启进程'}
          </button>
        )}
      </div>
    </div>
  );
};

export const AgentHealthSidebar: React.FC = () => {
  const [agents, setAgents] = useState<AgentHealthStatus[]>([]);
  const [lastScan, setLastScan] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toasts, setToasts] = useState<Toast[]>([]);
  // 正在重启的 PID 集合，用于控制按钮 disabled 状态
  const [restartingPids, setRestartingPids] = useState<Set<number>>(new Set());
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const toastIdRef = useRef(0);
  // Track which PIDs we've already notified about going offline
  const notifiedOfflineRef = useRef<Set<number>>(new Set());

  const addToast = useCallback((message: string) => {
    const id = ++toastIdRef.current;
    setToasts(prev => [...prev, { id, message }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 5000);
  }, []);

  const refresh = useCallback(async () => {
    try {
      const data = await fetchAgentHealth();

      // 检测新增离线和卡顿 agent
      data.agents.forEach(a => {
        if (a.status === 'offline' && !notifiedOfflineRef.current.has(a.pid)) {
          notifiedOfflineRef.current.add(a.pid);
          addToast(`⚠️ Agent "${a.agent_name}" (PID ${a.pid}) 已下线`);
        }
        if (a.status === 'hung' && !notifiedOfflineRef.current.has(-a.pid)) {
          notifiedOfflineRef.current.add(-a.pid); // 用负数区分 hung 通知
          addToast(`⏳ Agent "${a.agent_name}" (PID ${a.pid}) 响应超时，可能卡顿`);
        }
      });
      // 清理不再存在的 PID
      const currentPids = new Set(data.agents.map(a => a.pid));
      notifiedOfflineRef.current.forEach(pid => {
        const absPid = Math.abs(pid);
        if (!currentPids.has(absPid)) notifiedOfflineRef.current.delete(pid);
      });
      // 如果 hung 进程恢复正常，清除其 hung 通知记录
      data.agents.forEach(a => {
        if (a.status !== 'hung') notifiedOfflineRef.current.delete(-a.pid);
      });

      setAgents(data.agents);
      setLastScan(data.last_scan_time);
      setError(null);
    } catch (e: any) {
      setError(e.message || '请求失败');
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  const handleDelete = async (pid: number) => {
    try {
      await deleteAgentHealth(pid);
      notifiedOfflineRef.current.delete(pid);
      setAgents(prev => prev.filter(a => a.pid !== pid));
    } catch (e: any) {
      addToast(`删除失败: ${e.message}`);
    }
  };

  const handleRestart = async (pid: number) => {
    setRestartingPids(prev => new Set(prev).add(pid));
    try {
      const result = await restartAgentHealth(pid);
      addToast(`✅ 重启成功，新 PID: ${result.new_pid}，等待进程上线...`);
      // 清除 hung 通知记录
      notifiedOfflineRef.current.delete(-pid);
      // 立即从本地列表删除旧条目，不等下次扫描（新 PID 会在 30s 内自动出现）
      setAgents(prev => prev.filter(a => a.pid !== pid));
    } catch (e: any) {
      addToast(`重启失败: ${e.message}`);
    } finally {
      setRestartingPids(prev => {
        const next = new Set(prev);
        next.delete(pid);
        return next;
      });
    }
  };

  useEffect(() => {
    refresh();
    timerRef.current = setInterval(refresh, 10_000);
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [refresh]);

  // 排序: offline 首位（告警），其次 hung，然后 unhealthy，再 healthy，最后 no_port/unknown
  const sorted = [...agents].sort((a, b) => {
    const order: Record<string, number> = { offline: 0, hung: 1, unhealthy: 2, healthy: 3, unknown: 4, no_port: 5 };
    return (order[a.status] ?? 6) - (order[b.status] ?? 6);
  });

  const healthyCount = agents.filter(a => a.status === 'healthy').length;
  const offlineCount = agents.filter(a => a.status === 'offline').length;
  const hungCount = agents.filter(a => a.status === 'hung').length;
  const totalCount = agents.length;

  return (
    <>
      {/* Toast notifications */}
      <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
        {toasts.map(t => (
          <div key={t.id}
            className="bg-red-600 text-white text-xs px-4 py-2 rounded shadow-lg animate-pulse pointer-events-auto">
            {t.message}
          </div>
        ))}
      </div>

      <aside className="w-64 flex-shrink-0 border-l border-gray-200 bg-white overflow-y-auto"
             style={{ height: 'calc(100vh - 56px)' }}>
        {/* Header */}
        <div className="px-3 py-3 border-b border-gray-200 flex items-center justify-between">
          <span className="text-sm font-semibold text-gray-800">Agent 状态</span>
          <div className="flex items-center gap-1">
            {offlineCount > 0 && (
              <span className="text-xs px-1.5 py-0.5 rounded-full bg-red-100 text-red-600 font-semibold">
                {offlineCount} 下线
              </span>
            )}
            {hungCount > 0 && (
              <span className="text-xs px-1.5 py-0.5 rounded-full bg-orange-100 text-orange-600 font-semibold">
                {hungCount} 卡顿
              </span>
            )}
            {totalCount > 0 && (
              <span className="text-xs px-1.5 py-0.5 rounded-full bg-gray-100 text-gray-600">
                {healthyCount}/{totalCount}
              </span>
            )}
          </div>
        </div>

        {/* Content */}
        {loading ? (
          <div className="px-3 py-6 text-center text-xs text-gray-400">加载中...</div>
        ) : error ? (
          <div className="px-3 py-6 text-center text-xs text-red-400">{error}</div>
        ) : sorted.length === 0 ? (
          <div className="px-3 py-6 text-center text-xs text-gray-400">暂无已发现的 Agent</div>
        ) : (
          <div>
            {sorted.map(agent => (
              <AgentCard
                key={agent.pid}
                agent={agent}
                onDelete={handleDelete}
                onRestart={handleRestart}
                restarting={restartingPids.has(agent.pid)}
              />
            ))}
          </div>
        )}

        {/* Footer */}
        {lastScan > 0 && (
          <div className="px-3 py-2 border-t border-gray-100 text-xs text-gray-400">
            上次扫描: {relativeTime(lastScan)}
          </div>
        )}
      </aside>
    </>
  );
};

