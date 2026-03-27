// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import { ParsedEvent } from '@/utils/eventParsers';
import { decodeStdioMessage } from '@/utils/stdioParser';
import { UnifiedBlockData } from './UnifiedBlock';
import { 
  SparklesIcon, 
  CheckCircleIcon, 
  DocumentIcon, 
  CpuChipIcon, 
  CommandLineIcon,
  LockClosedIcon 
} from '@heroicons/react/24/outline';

// Simplified - no longer need these helper functions

function safeJsonParse(value: string): any | null {
  try {
    return JSON.parse(value);
  } catch {
    return null;
  }
}

function decodeEscapedText(value: string): string {
  const parsed = safeJsonParse(value);
  return typeof parsed === 'string' ? parsed : value;
}

/**
 * Leniently unescape JSON string escape sequences.
 * Unlike JSON.parse, this handles invalid escape sequences (e.g. from SSL
 * capture corruption) gracefully by dropping the backslash.
 */
function lenientUnescape(s: string): string {
  return s.replace(/\\(u[0-9a-fA-F]{4}|.)/g, (_, seq: string) => {
    if (seq.length === 5 && seq[0] === 'u') {
      return String.fromCharCode(parseInt(seq.substring(1), 16));
    }
    switch (seq) {
      case 'n': return '\n';
      case 't': return '\t';
      case 'r': return '\r';
      case '"': return '"';
      case '\\': return '\\';
      case '/': return '/';
      case 'b': return '\b';
      case 'f': return '\f';
      default: return seq;
    }
  });
}

/**
 * Extract a string field's raw value from potentially malformed JSON.
 * Walks the string character by character to handle corrupted escape sequences
 * that would break JSON.parse.
 */
function extractRawStringField(json: string, key: string): string | null {
  const keyStr = `"${key}"`;
  const keyIdx = json.indexOf(keyStr);
  if (keyIdx === -1) return null;

  let i = keyIdx + keyStr.length;
  while (i < json.length && (json[i] === ' ' || json[i] === ':' || json[i] === '\t')) i++;
  if (i >= json.length || json[i] !== '"') return null;
  i++; // skip opening quote

  const start = i;
  while (i < json.length) {
    if (json[i] === '\\') {
      i += 2; // skip any escape sequence (valid or not)
    } else if (json[i] === '"') {
      return json.substring(start, i);
    } else {
      i++;
    }
  }
  return json.substring(start);
}

/**
 * Format extracted content with an optional file path header line.
 */
function formatWithFilePath(content: string, filePath: string | null): string {
  if (filePath) {
    const separator = '\u2500'.repeat(Math.min(filePath.length + 2, 60));
    return `[${filePath}]\n${separator}\n${content}`;
  }
  return content;
}

function splitConcatenatedJsonObjects(value: string): string[] {
  const chunks: string[] = [];
  let start = -1;
  let depth = 0;
  let inString = false;
  let escape = false;

  for (let i = 0; i < value.length; i++) {
    const char = value[i];

    if (inString) {
      if (escape) {
        escape = false;
      } else if (char === '\\') {
        escape = true;
      } else if (char === '"') {
        inString = false;
      }
      continue;
    }

    if (char === '"') {
      inString = true;
      continue;
    }

    if (char === '{') {
      if (depth === 0) {
        start = i;
      }
      depth += 1;
      continue;
    }

    if (char === '}') {
      depth -= 1;
      if (depth === 0 && start >= 0) {
        chunks.push(value.slice(start, i + 1));
        start = -1;
      }
    }
  }

  return chunks;
}

function formatJsonContent(rawJsonContent: string): string {
  const decoded = decodeEscapedText(rawJsonContent).trim();

  const parsedWhole = safeJsonParse(decoded);
  if (parsedWhole && typeof parsedWhole === 'object') {
    const content = typeof parsedWhole.content === 'string'
      ? parsedWhole.content
      : JSON.stringify(parsedWhole, null, 2);
    const filePath = typeof parsedWhole.file_path === 'string' ? parsedWhole.file_path : null;
    return formatWithFilePath(String(content).trim(), filePath);
  }

  const chunks = splitConcatenatedJsonObjects(decoded);
  if (chunks.length === 0) {
    return decoded;
  }

  const formattedChunks = chunks.map((chunk, index) => {
    const parsedChunk = safeJsonParse(chunk);

    let content: string;
    let filePath: string | null = null;

    if (parsedChunk && typeof parsedChunk === 'object') {
      content = typeof parsedChunk.content === 'string'
        ? parsedChunk.content
        : JSON.stringify(parsedChunk, null, 2);
      filePath = typeof parsedChunk.file_path === 'string' ? parsedChunk.file_path : null;
    } else {
      // JSON.parse failed — likely corrupted escape sequences from SSL capture.
      // Try manual field extraction with lenient unescaping.
      const rawContent = extractRawStringField(chunk, 'content');
      const rawFilePath = extractRawStringField(chunk, 'file_path');

      if (rawContent !== null) {
        content = lenientUnescape(rawContent);
        filePath = rawFilePath !== null ? lenientUnescape(rawFilePath) : null;
      } else {
        // Can't locate a content field — unescape the whole chunk
        content = lenientUnescape(chunk);
      }
    }

    const formatted = formatWithFilePath(String(content).trim(), filePath);

    return chunks.length > 1
      ? `=== PART ${index + 1} ===\n${formatted}`
      : formatted;
  });

  return formattedChunks.join('\n\n');
}

