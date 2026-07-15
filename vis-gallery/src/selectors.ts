import type { GalleryData, GalleryEvent, GalleryFile, GallerySession, GraphEdge, LinePixel, TimeBucket, ViewState } from "./types";

export function eventVisible(event: GalleryEvent, state: ViewState): boolean {
  return (
    event.ts_ms >= state.rangeStartMs &&
    event.ts_ms <= Math.min(state.cursorMs, state.rangeEndMs) &&
    (state.vendors.size === 0 || state.vendors.has(event.vendor)) &&
    (state.associationStates.size === 0 ||
      state.associationStates.has(event.association_state)) &&
    (!state.selectedPath || event.path === state.selectedPath) &&
    (!state.selectedSession || event.session_id === state.selectedSession)
  );
}

export function visibleEvents(data: GalleryData, state: ViewState): GalleryEvent[] {
  return data.events.filter((event) => eventVisible(event, state));
}

export function activeFiles(events: GalleryEvent[], files: GalleryFile[]): GalleryFile[] {
  const paths = new Set(events.map((event) => event.path));
  return files.filter(
    (file) => paths.has(file.path) || paths.has(file.current_path ?? ""),
  );
}

export function completedSessionsInVisibleInterval(
  sessions: GallerySession[],
  events: GalleryEvent[],
  state: ViewState,
): GallerySession[] {
  const activeSessionIds = new Set(events.map((event) => event.session_id));
  const visibleEnd = Math.min(state.cursorMs, state.rangeEndMs);
  return sessions.filter(
    (session) =>
      activeSessionIds.has(session.id) &&
      session.started_at_ms !== null &&
      session.ended_at_ms !== null &&
      session.started_at_ms >= state.rangeStartMs &&
      session.ended_at_ms <= visibleEnd,
  );
}

export function linePixelVisible(pixel: LinePixel, cursorMs: number): boolean {
  return pixel.origin_ms <= cursorMs;
}

export function projectOrderedEdges(events: GalleryEvent[]): GraphEdge[] {
  const groups = new Map<string, GalleryEvent[]>();
  events.forEach((event) => {
    const key = `${event.session_id}:${event.prompt_index}`;
    groups.set(key, [...(groups.get(key) ?? []), event]);
  });
  const edges = new Map<string, GraphEdge>();
  groups.forEach((rows) => {
    let reads: string[] = [];
    [...rows].sort((a, b) => a.ts_ms - b.ts_ms || a.id.localeCompare(b.id)).forEach((row) => {
      if (row.effect === "read") {
        if (!reads.includes(row.path)) reads.push(row.path);
        reads = reads.slice(-8);
      } else if (row.effect === "write") {
        reads.forEach((source) => {
          if (source === row.path) return;
          const key = `${source}\u0000${row.path}`;
          const current = edges.get(key) ?? { source, target: row.path, count: 0, vendors: {}, semantics: "ordered read-before-write evidence; not causality" };
          current.count += 1;
          current.vendors![row.vendor] = (current.vendors![row.vendor] ?? 0) + 1;
          edges.set(key, current);
        });
        reads = [];
      }
    });
  });
  return [...edges.values()].sort((a, b) => b.count - a.count || a.source.localeCompare(b.source) || a.target.localeCompare(b.target)).slice(0, 400);
}

export function projectTimeBuckets(events: GalleryEvent[]): TimeBucket[] {
  const buckets = new Map<number, TimeBucket>();
  events.forEach((event) => {
    const ts_ms = Math.floor(event.ts_ms / 3_600_000) * 3_600_000;
    const row = buckets.get(ts_ms) ?? { ts_ms };
    row.events = (row.events ?? 0) + 1;
    const effect = event.effect as keyof Omit<TimeBucket, "ts_ms">;
    if (["read", "write", "test", "process", "network", "repo"].includes(effect)) {
      row[effect] = (row[effect] ?? 0) + 1;
    }
    buckets.set(ts_ms, row);
  });
  return [...buckets.values()].sort((a, b) => a.ts_ms - b.ts_ms);
}

export function formatCompact(value: number): string {
  return new Intl.NumberFormat("en", {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);
}

export function formatTime(timestampMs: number): string {
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "UTC",
  }).format(timestampMs);
}

export function topBy<T>(values: T[], score: (value: T) => number, limit: number): T[] {
  return [...values].sort((a, b) => score(b) - score(a)).slice(0, limit);
}
