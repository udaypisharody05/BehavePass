# Final experimental results summary

All results below are the already measured participant-held-out results. No
models were retrained for this summary.

| Model | MAE | RMSE | R² |
|---|---:|---:|---:|
| Safe-static Random Forest | 0.3113 | 0.8106 | 0.9619 |
| Static-only MLP | 0.4647 | 0.8914 | 0.9539 |
| Behavioral-only BiLSTM | 0.8210 | 1.3223 | 0.8987 |
| BiLSTM + static fusion | 0.5210 | 0.9343 | 0.9494 |

The safe-static Random Forest is the strongest leakage-safe baseline. The
behavioral-only BiLSTM learns relationships present in the synthetic data, but
fusion did not outperform the static-only models. Therefore, the current
experiment does not demonstrate incremental behavioral benefit.

The implemented browser-to-BiLSTM fusion path nevertheless demonstrates that
privacy-conscious, variable-length keystroke inference is technically feasible.
Meaningful validation of behavioral contribution requires controlled real-user
sequence data and participant-independent evaluation.

The current target is derived from zxcvbn-based guessability rather than PassGAN
rank. PassGAN is not implemented.