/**
 * Format prompt content for display.
 * Parses JSON and unescapes string literals so \n and \t render as real whitespace.
 */
function formatPromptExpandedContent(content: string): string {
  const parsed = safeJsonParse(content);
  if (parsed && typeof parsed === 'object') {
    const pretty = JSON.stringify(parsed, null, 2);
    return lenientUnescape(pretty);
  }
  return lenientUnescape(content);
}

function formatResponseExpandedContent(event: ParsedEvent): string {
  const raw = event.metadata?.raw;
  if (raw && typeof raw === 'object') {
    if (typeof raw.json_content === 'string' && raw.json_content.trim().length > 0) {
      return formatJsonContent(raw.json_content);
    }
    if (typeof raw.text_content === 'string' && raw.text_content.trim().length > 0) {
      return raw.text_content.trim();
    }
    return JSON.stringify(raw, null, 2);
  }
  return event.content || JSON.stringify(event.metadata, null, 2);
}

export function adaptPromptEvent(event: ParsedEvent): UnifiedBlockData {
  const metadata = event.metadata || {};
  
  // Update tags to include diff info
  const tags = ['AI PROMPT', metadata.model, metadata.method].filter(Boolean);
  if (event.promptDiff?.hasChanges) {
    tags.push('CHANGED');
  }
  
  // Expanded content: include diff if available
  const rawContent = event.content || JSON.stringify(event.metadata, null, 2);
  let expandedContent = formatPromptExpandedContent(rawContent);

  // Fold content: use formatted content for preview so escape sequences are resolved
  let foldContent = expandedContent && expandedContent.length > 0
    ? expandedContent.replace(/\n/g, ' ').substring(0, 100) + (expandedContent.length > 100 ? '...' : '')
    : metadata.url || '';

  if (event.promptDiff?.summary) {
    foldContent = `📝 ${event.promptDiff.summary}`;
  }
  
  if (event.promptDiff?.diff) {
    expandedContent = `=== CHANGES FROM PREVIOUS PROMPT ===\n${event.promptDiff.diff}\n\n=== FULL CONTENT ===\n${expandedContent}`;
  }

  return {
    id: event.id,
    type: 'prompt',
    timestamp: event.timestamp,
    tags,
    bgGradient: event.promptDiff?.hasChanges 
      ? 'bg-gradient-to-r from-yellow-50 via-orange-50 to-red-50'
      : 'bg-gradient-to-r from-blue-50 via-purple-50 to-pink-50',
    borderColor: event.promptDiff?.hasChanges 
      ? 'border-yellow-400'
      : 'border-blue-400',
    iconColor: event.promptDiff?.hasChanges 
      ? 'text-yellow-600'
      : 'text-blue-600',
    icon: SparklesIcon,
    foldContent,
    expandedContent
  };
}

export function adaptResponseEvent(event: ParsedEvent): UnifiedBlockData {
  const metadata = event.metadata || {};
  const expandedContent = formatResponseExpandedContent(event);
  
  // Fold content: short preview
  const foldContent = expandedContent && expandedContent.length > 0 
    ? expandedContent.substring(0, 100) + (expandedContent.length > 100 ? '...' : '')
    : '';

  return {
    id: event.id,
    type: 'response',
    timestamp: event.timestamp,
    tags: ['AI RESPONSE', metadata.model].filter(Boolean),
    bgGradient: 'bg-gradient-to-r from-green-50 via-emerald-50 to-teal-50',
    borderColor: 'border-green-400',
    iconColor: 'text-green-600',
    icon: CheckCircleIcon,
    foldContent,
    expandedContent
  };
}

// Helper function to format file sizes
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

