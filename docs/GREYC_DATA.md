# GREYC-Web adapter

GREYC-Web provides real keystroke-dynamics captures for user-selected passwords. It is useful as public baseline data for validating parsing, timing features, sequence models, and leakage-safe experimental pipelines.

It is not a substitute for a future BehavePass password-creation dataset. GREYC primarily records repeated typing/authentication attempts, not the moment a participant originally creates a password. Repeated attempts at the same password share the same static strength and guessability target, so thousands of captures are not thousands of independent password-strength labels.

## Local data and inspection

The raw dataset is local-only and ignored by Git under `data/`. From the repository root, inspect it without training:

```text
python -m ml.data.inspect_greyc --data-dir data/greyc/webkeystroke
```

The adapter reads `output_numpy/passwords`. Despite that directory name, the extracted dataset consists of plain UTF-8 text files. Each capture contains:

- `p_raw_press.txt`: two integer columns, key code and Unix epoch timestamp
- `p_raw_release.txt`: two integer columns, key code and Unix epoch timestamp
- `p_pp.txt`: adjacent press-to-press differences
- `p_pr.txt`: positional press-to-release-event differences
- `p_rp.txt`: press to next chronological release-event differences
- `p_rr.txt`: adjacent release-to-release differences
- `p_total.txt`: supplied total duration
- `password.txt`, `userid.txt`, `genuine.txt`, `date.txt`, and browser metadata

Values are milliseconds. This is established by the epoch magnitudes, human-scale differences, and exact equality between raw timestamp differences and the supplied timing vectors.

Release events can occur in a different order from presses when keys overlap. The adapter pairs releases back to presses by key code and occurrence order before deriving canonical dwell and flight values. Negative release-to-next-press flight times are valid and retained.

## Canonical samples and targets

`ml.data.schemas.CanonicalSample` holds a source-independent sample ID, typist participant ID, password hash ID, source, password, key codes, press/release timestamps, dwell/flight/press-latency vectors, digraph records, total duration, static features, optional target values, and source metadata. GREYC password owner, genuine/impostor status, capture time, and source path are retained in metadata.

When frontend dependencies and Node.js are available, the adapter batch-invokes the existing `frontend/src/utils/staticFeatures.ts` extractor for each unique password. It also retains zxcvbn's raw `guesses` value. The future continuous regression target is:

```text
log10(max(guesses, 1) + 1)
```

No strength labels are invented and no model is trained. If the frontend extractor is unavailable, composition features remain available while zxcvbn score, guess count, and target are explicitly `None`.

## Leakage-safe splitting

Use `ml.data.grouped_password_split`. It deterministically assigns complete `password_id` groups to train, validation, and test sets, ensuring the same password never crosses partitions.

Password grouping is primary for password-strength evaluation. Participant grouping instead measures generalization to unseen typists but may still leak identical passwords. Grouping by both is strictest, though with only a modest number of unique passwords it reduces flexibility and can make balanced partitions difficult. Retained participant and password identifiers support all three designs.

Malformed captures are counted with a source-relative path and reason; raw files are never changed. Validation covers missing files/IDs, empty sequences, mismatched event lengths, unmatched key events, non-numeric and non-finite timestamps, negative dwell, unordered presses, inconsistent supplied timing vectors/totals, and duplicate canonical IDs.
