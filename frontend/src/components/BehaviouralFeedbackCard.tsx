import React from 'react';
import { PredictResponse, CreateSessionPayload } from '../types';
import { ShieldCheck, Cpu, Activity, Clock, AlertCircle, Info, Sparkles } from 'lucide-react';

interface BehaviouralFeedbackCardProps {
  prediction: PredictResponse | null;
  payload: CreateSessionPayload | null;
}

export const BehaviouralFeedbackCard: React.FC<BehaviouralFeedbackCardProps> = ({
  prediction,
  payload,
}) => {
  if (!prediction || !payload) return null;

  const { static_features, session_features } = payload;

  const getTierColor = (score: number) => {
    switch (score) {
      case 0:
      case 1:
        return 'text-rose-400 border-rose-500/30 bg-rose-500/10';
      case 2:
        return 'text-amber-400 border-amber-500/30 bg-amber-500/10';
      case 3:
        return 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10';
      case 4:
        return 'text-cyan-400 border-cyan-500/30 bg-cyan-500/10';
      default:
        return 'text-slate-400 border-slate-700 bg-slate-800';
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-6">
          <div className="flex items-center gap-2.5">
            <Sparkles className="w-5 h-5 text-blue-400" />
            <h2 className="text-xl font-bold text-white">Experimental Session Analysis</h2>
          </div>
          <span className="text-xs font-mono text-slate-400 bg-slate-950 border border-slate-800 px-3 py-1 rounded-full">
            Schema v{payload.feature_schema_version}
          </span>
        </div>

        {/* 2-Column Section: Static vs Behavioural Timing */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          
          {/* Static Analysis Card */}
          <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-5">
            <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2 mb-4">
              <ShieldCheck className="w-4 h-4 text-blue-400" />
              Static Password Features (In-Memory)
            </h3>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400">Static Strength Tier:</span>
                <span className={`text-xs font-bold font-mono px-3 py-1 rounded-full border ${getTierColor(prediction.zxcvbn_score)}`}>
                  {prediction.static_strength_tier} (zxcvbn {prediction.zxcvbn_score}/4)
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs font-mono">
                <div className="bg-slate-900 p-2.5 rounded border border-slate-800">
                  <div className="text-slate-400 text-[10px]">Log10 Guesses</div>
                  <div className="text-blue-300 font-semibold text-sm mt-0.5">{static_features.log10_estimated_guesses}</div>
                </div>

                <div className="bg-slate-900 p-2.5 rounded border border-slate-800">
                  <div className="text-slate-400 text-[10px]">Password Length</div>
                  <div className="text-slate-200 font-semibold text-sm mt-0.5">{static_features.password_length} chars</div>
                </div>

                <div className="bg-slate-900 p-2.5 rounded border border-slate-800">
                  <div className="text-slate-400 text-[10px]">Empirical Entropy</div>
                  <div className="text-purple-300 font-semibold text-sm mt-0.5">{static_features.empirical_character_entropy} bits</div>
                </div>

                <div className="bg-slate-900 p-2.5 rounded border border-slate-800">
                  <div className="text-slate-400 text-[10px]">Pool Entropy Est.</div>
                  <div className="text-purple-300 font-semibold text-sm mt-0.5">{static_features.character_pool_entropy_estimate} bits</div>
                </div>
              </div>

              <div className="text-[11px] text-slate-400 border-t border-slate-900 pt-2 leading-relaxed">
                Character Breakdown: {static_features.lowercase_count} lower, {static_features.uppercase_count} upper, {static_features.digit_count} digits, {static_features.symbol_count} symbols ({static_features.unique_character_count} unique).
              </div>
            </div>
          </div>

          {/* Behavioural Timing Metrics Card */}
          <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-5">
            <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2 mb-4">
              <Activity className="w-4 h-4 text-emerald-400" />
              Keystroke Dynamics Metrics
            </h3>

            <div className="grid grid-cols-2 gap-3 text-xs font-mono mb-4">
              <div className="bg-slate-900 p-2.5 rounded border border-slate-800">
                <div className="text-slate-400 text-[10px]">Avg Dwell Time</div>
                <div className="text-emerald-300 font-semibold text-sm mt-0.5">{session_features.average_dwell_time} ms</div>
                <div className="text-[9px] text-slate-400">std: ±{session_features.dwell_time_std} ms</div>
              </div>

              <div className="bg-slate-900 p-2.5 rounded border border-slate-800">
                <div className="text-slate-400 text-[10px]">Avg Flight Time</div>
                <div className="text-emerald-300 font-semibold text-sm mt-0.5">{session_features.average_flight_time} ms</div>
                <div className="text-[9px] text-slate-400">std: ±{session_features.flight_time_std} ms</div>
              </div>

              <div className="bg-slate-900 p-2.5 rounded border border-slate-800">
                <div className="text-slate-400 text-[10px]">Typing Duration</div>
                <div className="text-slate-200 font-semibold text-sm mt-0.5">{(session_features.total_typing_duration / 1000).toFixed(2)} s</div>
              </div>

              <div className="bg-slate-900 p-2.5 rounded border border-slate-800">
                <div className="text-slate-400 text-[10px]">Typing Speed</div>
                <div className="text-slate-200 font-semibold text-sm mt-0.5">{session_features.characters_per_second} char/s</div>
              </div>

              <div className="bg-slate-900 p-2.5 rounded border border-slate-800">
                <div className="text-slate-400 text-[10px]">Backspaces / Bursts</div>
                <div className="text-amber-300 font-semibold text-sm mt-0.5">{session_features.backspace_count} / {session_features.correction_burst_count}</div>
              </div>

              <div className="bg-slate-900 p-2.5 rounded border border-slate-800">
                <div className="text-slate-400 text-[10px]">Pauses (&ge;{payload.pause_threshold_ms}ms)</div>
                <div className="text-amber-300 font-semibold text-sm mt-0.5">{session_features.pause_count} pauses</div>
              </div>
            </div>
          </div>

        </div>

        {/* Behavioural Observation Summary */}
        <div className="mt-6 bg-slate-950 border border-slate-800 rounded-lg p-5">
          <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-2">
            <Info className="w-4 h-4 text-blue-400" />
            Transparent Rule-Based Behavioural Observations
          </h3>

          <ul className="space-y-2 text-xs text-slate-200 font-sans">
            {prediction.behavioural_summary.map((obs, idx) => (
              <li key={idx} className="flex items-start gap-2 bg-slate-900/60 p-2.5 rounded border border-slate-800/60">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-400 mt-1.5 shrink-0" />
                <span>{obs}</span>
              </li>
            ))}
          </ul>

          <div className="mt-4 p-3 bg-blue-500/5 border border-blue-500/10 rounded text-[11px] text-slate-400 flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
            <div>
              <strong className="text-slate-300">BiLSTM Pipeline Status:</strong> {prediction.behavioural_model_status === 'not_trained' ? 'Behavioural BiLSTM neural model is currently pending dataset collection and training (Phase 1 Baseline).' : prediction.behavioural_model_status}
              <br />
              <span className="text-[10px] text-slate-400">Notice: Observations describe physical timing metrics only. No claims regarding stress, fatigue, anxiety, or cognitive load are made.</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
