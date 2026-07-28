# Architecture Specification - BehavePass-Lite

**BehavePass-Lite** investigates whether creation-time keystroke dynamics provide additional predictive power beyond static password analysis when estimating password guessability rank.

---

## Complete Planned Architecture

```text
  Password Creation Field (Browser)
             │
             ├──> Keystroke Timing Capture (performance.now()) ──> Behavioural Features
             │                                                           │
             └──> Static Analysis (zxcvbn, Entropy, Counts) ────────────┼──> In-Memory Payload
                                                                         │
                                                                         ▼
                                                                FastAPI Backend (/api/sessions)
                                                                         │
                                                                         ├──> SQLite / PostgreSQL Store
                                                                         │
                                                                         ▼
                                                               BiLSTM Encoder (Phase 2)
                                                                         │
                                                                         ▼
                                                               Fusion Layer (Static + Behavioural)
                                                                         │
                                                                         ▼
                                                               MLP Guessability Rank Head
                                                                         │
                                                                         ▼
                                                               Transparent Feedback Output
```

---

## Phase Implementation Status

| Component | Stage 1 Status | Planned Phase 2 |
| :--- | :--- | :--- |
| **Keystroke Capture Engine** | **Implemented** (High-res `performance.now()`, negative flight time support, focus loss detection) | Field expansion |
| **Static Analyzer** | **Implemented** (Browser-only `zxcvbn`, Shannon entropy, pool entropy, character breakdown) | Advanced pattern match |
| **FastAPI Session API** | **Implemented** (Zero-plaintext validation, session endpoints, summary, analytics, deletion) | PostgreSQL migration |
| **Dataset CSV Exporter** | **Implemented** (Model-ready flat CSV output) | Automated train/test split |
| **Rule-Based Feedback** | **Implemented** (Transparent, non-clinical timing observations) | BiLSTM fusion prediction |
| **BiLSTM Sequence Encoder** | Architectural Stub in `ml/models/bilstm_stub.py` | PyTorch training pipeline |
| **PassGAN Rank Fusion** | Reference target specified in `DATA_DICTIONARY.md` | Neural guesser calibration |

---

## Component Details

### 1. Client-Side Keystroke Engine (`frontend/src/hooks/useKeystrokeCollector.ts`)
- Captures raw keydown and keyup timestamps.
- Filters auto-repeat events (`e.repeat`).
- Rejects autofill, paste actions, and focus-lost sessions by setting `is_valid: false` with explicit `invalid_reason`.

### 2. Zero-Plaintext Security Boundary
- Static features are evaluated inside the participant's browser.
- Plaintext string is discarded immediately.
- Backend routes receive only derived numeric statistics and timing interval arrays.

### 3. Machine Learning Fusion Design (Phase 2 Integration)
- The BiLSTM processes normalized timing quadruples $[T_{\text{dwell}}, T_{\text{flight}}, T_{\text{press}}, I_{\text{backspace}}]$.
- The output hidden state ($128$-dim embedding) is concatenated with the $13$-dim static feature vector.
- An MLP maps the concatenated vector to $\log_{10}(\text{estimated guesses})$.
