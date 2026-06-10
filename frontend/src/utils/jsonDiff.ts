// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import { Change, diffLines } from 'diff';

export function comparePrompts(oldPrompt: any, newPrompt: any): {
  diff: string;
  summary: string;
  hasChanges: boolean;
} {
  const oldText = promptText(oldPrompt);
  const newText = promptText(newPrompt);

  if (!oldText || !newText) {
    return {
      diff: 'Unable to extract prompt content',
      summary: 'Unable to compare prompts',
      hasChanges: false,
    };
  }

  const changes = diffLines(oldText, newText);
  const added = changedLines(changes, 'added');
  const removed = changedLines(changes, 'removed');

  return {
    diff: formatDiff(changes),
    summary: added || removed
      ? `${added} added lines, ${removed} removed lines`
      : 'No changes detected',
    hasChanges: added > 0 || removed > 0,
  };
}

function promptText(data: any): string {
  const prompt = extractPrompt(data);
  if (!prompt) return '';

  if (Array.isArray(prompt.messages)) {
    return prompt.messages.map((message: any, index: number) => {
      const role = String(message.role || 'unknown').toUpperCase();
      return `[${index}] ${role}:\n${contentText(message.content)}`;
    }).join('\n\n---\n\n');
  }

  if (typeof prompt.prompt === 'string') return prompt.prompt;
  return JSON.stringify(prompt, null, 2);
}

function extractPrompt(data: any): any | null {
  if (typeof data?.body === 'string') {
    try {
      return JSON.parse(data.body);
    } catch {
      return null;
    }
  }
  if (typeof data?.text_content === 'string') return { prompt: data.text_content };
  return data?.messages || data?.prompt ? data : null;
}

function contentText(content: any): string {
  if (typeof content === 'string') return content;
  if (!Array.isArray(content)) return JSON.stringify(content);
  return content
    .map(part => typeof part?.text === 'string' ? part.text : JSON.stringify(part))
    .join('\n');
}

function formatDiff(changes: Change[]): string {
  return changes.map(change => {
    const prefix = change.added ? '+ ' : change.removed ? '- ' : '  ';
    const lines = change.value.split('\n').filter(Boolean);
    const visible = change.added || change.removed || lines.length <= 6
      ? lines
      : [...lines.slice(0, 3), '...', ...lines.slice(-3)];
    return visible.map(line => `${prefix}${line}`).join('\n');
  }).filter(Boolean).join('\n');
}

function changedLines(changes: Change[], kind: 'added' | 'removed'): number {
  return changes
    .filter(change => Boolean(change[kind]))
    .reduce((count, change) => count + change.value.split('\n').filter(Boolean).length, 0);
}
