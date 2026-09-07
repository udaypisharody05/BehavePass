# Synthetic baseline analysis

> **Synthetic-data disclaimer:** These experiments evaluate the technical feasibility of the BehavePass pipeline using synthetic behavioral data and should not be interpreted as validation on real-world users.

## Dataset and target

The analysis uses the unchanged `data/synthetic/behavepass_synthetic.csv`: 15,000 generated sessions, 34 columns, 240 synthetic participant identifiers, no missing values, and no duplicate rows. The continuous regression target is `log10_estimated_guesses`, calculated by the existing frontend as `log10(max(zxcvbn guesses, 1) + 1)`.

Constant or near-constant columns are `source`, `synthetic_seed`, `task_type`, and `pause_threshold_ms`. They are metadata and never model inputs.

## Leakage audit and feature groups

Never-model metadata:

```text
session_id, source, synthetic_seed, participant_code, typing_profile,
task_type, pause_threshold_ms
```

Safe static features (11):

```text
password_length, lowercase_count, uppercase_count, digit_count,
symbol_count, unique_character_count, repeated_character_count,
repeated_substring_count, sequential_character_count,
empirical_character_entropy, character_pool_entropy_estimate
```

Behavioral features (14):

```text
total_typing_duration, total_key_presses, average_dwell_time,
dwell_time_std, average_flight_time, flight_time_std,
average_press_latency, longest_interkey_delay, pause_count,
total_pause_duration, backspace_count, backspace_rate,
correction_burst_count, characters_per_second
```

`zxcvbn_score` is target-adjacent: the score and guess count underlying the target are outputs of the same zxcvbn evaluation. It is therefore excluded from the defensible baseline and included only in explicitly named diagnostic comparisons. The entropy fields are strongly target-correlated but are independently calculated password descriptors, not transformations of zxcvbn guesses; they remain in the safe static group.

The strongest absolute target correlations were character-pool entropy (0.954), password length (0.944), unique-character count (0.923), total keypresses (0.911), empirical entropy (0.897), and zxcvbn score (0.866). Total keypresses is a behavioral field but also acts as a strong password-length proxy in this generator. This explains much of behavioral-only performance and must not be mistaken for real behavioral evidence.

## Split and preprocessing

A fixed-seed `GroupShuffleSplit` creates one 80/20 participant-grouped split reused for every experiment:

- Training: 11,971 sessions from 192 synthetic participants
- Test: 3,029 sessions from 48 synthetic participants
- Participant overlap: zero

Participant grouping was selected because each synthetic participant has repeated sessions. Grouping prevents identity-specific session patterns from crossing train and test. `typing_profile` is neither an input nor a grouping key. Ridge scaling is fitted only on training rows through an sklearn `Pipeline`; tree and dummy models require no scaling.

## Model results

Held-out results for the main Random Forest comparison:

| Feature group | Features | MAE | RMSE | R² |
|---|---:|---:|---:|---:|
| Static safe | 11 | 0.3113 | 0.8106 | 0.9619 |
| Behavioral only | 14 | 0.7813 | 1.3602 | 0.8928 |
| Static + behavioral safe | 25 | 0.3445 | 0.8641 | 0.9567 |
| Static with zxcvbn | 12 | 0.0822 | 0.2118 | 0.9974 |
| Static + behavioral with zxcvbn | 26 | 0.0906 | 0.2281 | 0.9970 |

Baseline context:

| Model/group | MAE | RMSE | R² |
|---|---:|---:|---:|
| Dummy mean | 3.2820 | 4.1543 | -0.0002 |
| Dummy median | 3.2810 | 4.1945 | -0.0196 |
| Ridge, static safe | 0.7784 | 1.1872 | 0.9183 |
| Ridge, behavioral | 0.9526 | 1.3554 | 0.8935 |
| Ridge, combined safe | 0.7807 | 1.1888 | 0.9181 |

All complete results are in [`ml/results/synthetic_baseline_results.csv`](../ml/results/synthetic_baseline_results.csv).

## Behavioral contribution

Against safe static-only Random Forest, adding behavioral features:

- worsened MAE by 0.0332 (10.65%)
- worsened RMSE by 0.0535 (6.60%)
- reduced R² by 0.0052 (0.54% relative)

Thus this dataset provides no measured improvement from adding behavior to the best safe static baseline. Behavioral-only R² is high (0.893), but largely because generated timing totals, keypress count, pauses, and corrections were designed to correlate with password length and difficulty.

Adding zxcvbn score to static features reduced RMSE by 73.86% and MAE by 73.60%, reaching R² 0.9974. This very large jump is consistent with procedural target leakage/target adjacency rather than new independent predictive information. zxcvbn score must remain excluded from the defensible model.

## Permutation importance

Held-out permutation importance for the safe combined Random Forest is dominated by static fields:

| Rank | Feature | Type | RMSE increase |
|---:|---|---|---:|
| 1 | `character_pool_entropy_estimate` | Static | 2.5689 |
| 2 | `password_length` | Static | 1.2547 |
| 3 | `empirical_character_entropy` | Static | 0.2580 |
| 4 | `digit_count` | Static | 0.2043 |
| 5 | `unique_character_count` | Static | 0.1657 |

The largest behavioral importances were `characters_per_second` (0.0038), `total_typing_duration` (0.0030), and `flight_time_std` (0.0021). These values are tiny relative to the leading static fields, and some behavioral features had zero or slightly negative permutation importance.

## Scientific answers

1. **Static prediction:** safe static features predict the synthetic target very well (Random Forest R² 0.9619).
2. **Behavior-only prediction:** behavioral features predict much of the synthetic target (R² 0.8928), primarily through intentionally generated correlations and password-length proxies.
3. **Combined prediction:** safe behavior plus static features did not improve the best static-only model; all three headline metrics worsened slightly.
4. **Behavioral contributors:** characters per second, total duration, and flight-time variability ranked highest, but their incremental contribution was very small.
5. **zxcvbn leakage:** yes. Because zxcvbn score and the target originate from the same zxcvbn call, the score is target-adjacent and its dramatic metric improvement is not defensible evidence.
6. **Defensible baseline:** safe static features without zxcvbn score, using the Random Forest baseline and participant-grouped split.
7. **Neural-network justification:** no. Synthetic aggregate results do not show incremental behavioral value and cannot justify a neural architecture. Sequence models should wait for sufficient real, consented creation-time data and an evaluation design that tests incremental behavior beyond static features.

## Figures

- [Target distribution](../ml/results/figures/target_distribution.svg)
- [Selected correlation heatmap](../ml/results/figures/selected_correlation_heatmap.svg)
- [Feature-group RMSE comparison](../ml/results/figures/model_performance_rmse.svg)
- [Top permutation importances](../ml/results/figures/top_feature_importance.svg)
- [Actual versus predicted](../ml/results/figures/actual_vs_predicted.svg)

## Limitations and next step

These metrics validate code paths and expose generator relationships; they do not estimate real-world generalization. The target is purely static, participant identities and profiles are synthetic, and several behavioral values intentionally depend on password difficulty. The next step should be an experiment manifest and power/data-collection plan for real creation-time sessions, with a preregistered participant-grouped evaluation and static-only versus static-plus-behavior comparison. No neural model should be implemented yet.
