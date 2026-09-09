import { describe, it, expect } from 'vitest';
import {
  computeSessionFeatures,
  isCapturedPasswordKey,
  RawKeyRecord,
} from './keystrokeFeatures';

describe('keystrokeFeatures comprehensive timing tests', () => {
  it('captures password characters and backspaces but excludes control keys', () => {
    expect(isCapturedPasswordKey('a')).toBe(true);
    expect(isCapturedPasswordKey('!')).toBe(true);
    expect(isCapturedPasswordKey('Backspace')).toBe(true);
    expect(isCapturedPasswordKey('Shift')).toBe(false);
    expect(isCapturedPasswordKey('Control')).toBe(false);
    expect(isCapturedPasswordKey('ArrowLeft')).toBe(false);
  });

  it('represents undefined first-event flight_time and press_to_press_latency as null', () => {
    const records: RawKeyRecord[] = [
      { keyId: 'k1', isBackspace: false, keydownTimestamp: 1000, keyupTimestamp: 1080 },
    ];

    const { sequence, sessionFeatures } = computeSessionFeatures(records, 500.0, 1);
    expect(sequence.length).toBe(1);
    expect(sequence[0].dwell_time).toBe(80);
    expect(sequence[0].flight_time).toBeNull();
    expect(sequence[0].press_to_press_latency).toBeNull();
    expect(sessionFeatures.average_dwell_time).toBe(80);
  });

  it('calculates dwell time and flight time accurately for sequential keypresses', () => {
    const records: RawKeyRecord[] = [
      { keyId: 'k1', isBackspace: false, keydownTimestamp: 1000, keyupTimestamp: 1100 }, // Dwell = 100ms
      { keyId: 'k2', isBackspace: false, keydownTimestamp: 1250, keyupTimestamp: 1350 }, // Dwell = 100ms, Flight = 150ms, Latency = 250ms
    ];

    const { sequence, sessionFeatures } = computeSessionFeatures(records, 500.0, 2);
    expect(sequence[1].dwell_time).toBe(100);
    expect(sequence[1].flight_time).toBe(150);
    expect(sequence[1].press_to_press_latency).toBe(250);
    expect(sessionFeatures.total_typing_duration).toBe(350);
  });

  it('allows negative flight times for overlapping keypresses', () => {
    const records: RawKeyRecord[] = [
      { keyId: 'k1', isBackspace: false, keydownTimestamp: 1000, keyupTimestamp: 1150 },
      { keyId: 'k2', isBackspace: false, keydownTimestamp: 1100, keyupTimestamp: 1200 }, // Pressed before k1 keyup! Flight = 1100 - 1150 = -50ms
    ];

    const { sequence } = computeSessionFeatures(records, 500.0, 2);
    expect(sequence[1].flight_time).toBe(-50);
  });

  it('uses press-to-press latency for pause detection', () => {
    const records: RawKeyRecord[] = [
      { keyId: 'k1', isBackspace: false, keydownTimestamp: 1000, keyupTimestamp: 1100 },
      { keyId: 'k2', isBackspace: false, keydownTimestamp: 1600, keyupTimestamp: 1700 }, // Latency = 600ms >= 500ms
    ];

    const { sequence, sessionFeatures } = computeSessionFeatures(records, 500.0, 2);
    expect(sequence[1].press_to_press_latency).toBe(600);
    expect(sequence[1].is_pause).toBe(true);
    expect(sessionFeatures.pause_count).toBe(1);
    expect(sessionFeatures.total_pause_duration).toBe(600);
  });

  it('correctly tracks backspace count and correction bursts', () => {
    const records: RawKeyRecord[] = [
      { keyId: 'k1', isBackspace: false, keydownTimestamp: 1000, keyupTimestamp: 1050 },
      { keyId: 'k2', isBackspace: true, keydownTimestamp: 1100, keyupTimestamp: 1150 },
      { keyId: 'k3', isBackspace: true, keydownTimestamp: 1200, keyupTimestamp: 1250 },
      { keyId: 'k4', isBackspace: false, keydownTimestamp: 1300, keyupTimestamp: 1350 },
    ];

    const { sessionFeatures } = computeSessionFeatures(records, 500.0, 2);
    expect(sessionFeatures.backspace_count).toBe(2);
    expect(sessionFeatures.correction_burst_count).toBe(1);
  });
});
