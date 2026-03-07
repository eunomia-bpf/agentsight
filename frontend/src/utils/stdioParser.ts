// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

export type StdioMessageKind =
  | 'request'
  | 'notification'
  | 'response'
  | 'error'
  | 'text'
  | 'unknown';

export interface DecodedStdioMessage {
  direction: string;
  fdRole: string;
  fdTarget: string;
  fd: number | null;
  length: number;
  truncated: boolean;
  rawPayload: string;
  parsedPayload: any | null;
  kind: StdioMessageKind;
  method?: string;
  id?: string;
  toolName?: string;
  preview?: string;
  title: string;
  summary: string;
}

function safeJsonParse(value: string): any | null {
  if (!value.trim()) return null;

  try {
    return JSON.parse(value);
  } catch {
    return null;
  }
}

function truncateText(value: string, limit = 96): string {
  const normalized = value.replace(/\s+/g, ' ').trim();
  if (normalized.length <= limit) {
    return normalized;
  }
  return `${normalized.slice(0, limit - 3)}...`;
}

function stringifyId(value: unknown): string | undefined {
  if (value === null || value === undefined) return undefined;
  return String(value);
}

function extractToolName(parsedPayload: any): string | undefined {
  const toolName = parsedPayload?.params?.name;
  return typeof toolName === 'string' && toolName.length > 0 ? toolName : undefined;
}

function extractPreview(parsedPayload: any, kind: StdioMessageKind): string | undefined {
  if (!parsedPayload || typeof parsedPayload !== 'object') {
    return undefined;
  }

  if (kind === 'request' || kind === 'notification') {
    const args = parsedPayload.params?.arguments;
    if (typeof args?.text === 'string' && args.text.length > 0) {
      return truncateText(args.text);
    }

    const method = parsedPayload.method;
    if (method === 'tools/call' && typeof parsedPayload.params?.name === 'string') {
      return parsedPayload.params.name;
    }

    if (method === 'tools/list') {
      return 'list tools';
    }

    if (method === 'initialize') {
      return parsedPayload.params?.clientInfo?.name || 'initialize';
    }

    return undefined;
  }

  if (kind === 'response') {
    const content = parsedPayload.result?.content;
    if (Array.isArray(content) && typeof content[0]?.text === 'string') {
      return truncateText(content[0].text);
    }

    if (Array.isArray(parsedPayload.result?.tools)) {
      return `${parsedPayload.result.tools.length} tools`;
    }

    const protocolVersion = parsedPayload.result?.protocolVersion;
    if (typeof protocolVersion === 'string') {
      return protocolVersion;
    }

    return undefined;
  }

  if (kind === 'error') {
    const message = parsedPayload.error?.message;
    return typeof message === 'string' ? truncateText(message) : undefined;
  }

  return undefined;
}

function buildTitle(
  kind: StdioMessageKind,
  method: string | undefined,
  id: string | undefined,
  toolName: string | undefined
): string {
  switch (kind) {
    case 'request':
      if (method === 'tools/call' && toolName) return `tools/call ${toolName}`;
      return method ? `request ${method}` : 'stdio request';
    case 'notification':
      return method ? `notification ${method}` : 'stdio notification';
    case 'response':
      return id ? `response #${id}` : 'stdio response';
    case 'error':
      return id ? `error #${id}` : 'stdio error';
    case 'text':
      return 'stdio text';
    default:
      return 'stdio event';
  }
}

