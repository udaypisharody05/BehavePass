import React, { useEffect, useRef, useState } from 'react';
import { GitCompareArrows } from 'lucide-react';

import { fetchSessionById } from '../services/api';
import { SessionResponse, SessionSummaryResponse } from '../types';


interface SessionComparisonProps {
  sessions: SessionSummaryResponse[];
}

interface NumericMetric {
  label: string;
  unit: string;
  value: (session: SessionResponse) => number | null;
  decimals: number;
  showPercentage: boolean;
}

const numericMetrics: NumericMetric[] = [
  { label: 'Password length', unit: 'characters', value: (s) => s.static_features.password_length, decimals: 0, showPercentage: false },
  { label: 'Static zxcvbn Log10', unit: 'log10 guesses', value: (s) => s.static_features.log10_estimated_guesses, decimals: 4, showPercentage: false },
  { label: 'Behavioral/fusion Log10', unit: 'log10 guesses', value: (s) => s.fusion_log10_estimated_guesses ?? null, decimals: 4, showPercentage: false },
  { label: 'Total typing duration', unit: 'ms', value: (s) => s.session_features.total_typing_duration, decimals: 1, showPercentage: true },
  { label: 'Average dwell time', unit: 'ms', value: (s) => s.session_features.average_dwell_time, decimals: 1, showPercentage: true },
  { label: 'Average flight time', unit: 'ms', value: (s) => s.session_features.average_flight_time, decimals: 1, showPercentage: true },
  { label: 'Typing speed', unit: 'characters/s', value: (s) => s.session_features.characters_per_second, decimals: 2, showPercentage: true },
  { label: 'Pause count', unit: '', value: (s) => s.session_features.pause_count, decimals: 0, showPercentage: false },
  { label: 'Backspace count', unit: '', value: (s) => s.session_features.backspace_count, decimals: 0, showPercentage: false },
];

const timingMetrics = numericMetrics.filter((metric) => metric.showPercentage);

export function formatComparisonNumber(value: number | null, decimals: number, unit = ''): string {
  if (value === null) return 'Not available';
  const rendered = value.toFixed(decimals);
  return unit ? `${rendered} ${unit}` : rendered;
}

export function absoluteDifference(first: number | null, second: number | null): number | null {
  return first === null || second === null ? null : Math.abs(second - first);
}

export function percentageDifference(first: number | null, second: number | null): number | null {
  if (first === null || second === null || first === 0) return null;
  return (Math.abs(second - first) / Math.abs(first)) * 100;
}

function sessionLabel(session: SessionSummaryResponse): string {
  return `${session.participant_code} · ${session.condition} · ${session.id.slice(0, 8)}`;
}

function differenceLabel(metric: NumericMetric, first: number | null, second: number | null): string {
  const difference = absoluteDifference(first, second);
  if (difference === null) return 'Not available';
  const absolute = formatComparisonNumber(difference, metric.decimals, metric.unit);
  if (!metric.showPercentage) return `Δ ${absolute}`;
  const percentage = percentageDifference(first, second);
  return percentage === null
    ? `Δ ${absolute}`
    : `Δ ${absolute} (${percentage.toFixed(1)}% vs Session A)`;
}

function summaryDifference(
  label: string,
  first: number | null,
  second: number | null,
  decimals: number,
): string {
  const difference = absoluteDifference(first, second);
  return difference === null
    ? `${label}: Not available`
    : `${label}: ${difference.toFixed(decimals)} log10 guesses`;
}

function majorTimingDifference(first: SessionResponse, second: SessionResponse): string {
  const comparable = timingMetrics
    .map((metric) => {
      const firstValue = metric.value(first);
      const secondValue = metric.value(second);
      return {
        metric,
        firstValue,
        secondValue,
        percentage: percentageDifference(firstValue, secondValue),
      };
    })
    .filter((item) => item.percentage !== null)
    .sort((left, right) => (right.percentage ?? 0) - (left.percentage ?? 0));

  const largest = comparable[0];
  if (!largest) return 'Timing summary: percentage comparison is not available.';
  const difference = absoluteDifference(largest.firstValue, largest.secondValue) ?? 0;
  return `Largest relative timing difference: ${largest.metric.label} differs by ${largest.percentage?.toFixed(1)}% versus Session A (absolute difference ${formatComparisonNumber(difference, largest.metric.decimals, largest.metric.unit)}).`;
}

