# Machine Learning Preparation Module - BehavePass-Lite

This module contains the implemented preprocessing, experiment, and inference-compatible model architecture:
- Variable-length keystroke sequence encoding using a Bidirectional LSTM (BiLSTM).
- Fusion of a behavioral embedding with 11 safe static password features.
- Multi-layer perceptron (MLP) regression of `log10_estimated_guesses`.

The tested GREYC-Web preprocessing adapter is documented in
[`docs/GREYC_DATA.md`](../docs/GREYC_DATA.md). It performs inspection and
canonicalization only; it does not train a model.

The synthetic BiLSTM/fusion proof of concept is documented in
[`docs/bilstm_fusion_analysis.md`](../docs/bilstm_fusion_analysis.md). PyTorch is
installed by `backend/requirements.txt` because the live prediction endpoint uses
that synthetic-trained fusion checkpoint. The GREYC-Web adapter is a separate
data-inspection path and did not produce the current runtime checkpoint.

## Data Flow Pipeline

```text
[ Keystroke Sequence: (batch, seq_len, 6) ]
   ├── dwell_time
   ├── flight_time
   ├── press_to_press_latency
   ├── normalized_position
   ├── is_pause
   └── is_backspace
        │
        ▼
[ BiLSTM Behavioural Encoder ] ──> [ Behavioural Embedding (64-dim) ]
                                                │
                                                ▼
[ Safe Static Features (11-dim) ] ─> [ 16-dim Static Projection ]
                                                │
                                                ▼
                              [ Concatenation Fusion Layer ] ──> [ MLP Head ] ──> [ log10 estimated guesses ]
```

Training-time sequence/static means and standard deviations and target scaling
are stored in `ml/results/sequence_preprocessing.json`. Live inference reuses
those values and never fits preprocessing on browser input. The model checkpoint
is loaded by `backend/app/ml/inference.py` from
`ml/checkpoints/fusion_bilstm.pt`, on CPU and in evaluation mode.
