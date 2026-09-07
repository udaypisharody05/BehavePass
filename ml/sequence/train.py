from __future__ import annotations

import argparse
import copy
import csv
import json
import math
import random
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from torch import nn
from torch.utils.data import DataLoader

from ml.analysis.svg_plots import bars, lines, scatter
from ml.sequence.models import build_neural_model
from ml.sequence.preprocessing import (
    SEQUENCE_FEATURES,
    SequenceDataset,
    collate_sequences,
    fit_normalization,
    load_sequences,
    split_participants,
)


MODEL_NAMES = ("behavior_bilstm", "static_mlp", "fusion_bilstm")


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True)


def _loader(dataset, batch_size: int, shuffle: bool, seed: int) -> DataLoader:
    generator = torch.Generator().manual_seed(seed)
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        collate_fn=collate_sequences,
        generator=generator,
        num_workers=0,
    )


def _loss(model, loader, criterion, optimizer=None) -> float:
    training = optimizer is not None
    model.train(training)
    total = 0.0
    count = 0
    context = torch.enable_grad() if training else torch.no_grad()
    with context:
        for sequence, lengths, _mask, static, targets, _ids in loader:
            if training:
                optimizer.zero_grad(set_to_none=True)
            predicted = model(sequence, lengths, static)
            loss = criterion(predicted, targets)
            if training:
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
                optimizer.step()
            total += float(loss.detach()) * len(targets)
            count += len(targets)
    return total / count


def _predict(model, loader, target_mean: float, target_std: float):
    model.eval()
    predicted, actual, ids = [], [], []
    with torch.no_grad():
        for sequence, lengths, _mask, static, targets, session_ids in loader:
            output = model(sequence, lengths, static)
            predicted.extend((output.numpy() * target_std + target_mean).tolist())
            actual.extend((targets.numpy() * target_std + target_mean).tolist())
            ids.extend(session_ids)
    return np.asarray(actual), np.asarray(predicted), ids


def train_models(
    aggregate_path: Path,
    sequence_path: Path,
    results_dir: Path,
    checkpoint_dir: Path,
    seed: int = 42,
    epochs: int = 18,
    batch_size: int = 128,
    patience: int = 4,
) -> list[dict[str, object]]:
    set_seed(seed)
    torch.set_num_threads(min(4, torch.get_num_threads()))
    aggregate = pd.read_csv(aggregate_path)
    sequences = load_sequences(sequence_path)
    train, validation, test = split_participants(aggregate, seed)
    normalization = fit_normalization(train, sequences, seed, validation, test)
    results_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    normalization.save(results_dir / "sequence_preprocessing.json")
    train_data = SequenceDataset(train, sequences, normalization)
    validation_data = SequenceDataset(validation, sequences, normalization)
    test_data = SequenceDataset(test, sequences, normalization)
    validation_loader = _loader(validation_data, batch_size, False, seed)
    test_loader = _loader(test_data, batch_size, False, seed)
    criterion = nn.HuberLoss(delta=1.0)
    results = []
    histories: dict[str, dict[str, list[float]]] = {}
    combined_actual = combined_predicted = None

    for model_index, model_name in enumerate(MODEL_NAMES):
        set_seed(seed + model_index)
        model = build_neural_model(model_name)
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-5)
        train_loader = _loader(train_data, batch_size, True, seed + model_index)
        best_loss = math.inf
        best_state = None
        stale = 0
        history = {"train_loss": [], "validation_loss": []}
        for epoch in range(epochs):
            train_loss = _loss(model, train_loader, criterion, optimizer)
            validation_loss = _loss(model, validation_loader, criterion)
            history["train_loss"].append(train_loss)
            history["validation_loss"].append(validation_loss)
            if validation_loss < best_loss - 1e-5:
                best_loss = validation_loss
                best_state = copy.deepcopy(model.state_dict())
                stale = 0
            else:
                stale += 1
                if stale >= patience:
                    break
        if best_state is None:
            raise RuntimeError("training produced no checkpoint")
        model.load_state_dict(best_state)
        checkpoint_path = checkpoint_dir / f"{model_name}.pt"
        torch.save({
            "model_name": model_name,
            "state_dict": best_state,
            "sequence_size": len(SEQUENCE_FEATURES),
            "static_size": len(normalization.static_features),
            "hidden_size": 32,
            "seed": seed,
        }, checkpoint_path)
        actual, predicted, ids = _predict(
            model, test_loader, normalization.target_mean, normalization.target_std
        )
        result = {
            "model": model_name,
            "mae": mean_absolute_error(actual, predicted),
            "rmse": mean_squared_error(actual, predicted) ** 0.5,
            "r2": r2_score(actual, predicted),
            "train_samples": len(train),
            "validation_samples": len(validation),
            "test_samples": len(test),
            "epochs_trained": len(history["train_loss"]),
            "best_validation_loss": best_loss,
            "checkpoint": checkpoint_path.as_posix(),
        }
        results.append(result)
        histories[model_name] = history
        if model_name == "fusion_bilstm":
            combined_actual, combined_predicted = actual, predicted

    baseline = pd.read_csv(results_dir / "synthetic_baseline_results.csv")
    baseline_row = baseline[
        (baseline["feature_group"] == "static_safe")
        & (baseline["model"] == "random_forest")
    ].iloc[0]
    results.append({
        "model": "static_random_forest",
        "mae": baseline_row["mae"],
        "rmse": baseline_row["rmse"],
        "r2": baseline_row["r2"],
        "train_samples": baseline_row["train_samples"],
        "validation_samples": 0,
        "test_samples": baseline_row["test_samples"],
        "epochs_trained": 0,
        "best_validation_loss": "",
        "checkpoint": "",
    })
    with (results_dir / "neural_experiment_results.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    (results_dir / "neural_training_history.json").write_text(
        json.dumps(histories, indent=2), encoding="utf-8"
    )
    figures = results_dir / "figures"
    loss_series = {}
    for name, history in histories.items():
        loss_series[f"{name} train"] = history["train_loss"]
        loss_series[f"{name} validation"] = history["validation_loss"]
    lines(figures / "neural_training_loss.svg", loss_series, "Neural training and validation loss", "Normalized Huber loss")
    bars(figures / "neural_rmse_comparison.svg", [str(row["model"]) for row in results], [float(row["rmse"]) for row in results], "Participant-held-out model comparison", "RMSE")
    scatter(figures / "fusion_actual_vs_predicted.svg", combined_actual.tolist(), combined_predicted.tolist(), "BiLSTM fusion: actual vs predicted")
    print(json.dumps({
        "split": {
            "train": len(train), "validation": len(validation), "test": len(test),
            "train_participants": train["participant_code"].nunique(),
            "validation_participants": validation["participant_code"].nunique(),
            "test_participants": test["participant_code"].nunique(),
        },
        "results": results,
    }, indent=2, default=float))
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Train CPU-friendly BehavePass sequence models")
    parser.add_argument("--aggregate", type=Path, required=True)
    parser.add_argument("--sequences", type=Path, required=True)
    parser.add_argument("--results-dir", type=Path, default=Path("ml/results"))
    parser.add_argument("--checkpoint-dir", type=Path, default=Path("ml/checkpoints"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--epochs", type=int, default=18)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--patience", type=int, default=4)
    args = parser.parse_args()
    train_models(
        args.aggregate, args.sequences, args.results_dir, args.checkpoint_dir,
        args.seed, args.epochs, args.batch_size, args.patience,
    )


if __name__ == "__main__":
    main()
