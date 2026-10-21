import React, { useEffect, useState } from 'react';
import { AnalyticsSummaryResponse, SessionSummaryResponse } from '../types';
import { fetchAnalyticsSummary, fetchSessionSummaries, getCsvExportUrl, deleteSessionById } from '../services/api';
import { X, Download, Database, Trash2, RefreshCw, CheckCircle, AlertTriangle } from 'lucide-react';
import { SessionComparison } from './SessionComparison';

interface AnalyticsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function formatLog10Estimate(value: number | null): string {
  return value === null ? '-' : value.toFixed(4);
}

export const AnalyticsModal: React.FC<AnalyticsModalProps> = ({ isOpen, onClose }) => {
  const [analytics, setAnalytics] = useState<AnalyticsSummaryResponse | null>(null);
  const [summaries, setSummaries] = useState<SessionSummaryResponse[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [an, sum] = await Promise.all([
        fetchAnalyticsSummary(),
        fetchSessionSummaries(),
      ]);
      setAnalytics(an);
      setSummaries(sum);
    } catch (err: any) {
      setError(err.message || 'Failed to load research analytics');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadData();
    }
  }, [isOpen]);

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this session record?')) return;
    try {
      await deleteSessionById(id);
      loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to delete session');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950">
          <div className="flex items-center gap-2.5">
            <Database className="w-5 h-5 text-blue-400" />
            <h2 className="text-lg font-bold text-white">Research Team Analytics & Data Export</h2>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={loadData}
              disabled={isLoading}
              className="p-2 text-slate-400 hover:text-white transition-colors"
              title="Refresh Data"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-white transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {error && (
            <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-lg text-xs text-rose-300">
              {error}
            </div>
          )}

          {analytics && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                <div className="text-xs text-slate-400">Total Sessions</div>
                <div className="text-2xl font-bold font-mono text-white mt-1">{analytics.total_sessions}</div>
                <div className="text-[10px] text-slate-400 mt-1">
                  {analytics.valid_session_count} valid / {analytics.invalid_session_count} flagged
                </div>
              </div>

              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                <div className="text-xs text-slate-400">Participants</div>
                <div className="text-2xl font-bold font-mono text-blue-400 mt-1">{analytics.total_participants}</div>
                <div className="text-[10px] text-slate-400 mt-1">Reusable Codes</div>
              </div>

              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                <div className="text-xs text-slate-400">Timed vs Untimed</div>
                <div className="text-2xl font-bold font-mono text-amber-400 mt-1">
                  {analytics.timed_session_count} / {analytics.untimed_session_count}
                </div>
                <div className="text-[10px] text-slate-400 mt-1">Condition Split</div>
              </div>

              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                <div className="text-xs text-slate-400">Avg Duration & zxcvbn</div>
                <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">
                  {(analytics.average_duration / 1000).toFixed(1)}s
                </div>
                <div className="text-[10px] text-slate-400 mt-1">Avg Score: {analytics.average_zxcvbn_score}/4</div>
              </div>
            </div>
          )}

          {/* Export Action Card */}
          <div className="bg-blue-600/10 border border-blue-500/20 rounded-xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <h3 className="text-sm font-semibold text-white">Model-Ready Dataset CSV</h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Contains privacy-safe timing sequences, derived behavioral features, model outcomes, static scores, and anonymous metadata.
              </p>
            </div>

            <a
              href={getCsvExportUrl()}
              download="behavepass_dataset.csv"
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-lg shadow-md transition-all shrink-0"
            >
              <Download className="w-4 h-4" />
              Download Dataset CSV
            </a>
          </div>

          <SessionComparison sessions={summaries} />

          {/* Recent Sessions Table */}
          <div>
            <h3 className="text-sm font-semibold text-slate-200 mb-3">Stored Experimental Sessions</h3>
            <div className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-900 border-b border-slate-800 font-mono text-slate-400 text-[11px]">
                    <tr>
                      <th className="p-3">Participant Code</th>
                      <th className="p-3">Condition</th>
                      <th className="p-3">Status</th>
                      <th className="p-3">Len</th>
                      <th className="p-3">zxcvbn</th>
                      <th className="p-3">Static Log10</th>
                      <th className="p-3">Behavioral Log10</th>
                      <th className="p-3">Duration</th>
                      <th className="p-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono">
                    {summaries.length === 0 ? (
                      <tr>
                        <td colSpan={9} className="p-6 text-center text-slate-500 font-sans">
                          No experimental sessions recorded yet.
                        </td>
                      </tr>
                    ) : (
                      summaries.map((s) => (
                        <tr key={s.id} className="hover:bg-slate-900/40 text-slate-300">
                          <td className="p-3 text-blue-400 font-semibold">{s.participant_code}</td>
                          <td className="p-3">{s.condition}</td>
                          <td className="p-3">
                            {s.is_valid ? (
                              <span className="text-emerald-400 flex items-center gap-1"><CheckCircle className="w-3 h-3" /> Valid</span>
                            ) : (
                              <span className="text-rose-400 flex items-center gap-1"><AlertTriangle className="w-3 h-3" /> Flagged</span>
                            )}
                          </td>
                          <td className="p-3">{s.password_length}</td>
                          <td className="p-3">{s.zxcvbn_score}/4</td>
                          <td className="p-3">{formatLog10Estimate(s.log10_estimated_guesses)}</td>
                          <td className="p-3">{formatLog10Estimate(s.fusion_log10_estimated_guesses)}</td>
                          <td className="p-3">{(s.total_typing_duration / 1000).toFixed(1)}s</td>
                          <td className="p-3 text-right">
                            <button
                              onClick={() => handleDelete(s.id)}
                              className="p-1.5 text-slate-500 hover:text-rose-400 transition-colors"
                              title="Delete Session"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};