function buildSummary(
  direction: string,
  fdRole: string,
  kind: StdioMessageKind,
  method: string | undefined,
  id: string | undefined,
  toolName: string | undefined,
  preview: string | undefined,
  rawPayload: string
): string {
  const role = fdRole || 'fd';
  const directionLabel = direction || 'STDIO';

  if (kind === 'request' || kind === 'notification') {
    const action = method || 'message';
    const toolSuffix = toolName && method === 'tools/call' ? ` ${toolName}` : '';
    const previewSuffix = preview && preview !== toolName ? ` · ${preview}` : '';
    return `${directionLabel} ${role} ${action}${toolSuffix}${previewSuffix}`;
  }

  if (kind === 'response' || kind === 'error') {
    const idSuffix = id ? ` #${id}` : '';
    const previewSuffix = preview ? ` · ${preview}` : '';
    return `${directionLabel} ${role} ${kind}${idSuffix}${previewSuffix}`;
  }

  if (preview) {
    return `${directionLabel} ${role} · ${preview}`;
  }

  if (rawPayload.trim()) {
    return `${directionLabel} ${role} · ${truncateText(rawPayload)}`;
  }

  return `${directionLabel} ${role}`;
}

export function isStdioSource(source: string): boolean {
  return String(source || '').toLowerCase().trim() === 'stdio';
}

export function decodeStdioMessage(data: any): DecodedStdioMessage {
  const rawPayload = typeof data?.data === 'string' ? data.data : '';
  const parsedPayload = safeJsonParse(rawPayload);
  const direction = String(data?.direction || '').toUpperCase();
  const fdRole = String(data?.fd_role || (data?.fd !== undefined ? `fd ${data.fd}` : 'stdio'));
  const fdTarget = String(data?.fd_target || '');
  const fd = typeof data?.fd === 'number' ? data.fd : null;
  const length = typeof data?.len === 'number' ? data.len : 0;
  const truncated = Boolean(data?.truncated);

  let kind: StdioMessageKind = rawPayload.trim() ? 'text' : 'unknown';
  let method: string | undefined;
  let id: string | undefined;

  if (parsedPayload && typeof parsedPayload === 'object') {
    method = typeof parsedPayload.method === 'string' ? parsedPayload.method : undefined;
    id = stringifyId(parsedPayload.id);

    if (method) {
      kind = id ? 'request' : 'notification';
    } else if (parsedPayload.result !== undefined) {
      kind = 'response';
    } else if (parsedPayload.error !== undefined) {
      kind = 'error';
    } else {
      kind = 'unknown';
    }
  }

  const toolName = extractToolName(parsedPayload);
  const preview = parsedPayload ? extractPreview(parsedPayload, kind) : truncateText(rawPayload);
  const title = buildTitle(kind, method, id, toolName);
  const summary = buildSummary(
    direction,
    fdRole,
    kind,
    method,
    id,
    toolName,
    preview,
    rawPayload
  );

  return {
    direction,
    fdRole,
    fdTarget,
    fd,
    length,
    truncated,
    rawPayload,
    parsedPayload,
    kind,
    method,
    id,
    toolName,
    preview,
    title,
    summary,
  };
}

export function formatStdioExpandedContent(decoded: DecodedStdioMessage): string {
  const sections = [
    `Direction: ${decoded.direction || 'UNKNOWN'}`,
    `FD Role: ${decoded.fdRole || 'unknown'}`,
  ];

  if (decoded.fd !== null) {
    sections.push(`FD: ${decoded.fd}`);
  }

  if (decoded.fdTarget) {
    sections.push(`Target: ${decoded.fdTarget}`);
  }

  sections.push(`Kind: ${decoded.kind}`);

  if (decoded.method) {
    sections.push(`Method: ${decoded.method}`);
  }

  if (decoded.toolName) {
    sections.push(`Tool: ${decoded.toolName}`);
  }

  if (decoded.id) {
    sections.push(`Message ID: ${decoded.id}`);
  }

  sections.push(`Length: ${decoded.length}`);
  sections.push(`Truncated: ${decoded.truncated ? 'yes' : 'no'}`);

  const payload =
    decoded.parsedPayload !== null
      ? JSON.stringify(decoded.parsedPayload, null, 2)
      : decoded.rawPayload;

  return `${sections.join('\n')}\n\nPayload\n${'-'.repeat(7)}\n${payload}`;
}
