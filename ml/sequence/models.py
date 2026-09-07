from __future__ import annotations

import torch
from torch import nn
from torch.nn.utils.rnn import pack_padded_sequence


class BiLSTMEncoder(nn.Module):
    def __init__(self, input_size: int = 6, hidden_size: int = 32, layers: int = 1, dropout: float = 0.0):
        super().__init__()
        self.hidden_size = hidden_size
        self.lstm = nn.LSTM(
            input_size,
            hidden_size,
            num_layers=layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if layers > 1 else 0.0,
        )

    @property
    def output_size(self) -> int:
        return self.hidden_size * 2

    def forward(self, sequence: torch.Tensor, lengths: torch.Tensor) -> torch.Tensor:
        packed = pack_padded_sequence(
            sequence, lengths.cpu(), batch_first=True, enforce_sorted=False
        )
        _, (hidden, _) = self.lstm(packed)
        return torch.cat((hidden[-2], hidden[-1]), dim=1)


class SequenceRegressor(nn.Module):
    def __init__(self, sequence_size: int = 6, hidden_size: int = 32):
        super().__init__()
        self.encoder = BiLSTMEncoder(sequence_size, hidden_size)
        self.head = nn.Sequential(nn.Linear(hidden_size * 2, 32), nn.ReLU(), nn.Linear(32, 1))

    def forward(self, sequence, lengths, static):
        return self.head(self.encoder(sequence, lengths)).squeeze(1)


class StaticRegressor(nn.Module):
    def __init__(self, static_size: int = 11):
        super().__init__()
        self.head = nn.Sequential(
            nn.Linear(static_size, 32), nn.ReLU(), nn.Linear(32, 16), nn.ReLU(), nn.Linear(16, 1)
        )

    def forward(self, sequence, lengths, static):
        return self.head(static).squeeze(1)


class FusionRegressor(nn.Module):
    def __init__(self, sequence_size: int = 6, static_size: int = 11, hidden_size: int = 32):
        super().__init__()
        self.encoder = BiLSTMEncoder(sequence_size, hidden_size)
        self.static_projection = nn.Sequential(nn.Linear(static_size, 16), nn.ReLU())
        self.head = nn.Sequential(
            nn.Linear(hidden_size * 2 + 16, 32), nn.ReLU(), nn.Linear(32, 1)
        )

    def forward(self, sequence, lengths, static):
        behavior = self.encoder(sequence, lengths)
        static_embedding = self.static_projection(static)
        return self.head(torch.cat((behavior, static_embedding), dim=1)).squeeze(1)


def build_neural_model(name: str, sequence_size: int = 6, static_size: int = 11, hidden_size: int = 32):
    if name == "behavior_bilstm":
        return SequenceRegressor(sequence_size, hidden_size)
    if name == "static_mlp":
        return StaticRegressor(static_size)
    if name == "fusion_bilstm":
        return FusionRegressor(sequence_size, static_size, hidden_size)
    raise ValueError(f"unknown neural model: {name}")
