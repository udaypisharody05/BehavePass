# Synthetic BehavePass dataset

## Purpose and provenance

BehavePass currently lacks enough collected sessions for proof-of-concept model development. The generator therefore creates explicitly **synthetic** typing sessions for pipeline construction, schema validation, and preliminary model debugging. These rows were not collected from real users and must not be presented as real participant observations.

Synthetic results are not evidence of real-world password behavior, model accuracy, demographic performance, or security effectiveness. A model developed with this data must later be evaluated using appropriately consented, independently collected data.

## Generate and validate

From the repository root, with backend Python and frontend npm dependencies installed:

```text
python scripts/generate_synthetic_dataset.py --samples 15000 --seed 42 --output data/synthetic/behavepass_synthetic.csv
```

The command validates the rows before writing them and prints a concise summary. Validate an existing file with:

```text
python scripts/generate_synthetic_dataset.py --samples 15000 --output data/synthetic/behavepass_synthetic.csv --validate-only
```

Generated files under `data/` are ignored by Git.

## Generation assumptions

Each session starts with a temporary password-like string that is discarded before CSV output. The existing frontend `calculateStaticFeatures` implementation and zxcvbn integration derive static fields and the established continuous target, `log10(max(guesses, 1) + 1)`.

Four equally likely synthetic profiles parameterize bounded timing distributions:

| Profile | Mean dwell | Mean flight | Variability | Pause probability | Base backspace probability |
|---|---:|---:|---|---:|---:|
| Fast | 68 ms | 55 ms | Low | 1.8% | 2.5% |
| Average | 92 ms | 105 ms | Moderate | 3.5% | 4.5% |
| Slow | 130 ms | 185 ms | Moderate | 6.0% | 7.0% |
| Inconsistent | 105 ms | 125 ms | High | 9.5% | 8.5% |

Dwell times use clipped log-normal distributions. Flight times use clipped normal distributions and may be negative for overlapping keys. Pauses use a bounded log-normal addition when press-to-press latency crosses the existing 500 ms threshold. Longer and more complex passwords modestly increase pause/correction probabilities; corrections add physical keypresses and therefore extend duration. Noise prevents deterministic relationships.

Password generation mixes weak common patterns with increasingly long and diverse random strings. The mixture encourages—but does not guarantee—greater diversity and zxcvbn strength at higher complexity.

## Output fields

The CSV mirrors current BehavePass names: static composition, zxcvbn score, `log10_estimated_guesses`, entropy fields, total keypress/duration metrics, dwell/flight averages and standard deviations, press latency, longest delay, pause totals, backspace/correction metrics, and characters per second. Additional metadata is limited to synthetic source, generation seed, anonymous synthetic participant, profile, and synthetic task type.

No plaintext password, key sequence, or purported real-user identity is written.

## Validation

Validation checks row count, exact schema, missing values, provenance, profile names, zxcvbn range, finite/non-negative aggregate durations, realistic timing bounds, feature variance, target balance, and absence of plaintext-password columns.

## Limitations

The generator encodes assumptions rather than learned human behavior. Profile boundaries, correction behavior, and feature correlations are simplified. The zxcvbn target is determined by static password content; behavioral timing provides correlated session context but does not turn synthetic observations into independent real-world evidence. Synthetic participant codes do not represent people, and generated sessions must not be used for claims about actual users.
