# Pilot Experiment Protocol - BehavePass-Lite

## 1. Study Objective
To gather creation-time keystroke dynamics from human participants under controlled experimental conditions (timed vs untimed) to evaluate if typing timing features improve password guessability prediction beyond static string metrics.

---

## 2. Participant Instructions & Rules
1. **Safety First**: Do **NOT** use a real password or a password used for personal or institutional accounts.
2. **Synthetic Entry**: Invent a new, synthetic password for each trial task.
3. **Natural Typing**: Type naturally using standard keyboard rhythm. Do not deliberately stall or paste text.

---

## 3. Experimental Conditions & Tasks

### Task 1: Untimed Password Creation (`condition: untimed`)
- Participant enters a unique experimental password without time pressure.
- Platform records dwell times, inter-key flight times, pauses, and backspace corrections.

### Task 2: Time-Limited Password Creation (`condition: timed`)
- Participant is presented with a 15-second countdown timer (`timed_limit_ms: 15000`).
- Evaluates keystroke timing variations under time-constrained creation conditions.

---

## 4. Participant-Independent Data Partitioning
- Anonymous participant codes (e.g. `PART-8921`) are retained across multiple trial sessions.
- In Phase 2 model training, data splitting is performed **strictly by participant code** (all sessions of participant $P_i$ are placed in either train or test set) to prevent data leakage across typing styles.
