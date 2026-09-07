# Faculty review demo talking points

### Project objective

Investigate whether creation-time keystroke behavior adds information beyond
conventional static password analysis when predicting password guessability.

### Novelty

- Static password characteristics
- Creation-time keystroke dynamics
- Variable-length sequence modeling using a BiLSTM
- Privacy-conscious derived-feature processing

### Demo flow

1. Run `python scripts/check_demo_ready.py` and point out `DEMO READY`.
2. Open `http://localhost:5173` and accept the research notice.
3. Type a new synthetic password naturally; never use or paste a real password.
4. Submit the session.
5. Point out the separate static assessment, behavioral timing summary, and
   behavior-adjusted experimental estimate.
6. Highlight the synthetic-training disclaimer and absence of raw characters.

### Key result

Static features currently outperform behavior-augmented prediction on the
synthetic dataset. The safe-static Random Forest achieved RMSE 0.8106, while the
BiLSTM fusion model achieved RMSE 0.9343.

### Why this is still valid

The original research question allows a null result. The experiment establishes
that behavioral contribution must be validated rather than assumed, while also
demonstrating that the proposed end-to-end system can be implemented.

### Limitations

- Synthetic behavioral training data
- A zxcvbn-derived current target rather than PassGAN rank
- No real-user behavioral validation yet

### Future work

- Controlled, consented real-user data collection
- PassGAN or other neural guessability labeling
- Retraining on real sequential data
- Larger participant-independent evaluation
