// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import type { en } from './en';

type TranslationKey = keyof typeof en;

export const zh: Record<TranslationKey, string> = {
  // App
  'app.title': 'AgentSight 分析器',
  'app.subtitle': '上传并分析 eBPF Agent 追踪日志，支持多种视图模式',
  'app.eventsLoaded': '{count} 个事件已加载',
  'app.file': '文件：',
  'app.syncing': '同步中...',
  'app.logView': '日志视图',
  'app.timelineView': '时间线视图',
  'app.processTree': '进程树',
  'app.metrics': '性能指标',
  'app.hideLog': '隐藏上传',
  'app.uploadLog': '上传日志',
  'app.syncData': '同步数据',
  'app.clearData': '清除数据',
  'app.loadingEvents': '正在从服务器加载事件...',
  'app.noEventsLoaded': '暂无事件数据',
  'app.syncFromServer': '从服务器同步数据',
  'app.uploadLogFile': '上传日志文件',

  // Upload
  'upload.title': '上传日志文件',
  'upload.chooseFile': '选择日志文件',
  'upload.or': '或',
  'upload.pasteContent': '粘贴日志内容',
  'upload.pastePlaceholder': '在此粘贴日志内容（例如来自 {path}）',
  'upload.parseLog': '解析日志',
  'upload.parsing': '正在解析日志内容...',

  // Modal
  'modal.eventDetails': '事件详情',
  'modal.id': 'ID',
  'modal.source': '来源',
  'modal.process': '进程',
  'modal.pid': 'PID',
  'modal.time': '时间',
  'modal.timestamp': '时间戳',
  'modal.unixTimestamp': 'Unix 时间戳',
  'modal.decodedStdio': '解码后的标准 I/O',
  'modal.direction': '方向',
  'modal.fdRole': 'FD 角色',
  'modal.kind': '类型',
  'modal.messageId': '消息 ID',
  'modal.method': '方法',
  'modal.tool': '工具',
  'modal.rawData': '原始数据',

  // Filters
  'filter.searchEvents': '搜索事件...',
  'filter.allSources': '全部来源',
  'filter.allProcesses': '全部进程',
  'filter.allPids': '全部 PID',
  'filter.pid': 'PID {pid}',

  // Process Tree
  'processTree.title': '进程树 & AI 提示',
  'processTree.subtitle': '以层级视图展示进程及其 AI 提示和 API 调用',
  'processTree.noProcesses': '暂无进程可显示',
  'processTree.noMatch': '没有匹配当前筛选条件的进程',

  // Process Tree Filters
  'processTree.filters': '筛选',
  'processTree.active': '已启用',
  'processTree.aiOnly': '仅 AI',
  'processTree.filesOnly': '仅文件',
  'processTree.processesOnly': '仅进程',
  'processTree.showing': '显示 {filtered} / {total} 个事件',
  'processTree.clearAll': '清除全部',
  'processTree.search': '搜索',
  'processTree.searchPlaceholder': '搜索内容、模型、命令...',
  'processTree.eventTypes': '事件类型',
  'processTree.aiModels': 'AI 模型',
  'processTree.sources': '数据来源',
  'processTree.commands': '命令',
  'processTree.timeRange': '时间范围',
  'processTree.to': '至',

  // Badges
  'badge.prompt_one': '{count} 个提示',
  'badge.prompt_other': '{count} 个提示',
  'badge.response_one': '{count} 个响应',
  'badge.response_other': '{count} 个响应',
  'badge.ssl': '{count} SSL',
  'badge.file_one': '{count} 个文件',
  'badge.file_other': '{count} 个文件',
  'badge.process': '{count} 个进程',
  'badge.stdio': '{count} 个标准 I/O',

  // Tags
  'tag.aiPrompt': 'AI 提示',
  'tag.aiResponse': 'AI 响应',
  'tag.changed': '已变更',
  'tag.ssl': 'SSL',
  'tag.stdio': '标准 I/O',

  // Resource Metrics
  'metrics.noData': '暂无系统资源指标数据',
  'metrics.noDataHint': '使用 --system 参数或 record 命令时会采集系统指标',
  'metrics.title': '资源指标',
  'metrics.cpu': 'CPU',
  'metrics.memory': '内存',
  'metrics.allProcesses': '全部进程（{count} 个采样）',
  'metrics.processOption': '{comm}（PID {pid}）- {count} 个采样',
  'metrics.avgCpu': '平均 CPU',
  'metrics.peakCpu': '峰值 CPU',
  'metrics.avgMemory': '平均内存',
  'metrics.peakMemory': '峰值内存',
  'metrics.alerts': '告警',
  'metrics.cpuOverTime': 'CPU 使用率变化',
  'metrics.memoryOverTime': '内存使用变化',
  'metrics.dataPoints': '{count} 个数据点',
  'metrics.detailedMetrics': '详细指标',
  'metrics.table.time': '时间',
  'metrics.table.process': '进程',
  'metrics.table.pid': 'PID',
  'metrics.table.cpuPercent': 'CPU %',
  'metrics.table.memoryRss': '内存 (RSS)',
  'metrics.table.threads': '线程',
  'metrics.table.children': '子进程',

  // Timeline
  'timeline.title': '时间线视图',
  'timeline.durationInfo': '持续时间：{duration} · {count} 个事件',
  'timeline.zoomHelp': '使用鼠标滚轮 + Ctrl/Cmd 缩放，或使用 Ctrl/Cmd + +/- 键。按 Ctrl/Cmd + 0 重置。',
  'timeline.scrollHelp': '缩放后可使用鼠标滚轮或方向键滚动。',
  'timeline.noEvents': '暂无事件可显示',
  'timeline.eventDetails': '时间线事件详情',

  // Zoom Controls
  'timeline.zoomOut': '缩小',
  'timeline.zoomIn': '放大',
  'timeline.resetZoom': '重置缩放',
  'timeline.reset': '重置',
  'timeline.scrollLeft': '向左滚动',
  'timeline.scroll': '滚动',
  'timeline.scrollRight': '向右滚动',

  // Timeline Minimap
  'timeline.overview': '时间线概览',
  'timeline.scrolled': '已滚动 {percent}%',

  // Timeline ScrollBar
  'timeline.scrollPosition': '滚动位置',

  // Log
  'log.noEvents': '没有找到匹配当前筛选条件的事件。',
  'log.eventDetails': '日志事件详情',
};
