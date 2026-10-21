import React, { useMemo, useState } from 'react';
import { Activity } from 'lucide-react';

import { KeystrokeFeatureItem } from '../types';


interface KeystrokeTimelineProps {
  sequence?: KeystrokeFeatureItem[] | null;
}

type SeriesKey = 'dwell_time' | 'flight_time' | 'press_to_press_latency';

interface SeriesDefinition {
  key: SeriesKey;
  label: string;
  color: string;
}

const SERIES: SeriesDefinition[] = [
  { key: 'dwell_time', label: 'Dwell', color: '#34d399' },
  { key: 'flight_time', label: 'Flight', color: '#60a5fa' },
  { key: 'press_to_press_latency', label: 'Latency', color: '#c084fc' },
];

const HEIGHT = 300;
const MARGIN = { top: 30, right: 28, bottom: 48, left: 58 };

function formatTiming(value: number | null): string {
  return value === null ? 'Not available' : `${value.toFixed(2)} ms`;
}

function eventDescription(event: KeystrokeFeatureItem): string {
  const flags = [event.is_pause ? 'pause' : '', event.is_backspace ? 'backspace' : '']
    .filter(Boolean)
    .join(', ');
  return `Event ${event.sequence_index + 1}: dwell ${formatTiming(event.dwell_time)}, flight ${formatTiming(event.flight_time)}, latency ${formatTiming(event.press_to_press_latency)}${flags ? `, ${flags}` : ''}`;
}

