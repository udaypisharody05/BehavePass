import {
  CreateSessionPayload,
  SessionResponse,
  SessionSummaryResponse,
  AnalyticsSummaryResponse,
  PredictResponse,
  StaticFeaturesSchema,
  SessionFeaturesSchema,
  KeystrokeFeatureItem,
} from '../types';

const API_BASE = '/api';

function apiErrorMessage(errorData: unknown, fallback: string): string {
  if (!errorData || typeof errorData !== 'object' || !("detail" in errorData)) return fallback;
  const detail = (errorData as { detail?: unknown }).detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => (item && typeof item === 'object' && 'msg' in item ? String(item.msg) : ''))
      .filter(Boolean);
    if (messages.length > 0) return messages.join('; ');
  }
  return fallback;
}

export async function fetchHealth(): Promise<{ status: string; project: string }> {
  const res = await fetch('/health');
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

export async function postSession(payload: CreateSessionPayload): Promise<SessionResponse> {
  const res = await fetch(`${API_BASE}/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Failed to create session' }));
    throw new Error(errorData.detail || 'Failed to submit session');
  }
  return res.json();
}

export async function fetchSessionSummaries(): Promise<SessionSummaryResponse[]> {
  const res = await fetch(`${API_BASE}/sessions`);
  if (!res.ok) throw new Error('Failed to fetch session summaries');
  return res.json();
}

export async function fetchSessionById(sessionId: string): Promise<SessionResponse> {
  const res = await fetch(`${API_BASE}/sessions/${encodeURIComponent(sessionId)}`);
  if (!res.ok) throw new Error('Failed to fetch session details');
  return res.json();
}

export async function fetchAnalyticsSummary(): Promise<AnalyticsSummaryResponse> {
  const res = await fetch(`${API_BASE}/analytics/summary`);
  if (!res.ok) throw new Error('Failed to fetch analytics summary');
  return res.json();
}

export async function requestPrediction(
  static_features: StaticFeaturesSchema,
  session_features: SessionFeaturesSchema,
  keystroke_sequence: KeystrokeFeatureItem[]
): Promise<PredictResponse> {
  const res = await fetch(`${API_BASE}/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ static_features, session_features, keystroke_sequence }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Failed to obtain prediction' }));
    throw new Error(apiErrorMessage(errorData, 'Failed to obtain prediction'));
  }
  return res.json();
}

export async function deleteSessionById(sessionId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete session');
}

export function getCsvExportUrl(): string {
  return `${API_BASE}/export/csv`;
}
