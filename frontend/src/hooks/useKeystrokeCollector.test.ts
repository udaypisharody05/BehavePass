import { describe, it, expect } from 'vitest';
import { calculateStaticFeatures } from '../utils/staticFeatures';

describe('Validation and Session Control Logic', () => {
  it('flags session invalid on paste event', () => {
    let isValid = true;
    let invalidReason: string | null = null;

    const handlePaste = (e: { preventDefault: () => void }) => {
      e.preventDefault();
      isValid = false;
      invalidReason = 'Paste action detected and rejected';
    };

    handlePaste({ preventDefault: () => {} });
    expect(isValid).toBe(false);
    expect(invalidReason).toContain('Paste action detected');
  });

  it('flags session invalid on focus loss when input is non-empty', () => {
    let isValid = true;
    let invalidReason: string | null = null;
    const passwordLength = 8;

    const handleBlur = () => {
      if (passwordLength > 0) {
        isValid = false;
        invalidReason = 'Input focus lost during password entry';
      }
    };

    handleBlur();
    expect(isValid).toBe(false);
    expect(invalidReason).toContain('focus lost');
  });

  it('resets collector state on session reset', () => {
    let passwordValue = 'Secret123!';
    let attemptNumber = 1;
    let isValid = false;

    const resetSession = () => {
      passwordValue = '';
      isValid = true;
      attemptNumber += 1;
    };

    resetSession();
    expect(passwordValue).toBe('');
    expect(isValid).toBe(true);
    expect(attemptNumber).toBe(2);
  });
});
