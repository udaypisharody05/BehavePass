import { useState, useRef, useCallback } from 'react';
import {
  RawKeyRecord,
  computeSessionFeatures,
  isCapturedPasswordKey,
} from '../utils/keystrokeFeatures';
import { calculateStaticFeatures } from '../utils/staticFeatures';
import { CreateSessionPayload, ExperimentalCondition } from '../types';

export interface UseKeystrokeCollectorProps {
  participantCode: string;
  condition: ExperimentalCondition;
  timedLimitMs?: number;
  pauseThresholdMs?: number;
  taskId?: string;
}

export function useKeystrokeCollector({
  participantCode,
  condition,
  timedLimitMs = 15000,
  pauseThresholdMs = 500.0,
  taskId = 'TASK-01',
}: UseKeystrokeCollectorProps) {
  const [passwordValue, setPasswordValue] = useState<string>('');
  const [isValid, setIsValid] = useState<boolean>(true);
  const [invalidReason, setInvalidReason] = useState<string | null>(null);
  const [attemptNumber, setAttemptNumber] = useState<number>(1);
  const [isTimedOut, setIsTimedOut] = useState<boolean>(false);

  // Active keydown events mapped by opaque key identifier
  const activeKeysRef = useRef<Map<string, { keyId: string; isBackspace: boolean; start: number }>>(new Map());
  const completedRecordsRef = useRef<RawKeyRecord[]>([]);
  const pendingKeystrokeCountRef = useRef<number>(0);
  const keyIdCounterRef = useRef<number>(0);
  const intentionalControlInteractionRef = useRef<boolean>(false);

  const resetCollector = useCallback(() => {
    setPasswordValue('');
    setIsValid(true);
    setInvalidReason(null);
    setIsTimedOut(false);
    activeKeysRef.current.clear();
    completedRecordsRef.current = [];
    pendingKeystrokeCountRef.current = 0;
  }, []);

  const resetSession = useCallback(() => {
    resetCollector();
    setAttemptNumber((prev) => prev + 1);
  }, [resetCollector]);

  const flagTimeout = useCallback(() => {
    setIsTimedOut(true);
  }, []);

  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
    // If e.repeat is true, browser is auto-repeating held key. Ignore for timing pair matching.
    if (e.repeat || !isCapturedPasswordKey(e.key)) return;

    const isBackspace = e.key === 'Backspace';
    const now = performance.now();
    const keyId = `key_${keyIdCounterRef.current++}`;

    // Store active key down using code/key for event pairing during this session
    // Note: Opaque keyId is stored in raw records, NOT raw character
    const matchKey = e.code || e.key;
    activeKeysRef.current.set(matchKey, {
      keyId,
      isBackspace,
      start: now,
    });

    pendingKeystrokeCountRef.current += 1;
  }, []);

  const handleKeyUp = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!isCapturedPasswordKey(e.key)) return;

    const now = performance.now();
    const matchKey = e.code || e.key;
    const active = activeKeysRef.current.get(matchKey);

    if (active) {
      completedRecordsRef.current.push({
        keyId: active.keyId,
        isBackspace: active.isBackspace,
        keydownTimestamp: active.start,
        keyupTimestamp: now,
      });
      activeKeysRef.current.delete(matchKey);
    } else {
      // Unmatched keyup event
      completedRecordsRef.current.push({
        keyId: `unmatched_${keyIdCounterRef.current++}`,
        isBackspace: e.key === 'Backspace',
        keydownTimestamp: now,
        keyupTimestamp: now,
      });
    }
  }, []);

  const handlePaste = useCallback((e: React.ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault();
    setIsValid(false);
    setInvalidReason('Paste action detected and rejected');
  }, []);

  const markIntentionalControlInteraction = useCallback(() => {
    intentionalControlInteractionRef.current = true;
  }, []);

  const handleBlur = useCallback((e: React.FocusEvent<HTMLInputElement>) => {
    const relatedTarget = e.relatedTarget;
    const movedToExperimentControl =
      relatedTarget instanceof HTMLElement
      && relatedTarget.dataset.experimentControl === 'true';
    const intentionalFocusChange =
      intentionalControlInteractionRef.current || movedToExperimentControl;
    intentionalControlInteractionRef.current = false;

    if (intentionalFocusChange) return;

    // If input loses focus mid-typing, flag session as having focus loss
    if (passwordValue.length > 0) {
      setIsValid(false);
      setInvalidReason('Input focus lost during password entry');
    }
  }, [passwordValue.length]);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    // Check for autofill / rapid text insert where length jumped without keystrokes
    if (val.length > passwordValue.length + 1 && pendingKeystrokeCountRef.current === 0) {
      setIsValid(false);
      setInvalidReason('Autofill or programmatic text insertion detected');
    }
    setPasswordValue(val);
  }, [passwordValue.length]);

  const prepareSessionPayload = useCallback((): CreateSessionPayload | null => {
    if (!passwordValue) return null;

    let finalValid = isValid;
    let finalReason = invalidReason;

    // Check for minimum keystroke data
    if (completedRecordsRef.current.length === 0) {
      finalValid = false;
      finalReason = finalReason || 'Insufficient keystroke timing records';
    }

    // Calculate static features in-memory ONLY
    const staticFeatures = calculateStaticFeatures(passwordValue);

    // Calculate session timing features & keystroke sequence
    const { sequence, sessionFeatures } = computeSessionFeatures(
      completedRecordsRef.current,
      pauseThresholdMs,
      passwordValue.length
    );

    const completedWithinLimit = condition === 'timed' ? !isTimedOut : null;

    return {
      participant_code: participantCode || 'ANON-PARTICIPANT',
      task_id: taskId,
      task_type: 'creation',
      attempt_number: attemptNumber,
      condition,
      timed_limit_ms: condition === 'timed' ? timedLimitMs : null,
      completed_within_limit: completedWithinLimit,
      timed_out: isTimedOut,
      pause_threshold_ms: pauseThresholdMs,
      collector_version: '1.0.0',
      feature_schema_version: '1.0.0',
      consent_version: '1.0.0',
      is_valid: finalValid,
      invalid_reason: finalReason,
      device_type: 'desktop',
      static_features: staticFeatures,
      session_features: sessionFeatures,
      keystroke_sequence: sequence,
    };
  }, [
    passwordValue,
    isValid,
    invalidReason,
    isTimedOut,
    pauseThresholdMs,
    participantCode,
    taskId,
    attemptNumber,
    condition,
    timedLimitMs,
  ]);

  return {
    passwordValue,
    isValid,
    invalidReason,
    attemptNumber,
    isTimedOut,
    recordsCount: completedRecordsRef.current.length,
    handleKeyDown,
    handleKeyUp,
    handlePaste,
    handleBlur,
    markIntentionalControlInteraction,
    handleChange,
    flagTimeout,
    resetSession,
    resetCollector,
    prepareSessionPayload,
  };
}
