// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

export const en = {
  // App (page.tsx)
  'app.title': 'AgentSight Analyzer',
  'app.subtitle': 'Upload and analyze eBPF agent trace logs with dual view modes',
  'app.eventsLoaded': '{count} events loaded',
  'app.file': 'File:',
  'app.syncing': 'Syncing...',
  'app.logView': 'Log View',
  'app.timelineView': 'Timeline View',
  'app.processTree': 'Process Tree',
  'app.metrics': 'Metrics',
  'app.hideLog': 'Hide Log',
  'app.uploadLog': 'Upload Log',
  'app.syncData': 'Sync Data',
  'app.clearData': 'Clear Data',
  'app.loadingEvents': 'Loading events from server...',
  'app.noEventsLoaded': 'No events loaded',
  'app.syncFromServer': 'Sync Data from Server',
  'app.uploadLogFile': 'Upload Log File',

  // Upload (UploadPanel.tsx)
  'upload.title': 'Upload Log File',
  'upload.chooseFile': 'Choose log file',
  'upload.or': 'or',
  'upload.pasteContent': 'Paste log content',
  'upload.pastePlaceholder': 'Paste log content here (e.g., from {path})',
  'upload.parseLog': 'Parse Log',
  'upload.parsing': 'Parsing log content...',

  // Modal (EventModal.tsx)
  'modal.eventDetails': 'Event Details',
  'modal.id': 'ID',
  'modal.source': 'Source',
  'modal.process': 'Process',
  'modal.pid': 'PID',
  'modal.time': 'Time',
  'modal.timestamp': 'Timestamp',
  'modal.unixTimestamp': 'Unix Timestamp',
  'modal.decodedStdio': 'Decoded Stdio',
  'modal.direction': 'Direction',
  'modal.fdRole': 'FD Role',
  'modal.kind': 'Kind',
  'modal.messageId': 'Message ID',
  'modal.method': 'Method',
  'modal.tool': 'Tool',
  'modal.rawData': 'Raw Data',

  // Filters (EventFilters.tsx)
  'filter.searchEvents': 'Search events...',
  'filter.allSources': 'All Sources',
  'filter.allProcesses': 'All Processes',
  'filter.allPids': 'All PIDs',
  'filter.pid': 'PID {pid}',

  // Process Tree (ProcessTreeView.tsx)
  'processTree.title': 'Process Tree & AI Prompts',
  'processTree.subtitle': 'Hierarchical view of processes with their AI prompts and API calls',
  'processTree.noProcesses': 'No processes to display',
  'processTree.noMatch': 'No processes match the current filters',

  // Process Tree Filters (ProcessTreeFilters.tsx)
  'processTree.filters': 'Filters',
  'processTree.active': 'Active',
  'processTree.aiOnly': 'AI Only',
  'processTree.filesOnly': 'Files Only',
  'processTree.processesOnly': 'Processes Only',
  'processTree.showing': 'Showing {filtered} of {total} events',
  'processTree.clearAll': 'Clear all',
  'processTree.search': 'Search',
  'processTree.searchPlaceholder': 'Search in content, models, commands...',
  'processTree.eventTypes': 'Event Types',
  'processTree.aiModels': 'AI Models',
  'processTree.sources': 'Sources',
  'processTree.commands': 'Commands',
  'processTree.timeRange': 'Time Range',
  'processTree.to': 'to',

  // Process Node badges (ProcessNode.tsx)
  'badge.prompt_one': '{count} prompt',
  'badge.prompt_other': '{count} prompts',
  'badge.response_one': '{count} response',
  'badge.response_other': '{count} responses',
  'badge.ssl': '{count} SSL',
  'badge.file_one': '{count} file',
  'badge.file_other': '{count} files',
  'badge.process': '{count} process',
  'badge.stdio': '{count} stdio',

  // Tags (BlockAdapters.tsx -> rendered in UnifiedBlock.tsx)
  'tag.aiPrompt': 'AI PROMPT',
  'tag.aiResponse': 'AI RESPONSE',
  'tag.changed': 'CHANGED',
  'tag.ssl': 'SSL',
  'tag.stdio': 'STDIO',

  // Resource Metrics (ResourceMetricsView.tsx)
  'metrics.noData': 'No system resource metrics available',
  'metrics.noDataHint': 'System metrics are captured when using --system flag or the record command',
  'metrics.title': 'Resource Metrics',
  'metrics.cpu': 'CPU',
  'metrics.memory': 'Memory',
  'metrics.allProcesses': 'All Processes ({count} samples)',
  'metrics.processOption': '{comm} (PID {pid}) - {count} samples',
  'metrics.avgCpu': 'Avg CPU',
  'metrics.peakCpu': 'Peak CPU',
  'metrics.avgMemory': 'Avg Memory',
  'metrics.peakMemory': 'Peak Memory',
  'metrics.alerts': 'Alerts',
  'metrics.cpuOverTime': 'CPU Usage Over Time',
  'metrics.memoryOverTime': 'Memory Usage Over Time',
  'metrics.dataPoints': '{count} data points',
  'metrics.detailedMetrics': 'Detailed Metrics',
  'metrics.table.time': 'Time',
  'metrics.table.process': 'Process',
  'metrics.table.pid': 'PID',
  'metrics.table.cpuPercent': 'CPU %',
  'metrics.table.memoryRss': 'Memory (RSS)',
  'metrics.table.threads': 'Threads',
  'metrics.table.children': 'Children',

  // Timeline (Timeline.tsx)
  'timeline.title': 'Timeline View',
  'timeline.durationInfo': 'Duration: {duration} \u2022 {count} events',
  'timeline.zoomHelp': 'Use mouse wheel + Ctrl/Cmd to zoom, or Ctrl/Cmd + +/- keys. Press Ctrl/Cmd + 0 to reset.',
  'timeline.scrollHelp': 'Scroll with mouse wheel or arrow keys when zoomed.',
  'timeline.noEvents': 'No events to display',
  'timeline.eventDetails': 'Timeline Event Details',

  // Zoom Controls (ZoomControls.tsx)
  'timeline.zoomOut': 'Zoom Out',
  'timeline.zoomIn': 'Zoom In',
  'timeline.resetZoom': 'Reset Zoom',
  'timeline.reset': 'Reset',
  'timeline.scrollLeft': 'Scroll Left',
  'timeline.scroll': 'Scroll',
  'timeline.scrollRight': 'Scroll Right',

  // Timeline Minimap (TimelineMinimap.tsx)
  'timeline.overview': 'Timeline Overview',
  'timeline.scrolled': '{percent}% scrolled',

  // Timeline ScrollBar (TimelineScrollBar.tsx)
  'timeline.scrollPosition': 'Scroll Position',

  // Log (LogList.tsx, LogView.tsx)
  'log.noEvents': 'No events found matching the current filters.',
  'log.eventDetails': 'Log Event Details',
} as const;
