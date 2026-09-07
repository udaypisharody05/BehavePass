from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import GroupShuffleSplit
from torch.nn.utils.rnn import pad_sequence
from torch.utils.data import Dataset

from ml.analysis.analyze_synthetic_dataset import participant_grouped_split
from ml.analysis.features import STATIC_FEATURES, TARGET


SEQUENCE_FEATURES = [
    "dwell_time",
    "flight_time",
    "press_to_press_latency",
    "normalized_position",
    "is_pause",
    "is_backspace",
]


@dataclass
class NormalizationMetadata:
    sequence_features: list[str]
    sequence_mean: list[float]
    sequence_std: list[float]
    static_features: list[str]
    static_mean: list[float]
    static_std: list[float]
    target_mean: float
    target_std: float
    seed: int
    train_participants: list[str]
    validation_participants: list[str]
    test_participants: list[str]

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "NormalizationMetadata":
        return cls(**json.loads(path.read_text(encoding="utf-8")))


def load_sequences(path: Path) -> dict[str, list[dict[str, object]]]:
    output = {}
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            session_id = record["session_id"]
            if session_id in output:
                raise ValueError(f"duplicate sequence session_id: {session_id}")
            output[session_id] = record["events"]
    return output


def split_participants(
    aggregate: pd.DataFrame, seed: int = 42
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train_validation_index, test_index = participant_grouped_split(aggregate, seed)
    train_validation = aggregate.iloc[train_validation_index].reset_index(drop=True)
    test = aggregate.iloc[test_index].reset_index(drop=True)
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=seed + 1)
    train_index, validation_index = next(
        splitter.split(train_validation, groups=train_validation["participant_code"])
    )
    train = train_validation.iloc[train_index].reset_index(drop=True)
    validation = train_validation.iloc[validation_index].reset_index(drop=True)
    groups = [
        set(train["participant_code"]),
        set(validation["participant_code"]),
        set(test["participant_code"]),
    ]
    if groups[0] & groups[1] or groups[0] & groups[2] or groups[1] & groups[2]:
        raise RuntimeError("participant leakage detected")
    return train, validation, test


def _event_matrix(events: list[dict[str, object]]) -> np.ndarray:
    rows = []
    for event in events:
        rows.append([
            0.0 if event[name] is None else float(event[name])
            for name in SEQUENCE_FEATURES
        ])
    return np.asarray(rows, dtype=np.float32)


def fit_normalization(
    train: pd.DataFrame,
    sequences: dict[str, list[dict[str, object]]],
    seed: int,
    validation: pd.DataFrame,
    test: pd.DataFrame,
) -> NormalizationMetadata:
    event_rows = np.concatenate(
        [_event_matrix(sequences[item]) for item in train["session_id"]], axis=0
    )
    sequence_mean = event_rows.mean(axis=0)
    sequence_std = event_rows.std(axis=0)
    sequence_std[sequence_std < 1e-8] = 1.0
    static_values = train[STATIC_FEATURES].to_numpy(dtype=np.float32)
    static_mean = static_values.mean(axis=0)
    static_std = static_values.std(axis=0)
    static_std[static_std < 1e-8] = 1.0
    target_mean = float(train[TARGET].mean())
    target_std = float(train[TARGET].std(ddof=0)) or 1.0
    return NormalizationMetadata(
        sequence_features=SEQUENCE_FEATURES,
        sequence_mean=sequence_mean.tolist(),
        sequence_std=sequence_std.tolist(),
        static_features=STATIC_FEATURES,
        static_mean=static_mean.tolist(),
        static_std=static_std.tolist(),
        target_mean=target_mean,
        target_std=target_std,
        seed=seed,
        train_participants=sorted(train["participant_code"].unique().tolist()),
        validation_participants=sorted(validation["participant_code"].unique().tolist()),
        test_participants=sorted(test["participant_code"].unique().tolist()),
    )


class SequenceDataset(Dataset):
    def __init__(
        self,
        rows: pd.DataFrame,
        sequences: dict[str, list[dict[str, object]]],
        normalization: NormalizationMetadata,
    ) -> None:
        missing = set(rows["session_id"]) - set(sequences)
        if missing:
            raise ValueError(f"missing sequences for {len(missing)} aggregate sessions")
        self.rows = rows.reset_index(drop=True)
        self.sequences = sequences
        self.seq_mean = np.asarray(normalization.sequence_mean, dtype=np.float32)
        self.seq_std = np.asarray(normalization.sequence_std, dtype=np.float32)
        self.static_mean = np.asarray(normalization.static_mean, dtype=np.float32)
        self.static_std = np.asarray(normalization.static_std, dtype=np.float32)
        self.target_mean = normalization.target_mean
        self.target_std = normalization.target_std
        self.session_ids = self.rows["session_id"].tolist()
        self.sequence_tensors = [
            torch.from_numpy(
                ((_event_matrix(sequences[session_id]) - self.seq_mean) / self.seq_std).astype(np.float32)
            )
            for session_id in self.session_ids
        ]
        static_values = self.rows[STATIC_FEATURES].to_numpy(dtype=np.float32)
        self.static_tensor = torch.from_numpy(
            ((static_values - self.static_mean) / self.static_std).astype(np.float32)
        )
        targets = (self.rows[TARGET].to_numpy(dtype=np.float32) - self.target_mean) / self.target_std
        self.target_tensor = torch.from_numpy(targets.astype(np.float32))

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int):
        return (
            self.sequence_tensors[index],
            self.static_tensor[index],
            self.target_tensor[index],
            self.session_ids[index],
        )


def collate_sequences(batch):
    sequences, static, targets, session_ids = zip(*batch)
    lengths = torch.tensor([len(item) for item in sequences], dtype=torch.long)
    padded = pad_sequence(sequences, batch_first=True, padding_value=0.0)
    mask = torch.arange(padded.shape[1]).unsqueeze(0) < lengths.unsqueeze(1)
    return padded, lengths, mask, torch.stack(static), torch.stack(targets), list(session_ids)
