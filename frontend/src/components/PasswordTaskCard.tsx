import React, { useEffect, useState } from 'react';
import { ExperimentalCondition } from '../types';
import { Lock, RefreshCw, Send, AlertTriangle, CheckCircle2, Timer } from 'lucide-react';

interface PasswordTaskCardProps {
  condition: ExperimentalCondition;
  hasConsented: boolean;
  passwordValue: string;
  isValid: boolean;
  invalidReason: string | null;
  recordsCount: number;
  attemptNumber: number;
  handleKeyDown: (e: React.KeyboardEvent<HTMLInputElement>) => void;
  handleKeyUp: (e: React.KeyboardEvent<HTMLInputElement>) => void;
  handlePaste: (e: React.ClipboardEvent<HTMLInputElement>) => void;
  handleBlur: (e: React.FocusEvent<HTMLInputElement>) => void;
  markIntentionalControlInteraction: () => void;
  handleChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onReset: () => void;
  onSubmit: () => void;
  isSubmitting: boolean;
}

export const PasswordTaskCard: React.FC<PasswordTaskCardProps> = ({
  condition,
  hasConsented,
  passwordValue,
  isValid,
  invalidReason,
  recordsCount,
  attemptNumber,
  handleKeyDown,
  handleKeyUp,
  handlePaste,
  handleBlur,
  markIntentionalControlInteraction,
  handleChange,
  onReset,
  onSubmit,
  isSubmitting,
}) => {
  const [timeLeftMs, setTimeLeftMs] = useState<number>(15000);
  const [timerActive, setTimerActive] = useState<boolean>(false);

  // Timed mode countdown timer
  useEffect(() => {
    if (condition !== 'timed') {
      setTimerActive(false);
      return;
    }

    if (passwordValue.length > 0 && !timerActive) {
      setTimerActive(true);
    }

    if (timerActive) {
      const interval = setInterval(() => {
        setTimeLeftMs((prev) => {
          if (prev <= 100) {
            clearInterval(interval);
            return 0;
          }
          return prev - 100;
        });
      }, 100);

      return () => clearInterval(interval);
    }
  }, [condition, passwordValue.length, timerActive]);

  const handleResetClick = () => {
    setTimeLeftMs(15000);
    setTimerActive(false);
    onReset();
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl mb-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
        <div>
          <h2 className="text-xl font-semibold text-white flex items-center gap-2">
            <Lock className="w-5 h-5 text-blue-400" />
            Password Creation Task (Attempt #{attemptNumber})
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Type your experimental password naturally using standard typing rhythm.
          </p>
        </div>

        {condition === 'timed' && (
          <div className="flex items-center gap-2 bg-amber-500/10 border border-amber-500/30 px-3 py-1.5 rounded-lg text-amber-300 font-mono text-sm">
            <Timer className="w-4 h-4 animate-pulse" />
            <span>Time Remaining: {(timeLeftMs / 1000).toFixed(1)}s</span>
          </div>
        )}
      </div>

      <div className="space-y-4">
        <div className="relative">
          <label className="block text-xs font-medium text-slate-300 mb-1.5">
            Experimental Password Field:
          </label>
          <input
            type="password"
            autoComplete="new-password"
            spellCheck={false}
            disabled={!hasConsented || isSubmitting || (condition === 'timed' && timeLeftMs === 0)}
            value={passwordValue}
            onKeyDown={handleKeyDown}
            onKeyUp={handleKeyUp}
            onPaste={handlePaste}
            onBlur={handleBlur}
            onChange={handleChange}
            placeholder={hasConsented ? "Type your experimental password here..." : "Please accept privacy consent above to begin"}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-3 text-white font-mono text-base tracking-widest focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          />

          {!isValid && (
            <div className="mt-2 flex items-center gap-2 text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 p-2.5 rounded-lg">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>Session Flagged: {invalidReason || 'Invalid typing trail'}</span>
            </div>
          )}
        </div>

        <div className="flex flex-wrap items-center justify-between gap-4 pt-2 border-t border-slate-800">
          <div className="flex items-center gap-4 text-xs text-slate-400 font-mono">
            <span>Keys Captured: <strong className="text-blue-400">{recordsCount}</strong></span>
            <span>Length: <strong className="text-slate-200">{passwordValue.length}</strong></span>
            <span className="flex items-center gap-1">
              Validity: 
              {isValid ? (
                <span className="text-emerald-400 flex items-center gap-0.5"><CheckCircle2 className="w-3.5 h-3.5" /> Valid</span>
              ) : (
                <span className="text-rose-400 flex items-center gap-0.5"><AlertTriangle className="w-3.5 h-3.5" /> Flagged</span>
              )}
            </span>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              data-experiment-control="true"
              onPointerDown={markIntentionalControlInteraction}
              onClick={handleResetClick}
              disabled={isSubmitting || passwordValue.length === 0}
              className="flex items-center gap-1.5 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Reset Field
            </button>

            <button
              type="button"
              data-experiment-control="true"
              onPointerDown={markIntentionalControlInteraction}
              onClick={onSubmit}
              disabled={!hasConsented || isSubmitting || passwordValue.length === 0}
              className="flex items-center gap-2 px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-lg shadow-lg shadow-blue-600/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send className="w-3.5 h-3.5" />
              {isSubmitting ? 'Processing Session...' : 'Submit Session & Analyze'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