export function adaptFileEvent(event: ParsedEvent): UnifiedBlockData {
  const metadata = event.metadata || {};
  
  const operation = metadata.operation || metadata.event || 'file';
  const filepath = metadata.path || metadata.filepath || '';
  
  // Color scheme based on operation type - matching old FileBlock
  const getOperationColors = (op: string) => {
    const lowerOp = op.toLowerCase();
    if (lowerOp.includes('read')) return 'text-blue-600';
    if (lowerOp.includes('write')) return 'text-green-600';
    if (lowerOp.includes('open')) return 'text-purple-600';
    if (lowerOp.includes('close')) return 'text-gray-600';
    if (lowerOp.includes('delete') || lowerOp.includes('unlink')) return 'text-red-600';
    return 'text-indigo-600';
  };

  // Build tags for header
  const tags = [operation.toUpperCase()];
  if (metadata.fd !== undefined) tags.push(`FD ${metadata.fd}`);
  if (metadata.size !== undefined) tags.push(formatFileSize(metadata.size));

  // Fold content: file path
  const foldContent = filepath;

  // Expanded content: everything
  const expandedContent = event.content || JSON.stringify(event.metadata, null, 2);

  return {
    id: event.id,
    type: 'file',
    timestamp: event.timestamp,
    tags,
    bgGradient: 'bg-gradient-to-r from-cyan-50 via-sky-50 to-blue-50',
    borderColor: 'border-cyan-400',
    iconColor: getOperationColors(operation),
    icon: DocumentIcon,
    foldContent,
    expandedContent
  };
}

export function adaptProcessEvent(event: ParsedEvent): UnifiedBlockData {
  const metadata = event.metadata || {};
  
  const eventType = metadata.event || 'process';
  const comm = metadata.comm || '';
  const pid = metadata.pid || '';

  // Styling based on event type
  const getProcessColors = (eventType: string) => {
    const lowerEvent = eventType.toLowerCase();
    if (lowerEvent.includes('exec')) return { 
      icon: 'text-green-700',
      gradient: 'bg-gradient-to-r from-green-50 via-emerald-50 to-teal-50',
      border: 'border-green-400'
    };
    if (lowerEvent.includes('exit')) return { 
      icon: 'text-red-700',
      gradient: 'bg-gradient-to-r from-red-50 via-rose-50 to-pink-50',
      border: 'border-red-400'
    };
    return { 
      icon: 'text-gray-700',
      gradient: 'bg-gradient-to-r from-gray-50 via-slate-50 to-zinc-50',
      border: 'border-gray-400'
    };
  };

  const colors = getProcessColors(eventType);
  const tags = [eventType.toUpperCase()];
  if (pid) tags.push(`PID ${pid}`);

  // Fold content: command and PID
  const foldContent = comm && pid ? `${comm} (PID: ${pid})` : comm || `PID: ${pid}`;

  // Expanded content: everything
  const expandedContent = event.content || JSON.stringify(event.metadata, null, 2);

  return {
    id: event.id,
    type: 'process',
    timestamp: event.timestamp,
    tags,
    bgGradient: colors.gradient,
    borderColor: colors.border,
    iconColor: colors.icon,
    icon: CpuChipIcon,
    foldContent,
    expandedContent
  };
}

export function adaptSSLEvent(event: ParsedEvent): UnifiedBlockData {
  const metadata = event.metadata || {};
  
  const direction = metadata.direction || '';
  const size = metadata.data_size || metadata.size || 0;
  const comm = metadata.comm || '';

  // Fold content: size and command
  const foldContent = comm ? `${size} bytes - ${comm}` : `${size} bytes`;

  // Expanded content: everything
  const expandedContent = event.content || JSON.stringify(event.metadata, null, 2);

  return {
    id: event.id,
    type: 'ssl',
    timestamp: event.timestamp,
    tags: ['SSL', direction.toUpperCase(), `${size} bytes`].filter(Boolean),
    bgGradient: 'bg-gradient-to-r from-orange-50 via-amber-50 to-yellow-50',
    borderColor: 'border-orange-400',
    iconColor: 'text-orange-600',
    icon: LockClosedIcon,
    foldContent,
    expandedContent
  };
}

export function adaptStdioEvent(event: ParsedEvent): UnifiedBlockData {
  const metadata = event.metadata || {};
  const decoded = decodeStdioMessage(metadata);
  const tags = ['STDIO', decoded.direction || 'UNKNOWN', decoded.fdRole.toUpperCase()];

  if (decoded.method) {
    tags.push(decoded.method);
  } else if (decoded.kind !== 'text' && decoded.kind !== 'unknown') {
    tags.push(decoded.kind.toUpperCase());
  }

  if (decoded.toolName) {
    tags.push(decoded.toolName);
  }

  return {
    id: event.id,
    type: 'stdio',
    timestamp: event.timestamp,
    tags,
    bgGradient: 'bg-gradient-to-r from-slate-50 via-indigo-50 to-sky-50',
    borderColor: 'border-indigo-400',
    iconColor: 'text-indigo-700',
    icon: CommandLineIcon,
    foldContent: decoded.summary,
    expandedContent: event.content || JSON.stringify(event.metadata, null, 2)
  };
}

// Main adapter function
export function adaptEventToUnifiedBlock(event: ParsedEvent): UnifiedBlockData {
  switch (event.type) {
    case 'prompt':
      return adaptPromptEvent(event);
    case 'response':
      return adaptResponseEvent(event);
    case 'file':
      return adaptFileEvent(event);
    case 'process':
      return adaptProcessEvent(event);
    case 'stdio':
      return adaptStdioEvent(event);
    case 'ssl':
    default:
      return adaptSSLEvent(event);
  }
}
