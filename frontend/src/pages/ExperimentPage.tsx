import React, { useState } from 'react';
import { ExperimentalCondition, PredictResponse, CreateSessionPayload } from '../types';
import { useKeystrokeCollector } from '../hooks/useKeystrokeCollector';
import { postSession, requestPrediction } from '../services/api';
import { ParticipantHeader } from '../components/ParticipantHeader';
import { PrivacyDisclaimer } from '../components/PrivacyDisclaimer';
import { PasswordTaskCard } from '../components/PasswordTaskCard';
import { BehaviouralFeedbackCard } from '../components/BehaviouralFeedbackCard';
import { AnalyticsModal } from '../components/AnalyticsModal';

export const ExperimentPage: React.FC = () => {
  const [condition, setCondition] = useState<ExperimentalCondition>('untimed');
  const [hasConsented, setHasConsented] = useState<boolean>(false);
  const [participantCode, setParticipantCode] = useState<string>('PART-8921');
  const [isAnalyticsOpen, setIsAnalyticsOpen] = useState<boolean>(false);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const [lastPrediction, setLastPrediction] = useState<PredictResponse | null>(null);
  const [lastPayload, setLastPayload] = useState<CreateSessionPayload | null>(null);

  const collector = useKeystrokeCollector({
    participantCode,
    condition,
    timedLimitMs: 15000,
    pauseThresholdMs: 500.0,
    taskId: 'TASK-01',
  });

  const handleSubmit = async () => {
    setSubmitError(null);
    const payload = collector.prepareSessionPayload();
    if (!payload) {
      setSubmitError('Please enter a password before submitting.');
      return;
    }

    setIsSubmitting(true);
    try {
      // 1. Post session record to FastAPI backend
      await postSession(payload);

      // 2. Request prototype rule-based prediction & observations
      const pred = await requestPrediction(payload.static_features, payload.session_features);

      setLastPayload(payload);
      setLastPrediction(pred);
    } catch (err: any) {
      setSubmitError(err.message || 'Failed to process session submit');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen max-w-6xl mx-auto px-4 py-8">
      {/* Header & Mode Switcher */}
      <ParticipantHeader
        condition={condition}
        onConditionChange={setCondition}
        onOpenAnalytics={() => setIsAnalyticsOpen(true)}
      />

      {/* Privacy Disclaimer & Consent */}
      <PrivacyDisclaimer
        hasConsented={hasConsented}
        onConsentChange={setHasConsented}
        participantCode={participantCode}
        onParticipantCodeChange={setParticipantCode}
      />

      {/* Main Password Task Card */}
      <PasswordTaskCard
        condition={condition}
        hasConsented={hasConsented}
        passwordValue={collector.passwordValue}
        isValid={collector.isValid}
        invalidReason={collector.invalidReason}
        recordsCount={collector.recordsCount}
        attemptNumber={collector.attemptNumber}
        handleKeyDown={collector.handleKeyDown}
        handleKeyUp={collector.handleKeyUp}
        handlePaste={collector.handlePaste}
        handleBlur={collector.handleBlur}
        handleChange={collector.handleChange}
        onReset={collector.resetSession}
        onSubmit={handleSubmit}
        isSubmitting={isSubmitting}
      />

      {submitError && (
        <div className="mb-6 p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-300 text-sm">
          {submitError}
        </div>
      )}

      {/* Post-Submission Feedback */}
      <BehaviouralFeedbackCard
        prediction={lastPrediction}
        payload={lastPayload}
      />

      {/* Research Dashboard Modal */}
      <AnalyticsModal
        isOpen={isAnalyticsOpen}
        onClose={() => setIsAnalyticsOpen(false)}
      />
    </div>
  );
};
