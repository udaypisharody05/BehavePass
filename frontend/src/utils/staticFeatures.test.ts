import { describe, it, expect } from 'vitest';
import { calculateStaticFeatures } from './staticFeatures';

describe('staticFeatures utility tests', () => {
  it('computes character distribution and zxcvbn score without storing password', () => {
    const res = calculateStaticFeatures('P@ssword123');
    expect(res.password_length).toBe(11);
    expect(res.uppercase_count).toBe(1);
    expect(res.lowercase_count).toBe(6);
    expect(res.digit_count).toBe(3);
    expect(res.symbol_count).toBe(1);
    expect(res.zxcvbn_score).toBeGreaterThanOrEqual(0);
    expect(res.log10_estimated_guesses).toBeGreaterThan(0);
    expect(res.empirical_character_entropy).toBeGreaterThan(0);
    expect(res.character_pool_entropy_estimate).toBeGreaterThan(0);
  });
});
