import React from 'react';
import { ExperimentalCondition } from '../types';
import { Clock, Sliders, Database } from 'lucide-react';

interface ParticipantHeaderProps {
  condition: ExperimentalCondition;
  onConditionChange: (cond: ExperimentalCondition) => void;
  onOpenAnalytics: () => void;
}

export const ParticipantHeader: React.FC<ParticipantHeaderProps> = ({
  condition,
  onConditionChange,
  onOpenAnalytics,
}) => {
  return (
    <header className="flex flex-col md:flex-row justify-between items-start md:items-center py-6 border-b border-slate-800 gap-4 mb-8">
      <div>
        <div className="flex items-center gap-3">
          <span className="bg-blue-600/20 text-blue-400 border border-blue-500/30 text-xs font-mono px-2.5 py-1 rounded-full font-medium">
            BehavePass-Lite v1.0
          </span>
          <span className="text-xs text-slate-400 font-mono">Phase 1 Vertical Prototype</span>
        </div>
        <h1 className="text-2xl md:text-3xl font-bold text-white mt-1 tracking-tight">
          Password Strength & Keystroke Dynamics Experiment
        </h1>
      </div>

      <div className="flex items-center gap-3 w-full md:w-auto justify-between md:justify-end">
        <div className="flex items-center bg-slate-900 border border-slate-800 rounded-lg p-1">
          <button
            onClick={() => onConditionChange('untimed')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
              condition === 'untimed'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Sliders className="w-3.5 h-3.5" />
            Untimed Mode
          </button>
          <button
            onClick={() => onConditionChange('timed')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
              condition === 'timed'
                ? 'bg-amber-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Clock className="w-3.5 h-3.5" />
            Timed Mode (15s)
          </button>
        </div>

        <button
          onClick={onOpenAnalytics}
          className="flex items-center gap-1.5 px-3 py-2 bg-slate-900 border border-slate-800 hover:border-slate-700 text-xs font-medium text-slate-300 hover:text-white rounded-lg transition-all"
        >
          <Database className="w-4 h-4 text-blue-400" />
          <span>Research Dashboard</span>
        </button>
      </div>
    </header>
  );
};
