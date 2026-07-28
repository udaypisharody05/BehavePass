import { KeystrokeFeatureItem, SessionFeaturesSchema } from '../types';

export interface RawKeyRecord {
  keyId: string; // Internal opaque identifier for event matching, NOT saved
  isBackspace: boolean;
  keydownTimestamp: number;
  keyupTimestamp: number | null;
}

export function computeSessionFeatures(
  completedRecords: RawKeyRecord[],
  pauseThresholdMs: number = 500.0,
  finalLength: number = 0
): {
  sequence: KeystrokeFeatureItem[];
  sessionFeatures: SessionFeaturesSchema;
} {
  if (completedRecords.length === 0) {
    const emptySession: SessionFeaturesSchema = {
      total_typing_duration: 0,
      total_key_presses: 0,
      average_dwell_time: 0,
      dwell_time_std: 0,
      average_flight_time: 0,
      flight_time_std: 0,
      average_press_latency: 0,
      longest_interkey_delay: 0,
      pause_count: 0,
      total_pause_duration: 0,
      backspace_count: 0,
      backspace_rate: 0,
      correction_burst_count: 0,
      characters_per_second: 0,
    };
    return { sequence: [], sessionFeatures: emptySession };
  }

  // Sort records by keydownTimestamp
  const sorted = [...completedRecords].sort((a, b) => a.keydownTimestamp - b.keydownTimestamp);

  const sequence: KeystrokeFeatureItem[] = [];
  const dwellTimes: number[] = [];
  const flightTimes: number[] = [];
  const pressLatencies: number[] = [];

  let pauseCount = 0;
  let totalPauseDuration = 0;
  let backspaceCount = 0;
  let correctionBurstCount = 0;
  let currentBurstLength = 0;
  let longestDelay = 0;

  const firstKeyDown = sorted[0].keydownTimestamp;
  const lastEventTime = Math.max(...sorted.map(r => r.keyupTimestamp ?? r.keydownTimestamp));
  const totalTypingDuration = Math.max(0, lastEventTime - firstKeyDown);

  for (let i = 0; i < sorted.length; i++) {
    const curr = sorted[i];
    const dwell = Math.max(0, (curr.keyupTimestamp ?? curr.keydownTimestamp) - curr.keydownTimestamp);
    dwellTimes.push(dwell);

    let flight: number | null = null;
    let pressLatency: number | null = null;
    let isPause = false;

    if (i > 0) {
      const prev = sorted[i - 1];
      const prevUp = prev.keyupTimestamp ?? prev.keydownTimestamp;

      // Flight time = keydown[i] - keyup[i-1] (Negative flight time permitted for key overlaps!)
      flight = curr.keydownTimestamp - prevUp;
      flightTimes.push(flight);

      // Press-to-press latency = keydown[i] - keydown[i-1]
      pressLatency = curr.keydownTimestamp - prev.keydownTimestamp;
      pressLatencies.push(pressLatency);

      if (pressLatency > longestDelay) {
        longestDelay = pressLatency;
      }

      // Requirement 5: Press-to-press latency is used for pause detection
      if (pressLatency >= pauseThresholdMs) {
        isPause = true;
        pauseCount++;
        totalPauseDuration += pressLatency;
      }
    }

    if (curr.isBackspace) {
      backspaceCount++;
      currentBurstLength++;
    } else {
      if (currentBurstLength >= 2) {
        correctionBurstCount++;
      }
      currentBurstLength = 0;
    }

    sequence.push({
      sequence_index: i,
      dwell_time: parseFloat(dwell.toFixed(2)),
      flight_time: flight !== null ? parseFloat(flight.toFixed(2)) : null,
      press_to_press_latency: pressLatency !== null ? parseFloat(pressLatency.toFixed(2)) : null,
      is_backspace: curr.isBackspace,
      is_pause: isPause,
    });
  }

  if (currentBurstLength >= 2) {
    correctionBurstCount++;
  }

  const totalKeyPresses = sorted.length;
  const backspaceRate = totalKeyPresses > 0 ? backspaceCount / totalKeyPresses : 0;
  const durationSec = totalTypingDuration / 1000;
  const cps = durationSec > 0 ? finalLength / durationSec : 0;

  const avgDwell = mean(dwellTimes);
  const stdDwell = stdDev(dwellTimes, avgDwell);
  const avgFlight = mean(flightTimes);
  const stdFlight = stdDev(flightTimes, avgFlight);
  const avgPressLatency = mean(pressLatencies);

  const sessionFeatures: SessionFeaturesSchema = {
    total_typing_duration: parseFloat(totalTypingDuration.toFixed(2)),
    total_key_presses: totalKeyPresses,
    average_dwell_time: parseFloat(avgDwell.toFixed(2)),
    dwell_time_std: parseFloat(stdDwell.toFixed(2)),
    average_flight_time: parseFloat(avgFlight.toFixed(2)),
    flight_time_std: parseFloat(stdFlight.toFixed(2)),
    average_press_latency: parseFloat(avgPressLatency.toFixed(2)),
    longest_interkey_delay: parseFloat(longestDelay.toFixed(2)),
    pause_count: pauseCount,
    total_pause_duration: parseFloat(totalPauseDuration.toFixed(2)),
    backspace_count: backspaceCount,
    backspace_rate: parseFloat(backspaceRate.toFixed(4)),
    correction_burst_count: correctionBurstCount,
    characters_per_second: parseFloat(cps.toFixed(2)),
  };

  return { sequence, sessionFeatures };
}

function mean(arr: number[]): number {
  if (arr.length === 0) return 0;
  return arr.reduce((sum, v) => sum + v, 0) / arr.length;
}

function stdDev(arr: number[], avg: number): number {
  if (arr.length <= 1) return 0;
  const variance = arr.reduce((sum, v) => sum + Math.pow(v - avg, 2), 0) / arr.length;
  return Math.sqrt(variance);
}
