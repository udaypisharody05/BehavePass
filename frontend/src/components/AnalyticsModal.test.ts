import { describe, expect, it } from 'vitest';

import { formatLog10Estimate } from './AnalyticsModal';


describe('AnalyticsModal Log10 formatting', () => {
  it('shows unavailable behavioral estimates as a dash', () => {
    expect(formatLog10Estimate(null)).toBe('-');
  });

  it('formats estimates to four decimal places without changing source precision', () => {
    const estimate = 14.148052626142771;

    expect(formatLog10Estimate(estimate)).toBe('14.1481');
    expect(estimate).toBe(14.148052626142771);
  });
});
