// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import {
  TreeAuditEvent,
  TreeEventType,
  eventDetails,
  eventModel,
  eventName,
  eventTarget,
  treeEventType,
} from '@/utils/eventParsers';
import { decodeStdioMessage } from '@/utils/stdioParser';
import { UnifiedBlockData } from './UnifiedBlock';
import {
  CheckCircleIcon,
  CommandLineIcon,
  CpuChipIcon,
  DocumentIcon,
  LockClosedIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';

type Icon = UnifiedBlockData['icon'];

const STYLE_BY_TYPE: Record<TreeEventType, {
  tag: string;
  gradient: string;
  border: string;
  iconColor: string;
  icon: Icon;
}> = {
  prompt: {
    tag: 'tag.aiPrompt',
    gradient: 'bg-gradient-to-r from-blue-50 via-purple-50 to-pink-50',
    border: 'border-blue-400',
    iconColor: 'text-blue-600',
    icon: SparklesIcon,
  },
  response: {
    tag: 'tag.aiResponse',
    gradient: 'bg-gradient-to-r from-green-50 via-emerald-50 to-teal-50',
    border: 'border-green-400',
    iconColor: 'text-green-600',
    icon: CheckCircleIcon,
  },
  file: {
    tag: 'FILE',
    gradient: 'bg-gradient-to-r from-cyan-50 via-sky-50 to-blue-50',
    border: 'border-cyan-400',
    iconColor: 'text-cyan-700',
    icon: DocumentIcon,
  },
  process: {
    tag: 'PROCESS',
    gradient: 'bg-gradient-to-r from-purple-50 via-violet-50 to-indigo-50',
    border: 'border-purple-400',
    iconColor: 'text-purple-700',
    icon: CpuChipIcon,
  },
  stdio: {
    tag: 'tag.stdio',
    gradient: 'bg-gradient-to-r from-slate-50 via-indigo-50 to-sky-50',
    border: 'border-indigo-400',
    iconColor: 'text-indigo-700',
    icon: CommandLineIcon,
  },
  ssl: {
    tag: 'tag.ssl',
    gradient: 'bg-gradient-to-r from-orange-50 via-amber-50 to-yellow-50',
    border: 'border-orange-400',
    iconColor: 'text-orange-600',
    icon: LockClosedIcon,
  },
  system: {
    tag: 'SYSTEM',
    gradient: 'bg-gradient-to-r from-gray-50 via-slate-50 to-zinc-50',
    border: 'border-gray-400',
    iconColor: 'text-gray-700',
    icon: CpuChipIcon,
  },
};

export function adaptEventToUnifiedBlock(event: TreeAuditEvent): UnifiedBlockData {
  const type = treeEventType(event);
  const style = styleForEvent(type, event);
  const expandedContent = expandedEventContent(event, type);
  const tags = [
    style.tag,
    promptSourceTag(event, type),
    eventModel(event),
    event.action?.toUpperCase(),
    event.status,
    event.pid ? `PID ${event.pid}` : '',
  ].filter(Boolean) as string[];

  return {
    id: event.id,
    type,
    timestamp: event.timestamp_ms,
    tags,
    bgGradient: style.gradient,
    borderColor: style.border,
    iconColor: style.iconColor,
    icon: style.icon,
    foldContent: foldedEventContent(event, expandedContent),
    expandedContent,
  };
}

function promptSourceTag(event: TreeAuditEvent, type: TreeEventType): string {
  const source = eventDetails(event).prompt_source;
  return type === 'prompt' && typeof source === 'string' ? source.toUpperCase() : '';
}

function styleForEvent(type: TreeEventType, event: TreeAuditEvent) {
  if (type === 'process' && event.action === 'exit') {
    return {
      ...STYLE_BY_TYPE.process,
      gradient: 'bg-gradient-to-r from-red-50 via-rose-50 to-pink-50',
      border: 'border-red-400',
      iconColor: 'text-red-700',
    };
  }
  if (type === 'prompt' && event.promptDiff?.hasChanges) {
    return {
      ...STYLE_BY_TYPE.prompt,
      gradient: 'bg-gradient-to-r from-yellow-50 via-orange-50 to-red-50',
      border: 'border-yellow-400',
      iconColor: 'text-yellow-600',
    };
  }
  return STYLE_BY_TYPE[type];
}

function foldedEventContent(event: TreeAuditEvent, expandedContent: string): string {
  if (event.promptDiff?.hasChanges && event.promptDiff.summary) {
    return `Changed: ${event.promptDiff.summary}`;
  }
  return event.summary
    || eventTarget(event)
    || preview(expandedContent, 120)
    || eventName(event);
}

function expandedEventContent(event: TreeAuditEvent, type: TreeEventType): string {
  const details = eventDetails(event);
  let content = '';

  if (type === 'stdio') {
    content = formatStdio(details);
  } else if (type === 'prompt' && typeof details.text_content === 'string' && details.text_content.trim()) {
    content = formatPromptDetails(details);
  } else if (typeof details.json_content === 'string' && details.json_content.trim()) {
    content = formatJsonish(details.json_content);
  } else if (typeof details.text_content === 'string' && details.text_content.trim()) {
    content = details.text_content.trim();
  } else if (typeof details.body === 'string' && details.body.trim()) {
    content = formatJsonish(details.body);
  } else {
    content = JSON.stringify(event.details ?? event, null, 2);
  }

  if (event.promptDiff?.hasChanges && event.promptDiff.diff) {
    return [
      '=== CHANGES FROM PREVIOUS PROMPT ===',
      event.promptDiff.diff,
      '',
      '=== FULL CONTENT ===',
      content,
    ].join('\n');
  }

  return content;
}

function formatPromptDetails(details: Record<string, any>): string {
  const { text_content, prompt, ...meta } = details;
  const text = text_content.trim();
  return Object.keys(meta).length > 0
    ? `${text}\n\n${JSON.stringify(meta, null, 2)}`
    : text;
}

function formatStdio(details: Record<string, any>): string {
  const decoded = decodeStdioMessage(details);
  return decoded.parsedPayload !== null
    ? JSON.stringify(decoded.parsedPayload, null, 2)
    : decoded.rawPayload || JSON.stringify(details, null, 2);
}

function formatJsonish(value: string): string {
  const decoded = parseMaybeString(value);
  if (typeof decoded !== 'string') return JSON.stringify(decoded, null, 2);
  const parsed = safeJsonParse(decoded);
  return parsed ? JSON.stringify(parsed, null, 2) : decoded;
}

function parseMaybeString(value: string): unknown {
  const parsed = safeJsonParse(value);
  return typeof parsed === 'string' ? parsed : parsed ?? value;
}

function safeJsonParse(value: string): unknown | null {
  try {
    return JSON.parse(value);
  } catch {
    return null;
  }
}

function preview(value: string, limit: number): string {
  const normalized = value.replace(/\s+/g, ' ').trim();
  return normalized.length > limit ? `${normalized.slice(0, limit - 3)}...` : normalized;
}
