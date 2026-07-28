import {
  CreateSessionPayload,
  SessionResponse,
  SessionSummaryResponse,
  AnalyticsSummaryResponse,
  PredictResponse,
  StaticFeaturesSchema,
  SessionFeaturesSchema,
} from '../types';

const API_BASE = '/api';

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

export async function fetchAnalyticsSummary(): Promise<AnalyticsSummaryResponse> {
  const res = await fetch(`${API_BASE}/analytics/summary`);
  if (!res.ok) throw new Error('Failed to fetch analytics summary');
  return res.json();
}

export async function requestPrediction(
  static_features: StaticFeaturesSchema,
  session_features: SessionFeaturesSchema
): Promise<PredictResponse> {
  const res = await fetch(`${API_BASE}/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ static_features, session_features }),
  });
  if (!res.ok) throw new Error('Failed to obtain prototype prediction');
  return res.json();
}

export async function deleteSessionById(sessionId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete session');
}

export function getCsvExportUrl(): string {
  return `${API_BASE}/export/csv`;
}
