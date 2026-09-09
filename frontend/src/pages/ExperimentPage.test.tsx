import React, { act } from 'react';
import { createRoot, Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { CreateSessionPayload, PredictResponse } from '../types';
import { ExperimentPage } from './ExperimentPage';

const mocks = vi.hoisted(() => ({
  postSession: vi.fn(),
  requestPrediction: vi.fn(),
}));

const payload: CreateSessionPayload = {
  participant_code: 'PART-TEST',
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
  static_features: {
    password_length: 1, lowercase_count: 1, uppercase_count: 0,
    digit_count: 0, symbol_count: 0, unique_character_count: 1,
    repeated_character_count: 0, repeated_substring_count: 0,
    sequential_character_count: 0, zxcvbn_score: 0,
    log10_estimated_guesses: 1, empirical_character_entropy: 0,
    character_pool_entropy_estimate: 4.7,
  },
  session_features: {
    total_typing_duration: 80, total_key_presses: 1, average_dwell_time: 80,
    dwell_time_std: 0, average_flight_time: 0, flight_time_std: 0,
    average_press_latency: 0, longest_interkey_delay: 0, pause_count: 0,
    total_pause_duration: 0, backspace_count: 0, backspace_rate: 0,
    correction_burst_count: 0, characters_per_second: 12.5,
  },
  keystroke_sequence: [{
    sequence_index: 0, dwell_time: 80, flight_time: null,
    press_to_press_latency: null, is_backspace: false, is_pause: false,
  }],
};

vi.mock('../services/api', () => ({
  postSession: mocks.postSession,
  requestPrediction: mocks.requestPrediction,
}));

vi.mock('../hooks/useKeystrokeCollector', () => ({
  useKeystrokeCollector: () => ({
    passwordValue: 'x', isValid: true, invalidReason: null, recordsCount: 1,
    attemptNumber: 1, handleKeyDown: vi.fn(), handleKeyUp: vi.fn(),
    handlePaste: vi.fn(), handleBlur: vi.fn(), handleChange: vi.fn(),
    markIntentionalControlInteraction: vi.fn(), resetSession: vi.fn(),
    prepareSessionPayload: () => payload,
  }),
}));

vi.mock('../components/ParticipantHeader', () => ({ ParticipantHeader: () => null }));
vi.mock('../components/PrivacyDisclaimer', () => ({ PrivacyDisclaimer: () => null }));
vi.mock('../components/BehaviouralFeedbackCard', () => ({ BehaviouralFeedbackCard: () => null }));
vi.mock('../components/AnalyticsModal', () => ({ AnalyticsModal: () => null }));
vi.mock('../components/PasswordTaskCard', () => ({
  PasswordTaskCard: ({ onSubmit }: { onSubmit: () => void }) => (
    <button onClick={onSubmit}>Submit</button>
  ),
}));

describe('ExperimentPage behavioral persistence', () => {
  let container: HTMLDivElement;
  let root: Root;

  beforeEach(() => {
    (globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT: boolean })
      .IS_REACT_ACT_ENVIRONMENT = true;
    mocks.postSession.mockReset().mockResolvedValue({});
    mocks.requestPrediction.mockReset();
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
  });

  afterEach(() => {
    act(() => root.unmount());
    container.remove();
  });

  it.each([
    ['ready_synthetic_proof_of_concept', 7.125],
    ['model_unavailable', null],
  ] as const)('persists %s prediction outcome with the session', async (status, estimate) => {
    const prediction: PredictResponse = {
      static_strength_tier: 'Very Weak', zxcvbn_score: 0,
      log10_estimated_guesses: 1, behavioural_summary: [],
      behavioural_model_status: status,
      fusion_log10_estimated_guesses: estimate,
      model_used: 'test', model_type: 'BiLSTM + MLP fusion',
      target: 'log10 estimated guesses', warnings: [],
    };
    mocks.requestPrediction.mockResolvedValue(prediction);

    await act(async () => root.render(<ExperimentPage />));
    await act(async () => {
      (container.querySelector('button') as HTMLButtonElement).click();
    });

    expect(mocks.requestPrediction).toHaveBeenCalledOnce();
    expect(mocks.postSession).toHaveBeenCalledWith({
      ...payload,
      behavioural_model_status: status,
      fusion_log10_estimated_guesses: estimate,
    });
    expect(mocks.requestPrediction.mock.invocationCallOrder[0])
      .toBeLessThan(mocks.postSession.mock.invocationCallOrder[0]);
  });
});
