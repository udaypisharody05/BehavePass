# Machine Learning Preparation Module - BehavePass-Lite

This module prepares data preprocessing and model architectures for Phase 2:
- Variable-length keystroke sequence encoding using a Bidirectional LSTM (BiLSTM).
- Feature concatenation with static password features (`zxcvbn`, character counts, entropy).
- Multi-layer perceptron (MLP) regressor to estimate neural guessability rank (`log10_estimated_guesses` or PassGAN rank).

## Data Flow Pipeline

```text
[ Keystroke Sequence: (batch, seq_len, 4) ]
   ├── dwell_time
   ├── flight_time
   ├── press_to_press_latency
   └── is_backspace
        │
        ▼
[ BiLSTM Behavioural Encoder ] ──> [ Behavioural Embedding (128-dim) ]
                                                │
                                                ▼
[ Static Features (13-dim) ] ────> [ Concatenation Fusion Layer ] ──> [ MLP Head ] ──> [ Predicted Log Rank ]
```

## Setup & Training (Phase 2)
1. Export dataset CSV via `GET /api/export/csv`.
2. Load CSV into pandas for participant-independent train/test splitting.
3. Pass sequences into `ml/models/bilstm_stub.py`.
