from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .features import (
    BEHAVIORAL_FEATURES,
    FEATURE_GROUPS,
    TARGET,
    validate_feature_groups,
)
from .svg_plots import bars, heatmap, histogram, scatter


def participant_grouped_split(data: pd.DataFrame, seed: int = 42) -> tuple[np.ndarray, np.ndarray]:
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=seed)
    train, test = next(splitter.split(data, groups=data["participant_code"]))
    return train, test


def build_model(name: str, seed: int):
    if name == "dummy_mean":
        return DummyRegressor(strategy="mean")
    if name == "dummy_median":
        return DummyRegressor(strategy="median")
    if name == "ridge":
        return Pipeline([("scale", StandardScaler()), ("model", Ridge(alpha=1.0))])
    if name == "random_forest":
        return RandomForestRegressor(
            n_estimators=160,
            min_samples_leaf=3,
            max_features=0.75,
            n_jobs=-1,
            random_state=seed,
        )
    raise ValueError(f"unknown model: {name}")


def _metrics(actual: pd.Series, predicted: np.ndarray) -> dict[str, float]:
    return {
        "mae": mean_absolute_error(actual, predicted),
        "rmse": mean_squared_error(actual, predicted) ** 0.5,
        "r2": r2_score(actual, predicted),
    }


def run_analysis(data_path: Path, results_dir: Path, seed: int = 42) -> dict[str, object]:
    data = pd.read_csv(data_path)
    validate_feature_groups(set(data.columns))
    train_index, test_index = participant_grouped_split(data, seed)
    train = data.iloc[train_index]
    test = data.iloc[test_index]
    if set(train["participant_code"]) & set(test["participant_code"]):
        raise RuntimeError("participant leakage detected in split")

    numeric = data.select_dtypes(include="number")
    correlations = numeric.corr(numeric_only=True)
    target_correlations = correlations[TARGET].drop(TARGET).sort_values(key=abs, ascending=False)
    near_constant = [
        column for column in data.columns
        if data[column].nunique(dropna=False) <= 1
        or data[column].value_counts(normalize=True, dropna=False).iloc[0] >= 0.995
    ]
    eda = {
        "rows": len(data),
        "columns": len(data.columns),
        "column_types": {name: str(dtype) for name, dtype in data.dtypes.items()},
        "missing_values": int(data.isna().sum().sum()),
        "duplicate_rows": int(data.duplicated().sum()),
        "near_constant_features": near_constant,
        "target_descriptive_statistics": data[TARGET].describe().to_dict(),
        "target_correlations": target_correlations.to_dict(),
        "typing_profile_distribution": data["typing_profile"].value_counts().to_dict(),
        "zxcvbn_score_distribution": data["zxcvbn_score"].value_counts().sort_index().to_dict(),
        "train_rows": len(train),
        "test_rows": len(test),
        "train_participants": train["participant_code"].nunique(),
        "test_participants": test["participant_code"].nunique(),
        "participant_overlap": 0,
    }

    results = []
    fitted: dict[tuple[str, str], object] = {}
    predictions: dict[tuple[str, str], np.ndarray] = {}
    for group_name, features in FEATURE_GROUPS.items():
        for model_name in ("dummy_mean", "dummy_median", "ridge", "random_forest"):
            model = build_model(model_name, seed)
            model.fit(train[features], train[TARGET])
            predicted = model.predict(test[features])
            results.append({
                "feature_group": group_name,
                "model": model_name,
                "feature_count": len(features),
                "train_samples": len(train),
                "test_samples": len(test),
                **_metrics(test[TARGET], predicted),
            })
            fitted[(group_name, model_name)] = model
            predictions[(group_name, model_name)] = predicted
    results_frame = pd.DataFrame(results).sort_values(["feature_group", "rmse"])

    defensible = results_frame[results_frame["feature_group"].isin(["static_safe", "behavioral", "combined_safe"])]
    best_row = defensible.loc[defensible["rmse"].idxmin()]
    best_key = (str(best_row["feature_group"]), str(best_row["model"]))
    importance_model = fitted[("combined_safe", "random_forest")]
    sample_test = test.sample(min(2000, len(test)), random_state=seed)
    importance = permutation_importance(
        importance_model,
        sample_test[FEATURE_GROUPS["combined_safe"]],
        sample_test[TARGET],
        scoring="neg_root_mean_squared_error",
        n_repeats=5,
        random_state=seed,
        n_jobs=-1,
    )
    importance_frame = pd.DataFrame({
        "feature": FEATURE_GROUPS["combined_safe"],
        "importance_mean": importance.importances_mean,
        "importance_std": importance.importances_std,
        "feature_type": ["behavioral" if item in BEHAVIORAL_FEATURES else "static" for item in FEATURE_GROUPS["combined_safe"]],
    }).sort_values("importance_mean", ascending=False)

    results_dir.mkdir(parents=True, exist_ok=True)
    results_frame.to_csv(results_dir / "synthetic_baseline_results.csv", index=False)
    importance_frame.to_csv(results_dir / "synthetic_feature_importance.csv", index=False)
    (results_dir / "synthetic_eda.json").write_text(json.dumps(eda, indent=2, sort_keys=True), encoding="utf-8")

    figures = results_dir / "figures"
    histogram(figures / "target_distribution.svg", data[TARGET].tolist(), "Synthetic target distribution", TARGET)
    selected = [TARGET, "zxcvbn_score", "password_length", "character_pool_entropy_estimate", "total_typing_duration", "average_flight_time", "pause_count", "backspace_count"]
    selected_corr = data[selected].corr()
    heatmap(figures / "selected_correlation_heatmap.svg", selected, selected_corr.values.tolist(), "Selected synthetic feature correlations")
    comparison_groups = ["static_safe", "behavioral", "combined_safe", "static_with_zxcvbn", "combined_with_zxcvbn"]
    rf_rows = results_frame[results_frame["model"] == "random_forest"].set_index("feature_group")
    bars(figures / "model_performance_rmse.svg", comparison_groups, [float(rf_rows.loc[name, "rmse"]) for name in comparison_groups], "Random forest feature-group comparison", "Held-out RMSE")
    top = importance_frame.head(12).iloc[::-1]
    bars(figures / "top_feature_importance.svg", top["feature"].tolist(), top["importance_mean"].clip(lower=0).tolist(), "Permutation importance: defensible combined baseline", "RMSE increase after permutation")
    scatter(figures / "actual_vs_predicted.svg", test[TARGET].tolist(), predictions[best_key].tolist(), f"Actual vs predicted: {best_key[0]} / {best_key[1]}")

    output = {
        "eda": eda,
        "best_defensible": best_row.to_dict(),
        "top_importance": importance_frame.head(15).to_dict(orient="records"),
        "results_file": str((results_dir / "synthetic_baseline_results.csv").resolve()),
    }
    print(json.dumps(output, indent=2, default=float))
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Leakage-aware synthetic BehavePass baselines")
    parser.add_argument("--data", type=Path, default=Path("data/synthetic/behavepass_synthetic.csv"))
    parser.add_argument("--results-dir", type=Path, default=Path("ml/results"))
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    run_analysis(args.data, args.results_dir, args.seed)


if __name__ == "__main__":
    main()