export const SessionComparison: React.FC<SessionComparisonProps> = ({ sessions }) => {
  const [firstId, setFirstId] = useState('');
  const [secondId, setSecondId] = useState('');
  const [first, setFirst] = useState<SessionResponse | null>(null);
  const [second, setSecond] = useState<SessionResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const sessionCache = useRef(new Map<string, SessionResponse>());

  useEffect(() => {
    if (!firstId || !secondId || firstId === secondId) {
      setFirst(null);
      setSecond(null);
      setError(null);
      setIsLoading(false);
      return;
    }

    let active = true;
    setFirst(null);
    setSecond(null);
    setError(null);
    setIsLoading(true);
    const loadSession = async (sessionId: string) => {
      const cached = sessionCache.current.get(sessionId);
      if (cached) return cached;
      const session = await fetchSessionById(sessionId);
      sessionCache.current.set(sessionId, session);
      return session;
    };

    Promise.all([loadSession(firstId), loadSession(secondId)])
      .then(([firstSession, secondSession]) => {
        if (!active) return;
        setFirst(firstSession);
        setSecond(secondSession);
      })
      .catch((fetchError: unknown) => {
        if (!active) return;
        setError(fetchError instanceof Error ? fetchError.message : 'Failed to load sessions for comparison');
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });

    return () => {
      active = false;
    };
  }, [firstId, secondId]);

  const ready = first !== null && second !== null;

  return (
    <section className="bg-slate-950 border border-slate-800 rounded-xl p-4" aria-labelledby="session-comparison-heading">
      <div className="flex items-start gap-3">
        <GitCompareArrows className="w-5 h-5 text-violet-400 shrink-0 mt-0.5" aria-hidden="true" />
        <div>
          <h3 id="session-comparison-heading" className="text-sm font-semibold text-white">Compare Sessions</h3>
          <p className="text-xs text-slate-400 mt-1">
            Compare two stored sessions. Similar values do not establish that the same password was used.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-4">
        <label className="text-xs text-slate-300">
          Session A
          <select
            aria-label="Session A"
            value={firstId}
            onChange={(event) => setFirstId(event.target.value)}
            className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-violet-500"
          >
            <option value="">Select a session</option>
            {sessions.map((session) => (
              <option key={session.id} value={session.id} disabled={session.id === secondId}>
                {sessionLabel(session)}
              </option>
            ))}
          </select>
        </label>
        <label className="text-xs text-slate-300">
          Session B
          <select
            aria-label="Session B"
            value={secondId}
            onChange={(event) => setSecondId(event.target.value)}
            className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-violet-500"
          >
            <option value="">Select a different session</option>
            {sessions.map((session) => (
              <option key={session.id} value={session.id} disabled={session.id === firstId}>
                {sessionLabel(session)}
              </option>
            ))}
          </select>
        </label>
      </div>

      {sessions.length < 2 && (
        <p className="mt-3 text-xs text-amber-300" role="status">At least two stored sessions are required.</p>
      )}
      {isLoading && <p className="mt-3 text-xs text-slate-400" role="status">Loading comparison…</p>}
      {error && <p className="mt-3 text-xs text-rose-300" role="alert">{error}</p>}

      {ready && (
        <div className="mt-5 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {[
              { name: 'Session A', session: first },
              { name: 'Session B', session: second },
            ].map(({ name, session }) => (
              <div key={name} aria-label={`${name} details`} className="rounded-lg border border-slate-800 bg-slate-900 p-3">
                <div className="text-[10px] uppercase tracking-wider text-slate-500">{name}</div>
                <div className="mt-1 font-mono text-sm font-semibold text-blue-300">{session.participant_code}</div>
                <div className="mt-1 text-xs text-slate-400 break-all">Session {session.id}</div>
                <div className="mt-2 flex flex-wrap gap-2 text-xs">
                  <span className="rounded bg-slate-800 px-2 py-1 text-slate-300">{session.condition}</span>
                  <span className={`rounded px-2 py-1 ${session.is_valid ? 'bg-emerald-500/10 text-emerald-300' : 'bg-rose-500/10 text-rose-300'}`}>
                    {session.is_valid ? 'Valid' : 'Flagged'}
                  </span>
                </div>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
            {numericMetrics.map((metric) => {
              const firstValue = metric.value(first);
              const secondValue = metric.value(second);
              return (
                <div key={metric.label} className="rounded-lg border border-slate-800 bg-slate-900/70 p-3">
                  <div className="text-xs font-semibold text-slate-300">{metric.label}</div>
                  <div className="mt-2 grid grid-cols-2 gap-3 font-mono text-sm">
                    <div><span className="block text-[10px] text-slate-500">Session A</span>{formatComparisonNumber(firstValue, metric.decimals, metric.unit)}</div>
                    <div><span className="block text-[10px] text-slate-500">Session B</span>{formatComparisonNumber(secondValue, metric.decimals, metric.unit)}</div>
                  </div>
                  <div className="mt-2 text-[11px] text-violet-300">{differenceLabel(metric, firstValue, secondValue)}</div>
                </div>
              );
            })}
          </div>

          <div className="rounded-lg border border-violet-500/20 bg-violet-500/5 p-4" aria-live="polite">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-violet-300">Comparison summary</h4>
            <ul className="mt-2 space-y-1 text-xs text-slate-300">
              <li>{summaryDifference('Static estimate difference', first.static_features.log10_estimated_guesses, second.static_features.log10_estimated_guesses, 4)}</li>
              <li>{summaryDifference('Fusion estimate difference', first.fusion_log10_estimated_guesses ?? null, second.fusion_log10_estimated_guesses ?? null, 4)}</li>
              <li>{majorTimingDifference(first, second)}</li>
            </ul>
          </div>
        </div>
      )}
    </section>
  );
};
