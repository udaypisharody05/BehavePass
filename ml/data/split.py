import random
from collections.abc import Iterable

from .schemas import CanonicalSample


def grouped_password_split(
    samples: Iterable[CanonicalSample],
    train_fraction: float = 0.70,
    validation_fraction: float = 0.15,
    seed: int = 42,
) -> dict[str, list[CanonicalSample]]:
    if not 0 < train_fraction < 1:
        raise ValueError("train_fraction must be between 0 and 1")
    if not 0 <= validation_fraction < 1:
        raise ValueError("validation_fraction must be between 0 and 1")
    if train_fraction + validation_fraction >= 1:
        raise ValueError("train and validation fractions must sum to less than 1")

    materialized = list(samples)
    password_ids = sorted({sample.password_id for sample in materialized})
    random.Random(seed).shuffle(password_ids)
    train_end = int(len(password_ids) * train_fraction)
    validation_end = train_end + int(len(password_ids) * validation_fraction)
    groups = {
        "train": set(password_ids[:train_end]),
        "validation": set(password_ids[train_end:validation_end]),
        "test": set(password_ids[validation_end:]),
    }
    return {
        split: [sample for sample in materialized if sample.password_id in ids]
        for split, ids in groups.items()
    }
