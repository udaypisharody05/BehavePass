import zxcvbn from 'zxcvbn';
import { StaticFeaturesSchema } from '../types';

export function calculateStaticFeatures(password: string): StaticFeaturesSchema {
  const passwordLength = password.length;
  if (passwordLength === 0) {
    return {
      password_length: 0,
      lowercase_count: 0,
      uppercase_count: 0,
      digit_count: 0,
      symbol_count: 0,
      unique_character_count: 0,
      repeated_character_count: 0,
      repeated_substring_count: 0,
      sequential_character_count: 0,
      zxcvbn_score: 0,
      log10_estimated_guesses: 0,
      empirical_character_entropy: 0,
      character_pool_entropy_estimate: 0,
    };
  }

  const lowercaseCount = (password.match(/[a-z]/g) || []).length;
  const uppercaseCount = (password.match(/[A-Z]/g) || []).length;
  const digitCount = (password.match(/[0-9]/g) || []).length;
  const symbolCount = (password.match(/[^a-zA-Z0-9]/g) || []).length;

  const uniqueChars = new Set(password.split(''));
  const uniqueCount = uniqueChars.size;
  const repeatedCharCount = passwordLength - uniqueCount;

  // Repeated substring count (length >= 2)
  let repeatedSubstringCount = 0;
  for (let len = 2; len <= Math.floor(passwordLength / 2); len++) {
    for (let i = 0; i <= passwordLength - 2 * len; i++) {
      const sub = password.slice(i, i + len);
      const rest = password.slice(i + len);
      if (rest.includes(sub)) {
        repeatedSubstringCount++;
      }
    }
  }

  // Sequential character count (e.g. abc, 123, 321, cba)
  let sequentialCount = 0;
  for (let i = 0; i < passwordLength - 1; i++) {
    const code1 = password.charCodeAt(i);
    const code2 = password.charCodeAt(i + 1);
    if (Math.abs(code1 - code2) === 1) {
      sequentialCount++;
    }
  }

  // zxcvbn evaluation
  const zxcvbnRes = zxcvbn(password);
  const zxcvbnScore = zxcvbnRes.score;
  const estimatedGuesses = zxcvbnRes.guesses || 1;
  const log10EstimatedGuesses = Math.log10(Math.max(1, estimatedGuesses) + 1);

  // Empirical Shannon Character Entropy
  const freqMap: Record<string, number> = {};
  for (const char of password) {
    freqMap[char] = (freqMap[char] || 0) + 1;
  }
  let empiricalEntropy = 0;
  for (const char in freqMap) {
    const p = freqMap[char] / passwordLength;
    empiricalEntropy -= p * Math.log2(p);
  }

  // Character Pool Entropy Estimate (Length * log2(Pool Size))
  let poolSize = 0;
  if (lowercaseCount > 0) poolSize += 26;
  if (uppercaseCount > 0) poolSize += 26;
  if (digitCount > 0) poolSize += 10;
  if (symbolCount > 0) poolSize += 32;

  const poolEntropyEstimate = poolSize > 0 ? passwordLength * Math.log2(poolSize) : 0;

  return {
    password_length: passwordLength,
    lowercase_count: lowercaseCount,
    uppercase_count: uppercaseCount,
    digit_count: digitCount,
    symbol_count: symbolCount,
    unique_character_count: uniqueCount,
    repeated_character_count: repeatedCharCount,
    repeated_substring_count: repeatedSubstringCount,
    sequential_character_count: sequentialCount,
    zxcvbn_score: zxcvbnScore,
    log10_estimated_guesses: parseFloat(log10EstimatedGuesses.toFixed(4)),
    empirical_character_entropy: parseFloat(empiricalEntropy.toFixed(4)),
    character_pool_entropy_estimate: parseFloat(poolEntropyEstimate.toFixed(4)),
  };
}