export const KeystrokeTimeline: React.FC<KeystrokeTimelineProps> = ({ sequence }) => {
  const ordered = useMemo(
    () => [...(sequence ?? [])].sort((left, right) => left.sequence_index - right.sequence_index),
    [sequence],
  );
  const [visible, setVisible] = useState<Record<SeriesKey, boolean>>({
    dwell_time: true,
    flight_time: true,
    press_to_press_latency: true,
  });
  const [activeIndex, setActiveIndex] = useState<number | null>(null);

  if (ordered.length === 0) {
    return (
      <section className="mt-6 rounded-lg border border-slate-800 bg-slate-950/60 p-5" aria-labelledby="keystroke-timeline-heading">
        <h3 id="keystroke-timeline-heading" className="flex items-center gap-2 text-sm font-semibold text-slate-200">
          <Activity className="h-4 w-4 text-cyan-400" aria-hidden="true" />
          Keystroke Timing Sequence
        </h3>
        <p className="mt-3 text-xs text-slate-400" role="status">
          No privacy-safe event sequence is available for this session.
        </p>
      </section>
    );
  }

  const enabledSeries = SERIES.filter((series) => visible[series.key]);
  const values = enabledSeries.flatMap((series) =>
    ordered.flatMap((event) => {
      const value = event[series.key];
      return value === null ? [] : [value];
    }),
  );
  const rawMinimum = Math.min(0, ...values);
  const rawMaximum = Math.max(0, ...values);
  const span = Math.max(1, rawMaximum - rawMinimum);
  const minimum = rawMinimum - span * 0.08;
  const maximum = rawMaximum + span * 0.08;
  const chartWidth = Math.max(720, ordered.length * 46 + MARGIN.left + MARGIN.right);
  const plotWidth = chartWidth - MARGIN.left - MARGIN.right;
  const plotHeight = HEIGHT - MARGIN.top - MARGIN.bottom;
  const xFor = (position: number) => (
    MARGIN.left + (ordered.length === 1 ? plotWidth / 2 : (position / (ordered.length - 1)) * plotWidth)
  );
  const yFor = (value: number) => MARGIN.top + ((maximum - value) / (maximum - minimum)) * plotHeight;
  const zeroY = yFor(0);
  const activeEvent = activeIndex === null ? null : ordered[activeIndex] ?? null;

  const pathFor = (key: SeriesKey) => {
    let path = '';
    let continuing = false;
    ordered.forEach((event, position) => {
      const value = event[key];
      if (value === null) {
        continuing = false;
        return;
      }
      path += `${continuing ? ' L' : 'M'} ${xFor(position).toFixed(2)} ${yFor(value).toFixed(2)}`;
      continuing = true;
    });
    return path;
  };

  return (
    <section className="mt-6 rounded-lg border border-slate-800 bg-slate-950/60 p-4 sm:p-5" aria-labelledby="keystroke-timeline-heading">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h3 id="keystroke-timeline-heading" className="flex items-center gap-2 text-sm font-semibold text-slate-200">
            <Activity className="h-4 w-4 text-cyan-400" aria-hidden="true" />
            Keystroke Timing Sequence
          </h3>
          <p className="mt-1 text-xs text-slate-400">
            Ordered privacy-safe events supplied to the behavioral model. No characters or key identities are shown.
          </p>
        </div>
        <fieldset className="flex flex-wrap gap-2" aria-label="Visible timing series">
          <legend className="sr-only">Visible timing series</legend>
          {SERIES.map((series) => (
            <label key={series.key} className="flex cursor-pointer items-center gap-1.5 rounded border border-slate-700 bg-slate-900 px-2.5 py-1.5 text-xs text-slate-300 focus-within:ring-2 focus-within:ring-cyan-500">
              <input
                type="checkbox"
                checked={visible[series.key]}
                onChange={() => setVisible((current) => ({ ...current, [series.key]: !current[series.key] }))}
                className="accent-cyan-500"
              />
              <span className="h-2 w-2 rounded-full" style={{ backgroundColor: series.color }} aria-hidden="true" />
              {series.label}
            </label>
          ))}
        </fieldset>
      </div>

      <div className="mt-4 flex flex-wrap gap-x-4 gap-y-2 text-[11px] text-slate-400" aria-label="Timeline legend">
        {SERIES.map((series) => (
          <span key={series.key} className="flex items-center gap-1.5">
            <span className="h-0.5 w-5" style={{ backgroundColor: series.color }} aria-hidden="true" />
            {series.label} time
          </span>
        ))}
        <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rotate-45 border border-amber-300 bg-amber-400/30" aria-hidden="true" />Pause</span>
        <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 border border-rose-300 bg-rose-400/30" aria-hidden="true" />Backspace</span>
      </div>

      <div className="mt-3 overflow-x-auto rounded-lg border border-slate-800 bg-slate-950" tabIndex={0} aria-label="Scrollable keystroke timeline">
        {enabledSeries.length === 0 ? (
          <div className="flex h-64 items-center justify-center px-4 text-center text-xs text-slate-400">
            Select at least one timing series to display the chart.
          </div>
        ) : (
          <svg
            viewBox={`0 0 ${chartWidth} ${HEIGHT}`}
            width={chartWidth}
            height={HEIGHT}
            role="img"
            aria-label={`Keystroke timing chart with ${ordered.length} ordered events`}
            onMouseLeave={() => setActiveIndex(null)}
          >
            <line x1={MARGIN.left} x2={chartWidth - MARGIN.right} y1={zeroY} y2={zeroY} stroke="#475569" strokeDasharray="4 4" data-axis="zero" />
            <line x1={MARGIN.left} x2={MARGIN.left} y1={MARGIN.top} y2={HEIGHT - MARGIN.bottom} stroke="#334155" />
            <line x1={MARGIN.left} x2={chartWidth - MARGIN.right} y1={HEIGHT - MARGIN.bottom} y2={HEIGHT - MARGIN.bottom} stroke="#334155" />
            <text x={14} y={MARGIN.top + 5} fill="#94a3b8" fontSize="10">{maximum.toFixed(0)} ms</text>
            <text x={18} y={zeroY + 4} fill="#94a3b8" fontSize="10">0 ms</text>
            <text x={10} y={HEIGHT - MARGIN.bottom} fill="#94a3b8" fontSize="10">{minimum.toFixed(0)} ms</text>

            {enabledSeries.map((series) => (
              <path
                key={series.key}
                d={pathFor(series.key)}
                fill="none"
                stroke={series.color}
                strokeWidth="2"
                strokeLinejoin="round"
                strokeLinecap="round"
                data-series={series.key}
              />
            ))}

            {ordered.map((event, position) => {
              const x = xFor(position);
              return (
                <g
                  key={`${event.sequence_index}-${position}`}
                  tabIndex={0}
                  role="img"
                  aria-label={eventDescription(event)}
                  onFocus={() => setActiveIndex(position)}
                  onBlur={() => setActiveIndex(null)}
                  onMouseEnter={() => setActiveIndex(position)}
                  data-event-index={event.sequence_index}
                  className="outline-none focus:[&>rect:first-child]:stroke-cyan-300"
                >
                  <rect x={x - 18} y={MARGIN.top} width="36" height={plotHeight} fill="transparent" stroke="transparent" rx="4" />
                  {enabledSeries.map((series) => {
                    const value = event[series.key];
                    return value === null ? null : (
                      <circle
                        key={series.key}
                        cx={x}
                        cy={yFor(value)}
                        r={activeIndex === position ? 5 : 3.5}
                        fill={series.color}
                        stroke="#020617"
                        strokeWidth="1.5"
                        data-point-series={series.key}
                        data-value={value}
                      />
                    );
                  })}
                  {event.is_pause && (
                    <rect
                      x={x - 4}
                      y={MARGIN.top - 16}
                      width="8"
                      height="8"
                      transform={`rotate(45 ${x} ${MARGIN.top - 12})`}
                      fill="#f59e0b"
                      stroke="#fde68a"
                      data-indicator="pause"
                    />
                  )}
                  {event.is_backspace && (
                    <rect x={x - 4} y={MARGIN.top - 1} width="8" height="8" fill="#fb7185" stroke="#fecdd3" data-indicator="backspace" />
                  )}
                  <text x={x} y={HEIGHT - 24} fill="#94a3b8" fontSize="10" textAnchor="middle">
                    {event.sequence_index + 1}
                  </text>
                </g>
              );
            })}
            <text x={chartWidth / 2} y={HEIGHT - 7} fill="#64748b" fontSize="10" textAnchor="middle">Event number (sequence order)</text>
          </svg>
        )}
      </div>

      <div className="mt-3 min-h-16 rounded-lg border border-slate-800 bg-slate-900 p-3 text-xs" aria-live="polite">
        {activeEvent ? (
          <div>
            <div className="font-semibold text-cyan-300">Event {activeEvent.sequence_index + 1}</div>
            <div className="mt-1 grid grid-cols-1 gap-1 font-mono text-slate-300 sm:grid-cols-3">
              <span>Dwell: {formatTiming(activeEvent.dwell_time)}</span>
              <span>Flight: {formatTiming(activeEvent.flight_time)}</span>
              <span>Latency: {formatTiming(activeEvent.press_to_press_latency)}</span>
            </div>
            {(activeEvent.is_pause || activeEvent.is_backspace) && (
              <div className="mt-2 text-amber-200">
                {[activeEvent.is_pause ? 'Pause event' : '', activeEvent.is_backspace ? 'Backspace event' : ''].filter(Boolean).join(' · ')}
              </div>
            )}
          </div>
        ) : (
          <p className="text-slate-400">Hover over or focus an event to inspect exact timing values.</p>
        )}
      </div>
    </section>
  );
};
