export type ExperimentalCondition = 'untimed' | 'timed';

export interface RawKeystrokeEvent {
  keyType: 'keydown' | 'keyup';
  timestamp: number; // high-res performance.now()
  isBackspace: boolean;
  isModifier: boolean;
}

export interface KeystrokeFeatureItem {
  sequence_index: number;
  dwell_time: number;
  flight_time: number | null; // null for first event
  press_to_press_latency: number | null; // null for first event
  is_backspace: boolean;
  is_pause: boolean;
}

export interface StaticFeaturesSchema {
  password_length: number;
  lowercase_count: number;
  uppercase_count: number;
  digit_count: number;
  symbol_count: number;
  unique_character_count: number;
  repeated_character_count: number;
  repeated_substring_count: number;
  sequential_character_count: number;
  zxcvbn_score: number;
  log10_estimated_guesses: number;
  empirical_character_entropy: number;
  character_pool_entropy_estimate: number;
}

export interface SessionFeaturesSchema {
  total_typing_duration: number;
  total_key_presses: number;
  average_dwell_time: number;
  dwell_time_std: number;
  average_flight_time: number;
  flight_time_std: number;
  average_press_latency: number;
  longest_interkey_delay: number;
  pause_count: number;
  total_pause_duration: number;
  backspace_count: number;
  backspace_rate: number;
  correction_burst_count: number;
  characters_per_second: number;
}

export interface CreateSessionPayload {
  participant_code: string;
  task_id: string;
  task_type: string;
  attempt_number: number;
  condition: ExperimentalCondition;
  timed_limit_ms: number | null;
  completed_within_limit: boolean | null;
  timed_out: boolean;
  pause_threshold_ms: number;
  collector_version: string;
  feature_schema_version: string;
  consent_version: string;
  is_valid: boolean;
  invalid_reason: string | null;
  device_type: string;
  static_features: StaticFeaturesSchema;
  session_features: SessionFeaturesSchema;
  keystroke_sequence: KeystrokeFeatureItem[];
  behavioural_model_status?: string | null;
  fusion_log10_estimated_guesses?: number | null;
}

export interface SessionResponse extends CreateSessionPayload {
  id: string;
  participant_id: number;
  created_at: string;
}

export interface SessionSummaryResponse {
  id: string;
  participant_code: string;
  task_id: string;
  condition: string;
  completed_within_limit: boolean | null;
  timed_out: boolean;
  is_valid: boolean;
  password_length: number;
  zxcvbn_score: number;
  log10_estimated_guesses: number;
  behavioural_model_status: string | null;
  fusion_log10_estimated_guesses: number | null;
  total_typing_duration: number;
  pause_count: number;
  backspace_count: number;
  created_at: string;
}

export interface AnalyticsSummaryResponse {
  total_sessions: number;
  total_participants: number;
  timed_session_count: number;
  untimed_session_count: number;
  valid_session_count: number;
  invalid_session_count: number;
  average_duration: number;
  average_backspace_count: number;
  average_pause_count: number;
  average_zxcvbn_score: number;
}

export interface PredictResponse {
  static_strength_tier: string;
  zxcvbn_score: number;
  log10_estimated_guesses: number;
  behavioural_summary: string[];
  behavioural_model_status: string;
  fusion_log10_estimated_guesses: number | null;
  model_used: string;
  model_type: string;
  target: string;
  warnings: string[];
}
