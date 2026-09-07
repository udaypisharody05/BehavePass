"""Static features matching the portable subset of the frontend extractor.

The repository's zxcvbn integration is TypeScript/browser code. This module
keeps its non-zxcvbn field definitions aligned for offline adapters; zxcvbn
outputs remain explicitly unavailable rather than silently substituting a
different implementation.
"""

from functools import lru_cache
import math

from .schemas import StaticFeatures


@lru_cache(maxsize=None)
def extract_static_features(password: str) -> StaticFeatures:
    length = len(password)
    lower = sum(char.isascii() and char.islower() for char in password)
    upper = sum(char.isascii() and char.isupper() for char in password)
    digits = sum(char.isascii() and char.isdigit() for char in password)
    symbols = length - lower - upper - digits
    unique = len(set(password))
    repeated_substrings = 0
    for size in range(2, length // 2 + 1):
        for start in range(0, length - 2 * size + 1):
            substring = password[start : start + size]
            if substring in password[start + size :]:
                repeated_substrings += 1
    sequential = sum(
        abs(ord(password[index + 1]) - ord(password[index])) == 1
        for index in range(max(0, length - 1))
    )
    frequencies = {char: password.count(char) for char in set(password)}
    empirical_entropy = -sum(
        (count / length) * math.log2(count / length)
        for count in frequencies.values()
    ) if length else 0.0
    pool_size = (
        (26 if lower else 0)
        + (26 if upper else 0)
        + (10 if digits else 0)
        + (32 if symbols else 0)
    )
    return StaticFeatures(
        password_length=length,
        lowercase_count=lower,
        uppercase_count=upper,
        digit_count=digits,
        symbol_count=symbols,
        unique_character_count=unique,
        repeated_character_count=length - unique,
        repeated_substring_count=repeated_substrings,
        sequential_character_count=sequential,
        empirical_character_entropy=empirical_entropy,
        character_pool_entropy_estimate=(
            length * math.log2(pool_size) if pool_size else 0.0
        ),
    )
