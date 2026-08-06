// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

'use client';

import type { ReactNode } from 'react';
import { ArrowRightIcon } from '@heroicons/react/24/solid';

// Shared chrome for dashboard panels. Extends the existing card language
// (bg-white rounded-lg shadow-md, border-gray-200) used across Timeline /
// Process Tree / Metrics so the dashboard reads as the same surface.
export interface DashboardPanelProps {
  title: string;
  subtitle?: string;
  // Right-aligned actions (usually a drill-down link into a detail view).
  action?: ReactNode;
  className?: string;
  bodyClassName?: string;
  children: ReactNode;
}

export function DashboardPanel({
  title,
  subtitle,
  action,
  className = '',
  bodyClassName = '',
  children,
}: DashboardPanelProps) {
  return (
    <section className={`flex flex-col rounded-lg border border-gray-200 bg-white shadow-md ${className}`}>
      <header className="flex items-start justify-between gap-3 border-b border-gray-100 px-4 py-3">
        <div className="min-w-0">
          <h3 className="truncate text-sm font-semibold text-gray-900">{title}</h3>
          {subtitle && <p className="mt-0.5 truncate text-xs text-gray-500">{subtitle}</p>}
        </div>
        {action && <div className="shrink-0">{action}</div>}
      </header>
      <div className={`px-4 py-3 ${bodyClassName}`}>{children}</div>
    </section>
  );
}

// Drill-down link into an existing detail view. The dashboard chooses the
// session; the detail views inspect it.
export function PanelDrillLink({
  label,
  onClick,
}: {
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-blue-700 transition-colors hover:bg-blue-50"
    >
      {label}
      <ArrowRightIcon className="h-3 w-3" />
    </button>
  );
}

export type Severity = 'critical' | 'warning' | 'info' | 'good';

const SEVERITY_CLASSES: Record<Severity, string> = {
  critical: 'bg-red-50 text-red-700 ring-red-200',
  warning: 'bg-amber-50 text-amber-700 ring-amber-200',
  info: 'bg-blue-50 text-blue-700 ring-blue-200',
  good: 'bg-green-50 text-green-700 ring-green-200',
};

export function SeverityBadge({ severity, children }: { severity: Severity; children: ReactNode }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium ring-1 ring-inset ${SEVERITY_CLASSES[severity]}`}
    >
      {children}
    </span>
  );
}

export interface KpiTileProps {
  label: string;
  value: string;
  hint?: string;
  // semantic tone for state-aware tiles (e.g. failures). Keep reserved for state.
  tone?: 'default' | 'critical' | 'warning';
}

export function KpiTile({ label, value, hint, tone = 'default' }: KpiTileProps) {
  const valueColor =
    tone === 'critical'
      ? 'text-red-600'
      : tone === 'warning'
        ? 'text-amber-600'
        : 'text-gray-900';
  return (
    <div className="min-w-0 rounded-md border border-gray-100 bg-gray-50/60 px-3 py-2">
      <div
        className={`truncate text-lg font-semibold leading-tight ${valueColor}`}
        style={{ fontVariantNumeric: 'tabular-nums' }}
        title={value}
      >
        {value}
      </div>
      <div className="mt-0.5 truncate text-[11px] uppercase tracking-wide text-gray-500" title={label}>
        {label}
      </div>
      {hint && <div className="truncate text-[11px] text-gray-400" title={hint}>{hint}</div>}
    </div>
  );
}

export function EmptyState({ message, hint }: { message: string; hint?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-8 text-center">
      <p className="text-sm text-gray-500">{message}</p>
      {hint && <p className="mt-1 text-xs text-gray-400">{hint}</p>}
    </div>
  );
}

// A list row with a leading swatch + trailing count. Used for "top N" tables.
export interface RankedRowProps {
  rank?: number;
  swatch?: string;
  label: string;
  sublabel?: string;
  count?: number;
  countLabel?: string;
}

export function RankedRow({ rank, swatch, label, sublabel, count, countLabel }: RankedRowProps) {
  return (
    <li className="flex items-center gap-2 py-1">
      {rank != null && (
        <span className="w-4 shrink-0 text-right text-[11px] tabular-nums text-gray-400">{rank}</span>
      )}
      {swatch && <span className="h-2.5 w-2.5 shrink-0 rounded-sm" style={{ background: swatch }} />}
      <div className="min-w-0 flex-1">
        <div className="truncate text-xs font-medium text-gray-800" title={label}>
          {label}
        </div>
        {sublabel && (
          <div className="truncate text-[11px] text-gray-400" title={sublabel}>
            {sublabel}
          </div>
        )}
      </div>
      {count != null && (
        <div className="shrink-0 text-right">
          <div className="text-xs font-semibold tabular-nums text-gray-900">{count}</div>
          {countLabel && <div className="text-[10px] text-gray-400">{countLabel}</div>}
        </div>
      )}
    </li>
  );
}
