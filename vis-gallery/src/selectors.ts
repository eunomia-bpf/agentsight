import type { GalleryData, GalleryEvent, GalleryFile, GallerySession, LinePixel, ViewState } from "./types";

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
