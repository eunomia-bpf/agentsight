// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

'use client';

import { useState, useMemo } from 'react';
import { Event } from '@/types/event';
import { useTranslation } from '@/i18n';

interface ResourceMetrics {
  timestamp: number;
  datetime: Date;
  formattedTime: string;
  pid: number;
  comm: string;
  cpuPercent: number;
  memoryMB: number;
  memoryVszMB: number;
  threads: number;
  children: number;
  cores: number;
  alert: boolean;
}

interface ResourceMetricsViewProps {
  events: Event[];
}

export function ResourceMetricsView({ events }: ResourceMetricsViewProps) {
  const [selectedProcess, setSelectedProcess] = useState<string>('all');
  const [metricType, setMetricType] = useState<'cpu' | 'memory'>('cpu');
  const { t } = useTranslation();

  // Extract system events and convert to metrics
  const metrics = useMemo(() => {
    const systemEvents = events.filter(e => e.source === 'system');

    return systemEvents.map(event => {
      const data = event.data;
      const cpuPercent = parseFloat(data.cpu?.percent || '0');
      const memoryMB = data.memory?.rss_mb || 0;
      const memoryVszMB = data.memory?.vsz_mb || 0;

      const datetime = new Date(event.timestamp); // Timestamp is already in milliseconds since epoch

      return {
        timestamp: event.timestamp,
        datetime,
        formattedTime: datetime.toLocaleTimeString(),
        pid: event.pid,
        comm: event.comm,
        cpuPercent,
        memoryMB,
        memoryVszMB,
        threads: data.process?.threads || 0,
        children: data.process?.children || 0,
        cores: data.cpu?.cores || 0,
        alert: data.alert || false,
      } as ResourceMetrics;
    }).sort((a, b) => a.timestamp - b.timestamp);
  }, [events]);

  // Get unique processes
  const processes = useMemo(() => {
    const processMap = new Map<string, { pid: number; comm: string; count: number }>();

    metrics.forEach(m => {
      const key = `${m.pid}-${m.comm}`;
      const existing = processMap.get(key);
      if (existing) {
        existing.count++;
      } else {
        processMap.set(key, { pid: m.pid, comm: m.comm, count: 1 });
      }
    });

    return Array.from(processMap.entries()).map(([key, value]) => ({
      key,
      ...value
    })).sort((a, b) => b.count - a.count);
  }, [metrics]);

  // Filter metrics by selected process
  const filteredMetrics = useMemo(() => {
    if (selectedProcess === 'all') return metrics;

    const [pid, comm] = selectedProcess.split('-');
    return metrics.filter(m => m.pid === parseInt(pid) && m.comm === comm);
  }, [metrics, selectedProcess]);

  // Calculate statistics
  const stats = useMemo(() => {
    if (filteredMetrics.length === 0) {
      return {
        avgCpu: 0,
        maxCpu: 0,
        avgMemory: 0,
        maxMemory: 0,
        alertCount: 0,
      };
    }

    const cpuValues = filteredMetrics.map(m => m.cpuPercent);
    const memoryValues = filteredMetrics.map(m => m.memoryMB);

    return {
      avgCpu: (cpuValues.reduce((a, b) => a + b, 0) / cpuValues.length).toFixed(2),
      maxCpu: Math.max(...cpuValues).toFixed(2),
      avgMemory: (memoryValues.reduce((a, b) => a + b, 0) / memoryValues.length).toFixed(0),
      maxMemory: Math.max(...memoryValues).toFixed(0),
      alertCount: filteredMetrics.filter(m => m.alert).length,
    };
  }, [filteredMetrics]);

  // Calculate chart dimensions
  const maxValue = metricType === 'cpu'
    ? Math.max(100, ...filteredMetrics.map(m => m.cpuPercent))
    : Math.max(...filteredMetrics.map(m => m.memoryMB)) * 1.1;

  if (metrics.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-8 text-center">
        <p className="text-gray-500">{t('metrics.noData')}</p>
        <p className="text-sm text-gray-400 mt-2">
          {t('metrics.noDataHint')}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="bg-white rounded-lg shadow-md p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">
            {t('metrics.title')}
          </h2>

          <div className="flex items-center space-x-4">
            {/* Metric Type Toggle */}
            <div className="flex rounded-lg border border-gray-200 p-1">
              <button
                onClick={() => setMetricType('cpu')}
                className={`px-3 py-1 text-sm rounded-md transition-colors ${
                  metricType === 'cpu'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                {t('metrics.cpu')}
              </button>
              <button
                onClick={() => setMetricType('memory')}
                className={`px-3 py-1 text-sm rounded-md transition-colors ${
                  metricType === 'memory'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                {t('metrics.memory')}
              </button>
            </div>

            {/* Process Filter */}
            <select
              value={selectedProcess}
              onChange={(e) => setSelectedProcess(e.target.value)}
              className="px-3 py-1 text-sm border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">{t('metrics.allProcesses', { count: metrics.length })}</option>
              {processes.map(p => (
                <option key={p.key} value={p.key}>
                  {t('metrics.processOption', { comm: p.comm, pid: p.pid, count: p.count })}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Statistics */}
        <div className="grid grid-cols-5 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {stats.avgCpu}%
            </div>
            <div className="text-xs text-gray-500">{t('metrics.avgCpu')}</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">
              {stats.maxCpu}%
            </div>
            <div className="text-xs text-gray-500">{t('metrics.peakCpu')}</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {stats.avgMemory} MB
            </div>
            <div className="text-xs text-gray-500">{t('metrics.avgMemory')}</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">
              {stats.maxMemory} MB
            </div>
            <div className="text-xs text-gray-500">{t('metrics.peakMemory')}</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-600">
              {stats.alertCount}
            </div>
            <div className="text-xs text-gray-500">{t('metrics.alerts')}</div>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="space-y-4">
          {/* Chart Header */}
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-gray-900">
              {metricType === 'cpu' ? t('metrics.cpuOverTime') : t('metrics.memoryOverTime')}
            </h3>
            <div className="text-sm text-gray-500">
              {t('metrics.dataPoints', { count: filteredMetrics.length })}
            </div>
          </div>

          {/* Simple Line Chart */}
          <div className="relative h-64 border-l-2 border-b-2 border-gray-300">
            {/* Y-axis labels */}
            <div className="absolute left-0 top-0 bottom-0 w-12 flex flex-col justify-between text-right pr-2 text-xs text-gray-500">
              <div>{maxValue.toFixed(0)}{metricType === 'cpu' ? '%' : ' MB'}</div>
              <div>{(maxValue * 0.75).toFixed(0)}</div>
              <div>{(maxValue * 0.5).toFixed(0)}</div>
              <div>{(maxValue * 0.25).toFixed(0)}</div>
              <div>0</div>
            </div>

            {/* Chart area */}
            <div className="ml-14 h-full relative">
              {/* Grid lines */}
              {[0, 25, 50, 75, 100].map(percent => (
                <div
                  key={percent}
                  className="absolute w-full border-t border-gray-200"
                  style={{ bottom: `${percent}%` }}
                />
              ))}

              {/* Data points and lines */}
              <svg className="absolute inset-0 w-full h-full">
                {filteredMetrics.map((metric, i) => {
                  if (i === 0) return null;

                  const prevMetric = filteredMetrics[i - 1];
                  const value = metricType === 'cpu' ? metric.cpuPercent : metric.memoryMB;
                  const prevValue = metricType === 'cpu' ? prevMetric.cpuPercent : prevMetric.memoryMB;

                  const x1 = ((i - 1) / (filteredMetrics.length - 1)) * 100;
                  const x2 = (i / (filteredMetrics.length - 1)) * 100;
                  const y1 = 100 - (prevValue / maxValue) * 100;
                  const y2 = 100 - (value / maxValue) * 100;

                  return (
                    <line
                      key={i}
                      x1={`${x1}%`}
                      y1={`${y1}%`}
                      x2={`${x2}%`}
                      y2={`${y2}%`}
                      stroke={metric.alert ? '#EF4444' : '#3B82F6'}
                      strokeWidth="2"
                      className="transition-all"
                    />
                  );
                })}

                {/* Data point markers */}
                {filteredMetrics.map((metric, i) => {
                  const value = metricType === 'cpu' ? metric.cpuPercent : metric.memoryMB;
                  const x = (i / (filteredMetrics.length - 1)) * 100;
                  const y = 100 - (value / maxValue) * 100;

                  return (
                    <circle
                      key={`point-${i}`}
                      cx={`${x}%`}
                      cy={`${y}%`}
                      r="3"
                      fill={metric.alert ? '#EF4444' : '#3B82F6'}
                      className="hover:r-5 cursor-pointer transition-all"
                    >
                      <title>{`${metric.formattedTime}: ${value.toFixed(2)}${metricType === 'cpu' ? '%' : ' MB'}`}</title>
                    </circle>
                  );
                })}
              </svg>
            </div>

            {/* X-axis labels */}
            <div className="ml-14 flex justify-between text-xs text-gray-500 mt-2">
              {filteredMetrics.length > 0 && (
                <>
                  <div>{filteredMetrics[0].formattedTime}</div>
                  {filteredMetrics.length > 1 && (
                    <div>{filteredMetrics[filteredMetrics.length - 1].formattedTime}</div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Detailed Table */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">{t('metrics.detailedMetrics')}</h3>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('metrics.table.time')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('metrics.table.process')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('metrics.table.pid')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('metrics.table.cpuPercent')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('metrics.table.memoryRss')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('metrics.table.threads')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('metrics.table.children')}
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredMetrics.slice().reverse().map((metric, i) => (
                <tr key={i} className={metric.alert ? 'bg-red-50' : 'hover:bg-gray-50'}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {metric.formattedTime}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {metric.comm}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {metric.pid}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span className={`font-medium ${
                      metric.cpuPercent > 80 ? 'text-red-600' :
                      metric.cpuPercent > 50 ? 'text-yellow-600' :
                      'text-green-600'
                    }`}>
                      {metric.cpuPercent.toFixed(2)}%
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {metric.memoryMB} MB
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {metric.threads}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {metric.children}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
