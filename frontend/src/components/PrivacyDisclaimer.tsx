import React from 'react';
import { ShieldAlert, Lock, CheckSquare, Square } from 'lucide-react';

interface PrivacyDisclaimerProps {
  hasConsented: boolean;
  onConsentChange: (consented: boolean) => void;
  participantCode: string;
  onParticipantCodeChange: (code: string) => void;
}

export const PrivacyDisclaimer: React.FC<PrivacyDisclaimerProps> = ({
  hasConsented,
  onConsentChange,
  participantCode,
  onParticipantCodeChange,
}) => {
  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 shadow-xl backdrop-blur-sm mb-6">
      <div className="flex items-start space-x-4">
        <div className="p-3 bg-amber-500/10 rounded-lg text-amber-400 border border-amber-500/20 shrink-0">
          <ShieldAlert className="w-6 h-6" />
        </div>
        <div className="flex-1 space-y-3">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            Cybersecurity Research Privacy Protocol
          </h2>
          <div className="text-sm text-slate-300 space-y-2">
            <p className="leading-relaxed">
              <strong className="text-amber-300">IMPORTANT SECURITY WARNING:</strong> Do <strong className="underline">NOT</strong> enter a real password or a password you use for any account. Create a unique, synthetic password strictly for this research task.
            </p>
            <p className="text-slate-400 text-xs leading-normal">
              • Plaintext passwords and raw character keys are <strong className="text-slate-200">never saved or logged</strong>. All character metrics are computed locally in your browser.<br />
              • Recorded session data includes timing intervals (dwell time, flight time), pause counts, backspace statistics, static zxcvbn score, and an anonymous participant ID.
            </p>
          </div>

          <div className="pt-2 flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between border-t border-slate-800/80">
            <div className="flex items-center gap-3">
              <label className="text-xs font-medium text-slate-400">Reusable Anonymous Code:</label>
              <input
                type="text"
                value={participantCode}
                onChange={(e) => onParticipantCodeChange(e.target.value.toUpperCase())}
                placeholder="PART-8921"
                className="bg-slate-950 border border-slate-700 rounded px-3 py-1 text-xs text-blue-400 font-mono tracking-wider focus:outline-none focus:border-blue-500"
              />
            </div>

            <button
              type="button"
              onClick={() => onConsentChange(!hasConsented)}
              className="flex items-center gap-2 text-sm font-medium text-slate-200 hover:text-white transition-colors cursor-pointer select-none"
            >
              {hasConsented ? (
                <CheckSquare className="w-5 h-5 text-blue-500 shrink-0" />
              ) : (
                <Square className="w-5 h-5 text-slate-500 shrink-0" />
              )}
              <span>I consent to participate & confirm I am entering a synthetic test password.</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
