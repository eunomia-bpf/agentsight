export interface AgentFlameSvgFrame {
  id: string;
  name: string;
  kind: string;
  path: string[];
  value: number;
  metric: string;
  totalPct: number;
  x: number;
  y: number;
  width: number;
  height: number;
  depth: number;
}

export interface AgentFlameSvgProfile {
  title: string;
  metric: string;
  total: number;
  hiddenTiny: number;
  frames: AgentFlameSvgFrame[];
}

function decodeXml(value: string): string {
  return value
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&amp;/g, '&');
}

function stripMarkup(value: string): string {
  return decodeXml(value.replace(/<[^>]*>/g, '')).trim();
}

function attribute(tag: string, name: string): string | undefined {
  const match = tag.match(new RegExp(`\\b${name}=(['"])(.*?)\\1`, 'i'));
  return match?.[2];
}

function numberAttribute(tag: string, name: string): number | null {
  const value = Number(attribute(tag, name));
  return Number.isFinite(value) ? value : null;
}

export function parseAgentFlameFrameTitle(title: string): Omit<AgentFlameSvgFrame, 'id' | 'x' | 'y' | 'width' | 'height' | 'depth'> | null {
  const match = title.match(/^([\s\S]+?)\s*\n\s*([\d,]+)(?:\s+([^\n(]+?))?\s*\(([\d.]+)%\)$/)
    ?? title.match(/^(.+) \| ([\d,]+)\s+(.+?) \| ([\d.]+)%$/)
    ?? title.match(/^(.+) \| ([\d,]+)\s+(.+?) \(([\d.]+)%\)$/);
  if (!match) return null;

  const path = match[1].split(/\s*;\s*/).filter(Boolean);
  const value = Number(match[2].replace(/,/g, ''));
  const totalPct = Number(match[4]);
  if (!Number.isFinite(value) || !Number.isFinite(totalPct)) return null;

  const name = path[path.length - 1];
  return {
    name,
    kind: name.includes(':') ? name.split(':', 1)[0] : 'value',
    path,
    value,
    metric: match[3]?.trim() || 'count',
    totalPct,
  };
}

export function parseAgentFlameSvg(source: string): AgentFlameSvgProfile | null {
  const titleMatch = source.match(/<text\b[^>]*class=(['"])title\1[^>]*>([\s\S]*?)<\/text>/i);
  const metaMatch = source.match(/<text\b[^>]*class=(['"])meta\1[^>]*>([\s\S]*?)<\/text>/i);
  const meta = metaMatch ? stripMarkup(metaMatch[2]) : '';
  const total = Number(meta.match(/\btotal\s*=\s*([\d,]+)/i)?.[1]?.replace(/,/g, '') ?? 0);
  const hiddenTiny = Number(meta.match(/\bhidden tiny nodes\s*=\s*([\d,]+)/i)?.[1]?.replace(/,/g, '') ?? 0);
  let frames: AgentFlameSvgFrame[] = [];
  const groupPattern = /<g\b[^>]*>([\s\S]*?)<\/g>/gi;

  let match: RegExpExecArray | null;
  while ((match = groupPattern.exec(source)) !== null) {
    const group = match[1];
    const frameTitleMatch = group.match(/<title\b[^>]*>([\s\S]*?)<\/title>/i);
    const rectMatch = group.match(/<rect\b[^>]*>/i);
    if (!frameTitleMatch || !rectMatch) continue;

    const parsed = parseAgentFlameFrameTitle(stripMarkup(frameTitleMatch[1]));
    const x = numberAttribute(rectMatch[0], 'x');
    const y = numberAttribute(rectMatch[0], 'y');
    const width = numberAttribute(rectMatch[0], 'width');
    const height = numberAttribute(rectMatch[0], 'height');
    if (!parsed || x === null || y === null || width === null || height === null) continue;

    frames.push({
      ...parsed,
      id: parsed.path.join('\u0000'),
      x,
      y,
      width,
      height,
      depth: parsed.path.length - 1,
    });
  }

  const legacyPattern = /<rect\b([^>]*)>\s*<title\b[^>]*>([\s\S]*?)<\/title>\s*<\/rect>/gi;
  while ((match = legacyPattern.exec(source)) !== null) {
    const rectTag = `<rect ${match[1]}>`;
    const parsed = parseAgentFlameFrameTitle(stripMarkup(match[2]));
    const x = numberAttribute(rectTag, 'x');
    const y = numberAttribute(rectTag, 'y');
    const width = numberAttribute(rectTag, 'width');
    const height = numberAttribute(rectTag, 'height');
    if (!parsed || x === null || y === null || width === null || height === null) continue;
    frames.push({
      ...parsed,
      id: parsed.path.join('\u0000'),
      x,
      y,
      width,
      height,
      depth: 0,
    });
  }

  if (frames.length === 0) return null;
  if (frames.every(frame => frame.path.length === 1)) {
    const root = [...frames].sort((left, right) => right.width - left.width || left.y - right.y)[0];
    const contained = frames.filter(frame => frame !== root && (
      frame.x >= root.x - 0.1 && frame.x + frame.width <= root.x + root.width + 0.1
    ));
    const direction = contained.filter(frame => frame.y > root.y).length
      >= contained.filter(frame => frame.y < root.y).length ? 1 : -1;
    const ordered = [...frames].sort((left, right) => (
      direction * (left.y - right.y) || left.x - right.x || right.width - left.width
    ));
    const completed: AgentFlameSvgFrame[] = [];
    for (const frame of ordered) {
      const parent = completed
        .filter(candidate => direction * (frame.y - candidate.y) > 0)
        .filter(candidate => (
          frame.x >= candidate.x - 0.1
          && frame.x + frame.width <= candidate.x + candidate.width + 0.1
        ))
        .sort((left, right) => (
          Math.abs(frame.y - left.y) - Math.abs(frame.y - right.y)
          || left.width - right.width
        ))[0];
      frame.path = parent ? [...parent.path, frame.name] : [frame.name];
      frame.id = frame.path.join('\u0000');
      frame.depth = frame.path.length - 1;
      completed.push(frame);
    }
    frames = completed;
  }
  return {
    title: titleMatch ? stripMarkup(titleMatch[2]) : 'Agent profile',
    metric: frames[0].metric,
    total: Number.isFinite(total) && total > 0 ? total : Math.max(...frames.map(frame => frame.value)),
    hiddenTiny: Number.isFinite(hiddenTiny) ? hiddenTiny : 0,
    frames,
  };
}

export function isFrameDescendant(frame: AgentFlameSvgFrame, ancestor: AgentFlameSvgFrame): boolean {
  return frame.path.length >= ancestor.path.length
    && ancestor.path.every((part, index) => frame.path[index] === part);
}

export function directFrameChildren(
  frames: AgentFlameSvgFrame[],
  parent: AgentFlameSvgFrame,
): AgentFlameSvgFrame[] {
  return frames
    .filter(frame => frame.path.length === parent.path.length + 1 && isFrameDescendant(frame, parent))
    .sort((left, right) => right.value - left.value || left.name.localeCompare(right.name));
}

export function disjointMatchValue(
  frames: AgentFlameSvgFrame[],
  matches: Set<string>,
): number {
  return frames
    .filter(frame => matches.has(frame.id))
    .filter(frame => !frame.path.slice(0, -1).some((_, index) => (
      matches.has(frame.path.slice(0, index + 1).join('\u0000'))
    )))
    .reduce((sum, frame) => sum + frame.value, 0);
}
