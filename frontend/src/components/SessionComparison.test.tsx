import React, { act } from 'react';
import { createRoot, Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { SessionResponse, SessionSummaryResponse } from '../types';
import {
  absoluteDifference,
  formatComparisonNumber,
  percentageDifference,
  SessionComparison,
} from './SessionComparison';

const mocks = vi.hoisted(() => ({ fetchSessionById: vi.fn() }));

vi.mock('../services/api', () => ({ fetchSessionById: mocks.fetchSessionById }));

function detail(id: string, participant: string, overrides: Partial<SessionResponse> = {}): SessionResponse {
  return {
    id,
    participant_id: Number(id.slice(-1)),
    participant_code: participant,
    task_id: 'TASK-01',
    task_type: 'creation',
    attempt_number: 1,
    condition: 'untimed',
    timed_limit_ms: null,
    completed_within_limit: null,
    timed_out: false,
    pause_threshold_ms: 500,
    collector_version: '1.0.0',
    feature_schema_version: '1.0.0',
    consent_version: '1.0.0',
    is_valid: true,
    invalid_reason: null,
    device_type: 'desktop',
    behavioural_model_status: 'ready_synthetic_proof_of_concept',
    fusion_log10_estimated_guesses: 14.148052626142771,
    created_at: '2026-10-20T10:00:00Z',
    static_features: {
      password_length: 12,
      lowercase_count: 6,
      uppercase_count: 2,
      digit_count: 2,
      symbol_count: 2,
      unique_character_count: 12,
      repeated_character_count: 0,
      repeated_substring_count: 0,
      sequential_character_count: 0,
      zxcvbn_score: 4,
      log10_estimated_guesses: 12.477,
      empirical_character_entropy: 3.5,
      character_pool_entropy_estimate: 78,
    },
    session_features: {
      total_typing_duration: 1000,
      total_key_presses: 12,
      average_dwell_time: 80,
      dwell_time_std: 10,
      average_flight_time: 60,
      flight_time_std: 15,
      average_press_latency: 140,
      longest_interkey_delay: 300,
      pause_count: 1,
      total_pause_duration: 500,
      backspace_count: 0,
      backspace_rate: 0,
      correction_burst_count: 0,
      characters_per_second: 12,
    },
    keystroke_sequence: [],
    ...overrides,
  };
}

const details: Record<string, SessionResponse> = {
  'session-1': detail('session-1', 'PART-A'),
  'session-2': detail('session-2', 'PART-B', {
    condition: 'timed',
    fusion_log10_estimated_guesses: 14.03227001057665,
    session_features: {
      ...detail('session-2', 'PART-B').session_features,
      total_typing_duration: 1500,
      average_dwell_time: 100,
      average_flight_time: 90,
      characters_per_second: 8,
      pause_count: 2,
      backspace_count: 1,
    },
  }),
  'session-3': detail('session-3', 'PART-C', {
    fusion_log10_estimated_guesses: null,
  }),
};

const summaries: SessionSummaryResponse[] = Object.values(details).map((session) => ({
  id: session.id,
  participant_code: session.participant_code,
  task_id: session.task_id,
  condition: session.condition,
  completed_within_limit: session.completed_within_limit,
  timed_out: session.timed_out,
  is_valid: session.is_valid,
  password_length: session.static_features.password_length,
  zxcvbn_score: session.static_features.zxcvbn_score,
  log10_estimated_guesses: session.static_features.log10_estimated_guesses,
  behavioural_model_status: session.behavioural_model_status ?? null,
  fusion_log10_estimated_guesses: session.fusion_log10_estimated_guesses ?? null,
  total_typing_duration: session.session_features.total_typing_duration,
  pause_count: session.session_features.pause_count,
  backspace_count: session.session_features.backspace_count,
  created_at: session.created_at,
}));

describe('SessionComparison', () => {
  let container: HTMLDivElement;
  let root: Root;

  beforeEach(() => {
    (globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT: boolean })
      .IS_REACT_ACT_ENVIRONMENT = true;
    mocks.fetchSessionById.mockReset().mockImplementation((id: string) => Promise.resolve(details[id]));
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
    act(() => root.render(<SessionComparison sessions={summaries} />));
  });

  afterEach(() => {
    act(() => root.unmount());
    container.remove();
  });

  async function select(label: string, value: string) {
    const element = container.querySelector(`select[aria-label="${label}"]`) as HTMLSelectElement;
    await act(async () => {
      element.value = value;
      element.dispatchEvent(new Event('change', { bubbles: true }));
      await Promise.resolve();
    });
  }

  it('selects two distinct sessions and displays stored values and differences', async () => {
    await select('Session A', 'session-1');
    const secondSelect = container.querySelector('select[aria-label="Session B"]') as HTMLSelectElement;
    expect((secondSelect.querySelector('option[value="session-1"]') as HTMLOptionElement).disabled).toBe(true);

    await select('Session B', 'session-2');

    expect(mocks.fetchSessionById).toHaveBeenCalledWith('session-1');
    expect(mocks.fetchSessionById).toHaveBeenCalledWith('session-2');
    expect(container.textContent).toContain('14.1481 log10 guesses');
    expect(container.textContent).toContain('14.0323 log10 guesses');
    expect(container.textContent).toContain('Δ 500.0 ms (50.0% vs Session A)');
    expect(container.textContent).toContain('Static estimate difference: 0.0000 log10 guesses');
    expect(container.textContent).toContain('Fusion estimate difference: 0.1158 log10 guesses');
  });

  it('shows Not available for a null behavioral prediction', async () => {
    await select('Session A', 'session-1');
    await select('Session B', 'session-3');

    expect(container.textContent).toContain('Fusion estimate difference: Not available');
    expect(container.textContent).toContain('Not available');
  });

  it('reloads details when a selection changes', async () => {
    await select('Session A', 'session-1');
    await select('Session B', 'session-2');
    await select('Session B', 'session-3');

    expect(mocks.fetchSessionById).toHaveBeenLastCalledWith('session-3');
    expect(mocks.fetchSessionById.mock.calls.filter(([id]) => id === 'session-1')).toHaveLength(1);
    expect(container.querySelector('[aria-label="Session B details"]')?.textContent).toContain('PART-C');
  });
});

describe('session comparison numeric helpers', () => {
  it('formats numeric and unavailable values consistently', () => {
    expect(formatComparisonNumber(14.148052626142771, 4, 'log10 guesses')).toBe('14.1481 log10 guesses');
    expect(formatComparisonNumber(null, 4)).toBe('Not available');
    expect(absoluteDifference(10, 14)).toBe(4);
    expect(percentageDifference(10, 14)).toBe(40);
    expect(percentageDifference(0, 14)).toBeNull();
  });
});
