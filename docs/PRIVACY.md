# Privacy & Security Guardrails - BehavePass-Lite

## 1. Zero Plaintext Policy
BehavePass-Lite is designed with privacy-first research principles:
- **No Real Credentials**: Participants are instructed never to enter real or reused passwords.
- **Client-Side-Only Parsing**: Plaintext passwords are evaluated strictly in the client's browser DOM memory.
- **Immediate Discard**: Plaintext strings are discarded immediately following character count extraction.
- **Zero Plaintext Transmission**: No password text, password hash, or character key values are transmitted across HTTP endpoints or written to database storage.

## 2. Keystroke Feature Anonymization
- Keystroke timing sequences record $[T_{\text{dwell}}, T_{\text{flight}}, T_{\text{press}}, I_{\text{backspace}}]$.
- Specific key identities (letters, numbers, symbols) are **stripped prior to storage**.
- Only generic boolean flags (`is_backspace`, `is_pause`) are retained for sequence modelling.

## 3. Session Validity & Dataset Export Policy
- **Audit Preservation**: Invalid sessions (`is_valid: false`, e.g. paste, autofill, or focus loss) are preserved in database storage and included in dataset CSV exports (`GET /api/export/csv`) to allow researchers to audit participant compliance and anomaly rates.
- **Model Training Rule**: Machine learning training pipelines filter dataset rows strictly by `is_valid == true` to ensure model training uses only genuine, untampered typing sequences.

## 4. Participant Anonymity & Data Control
- Participants are identified via reusable anonymous codes (e.g. `PART-8921`).
- No personal identifiable information (PII) such as IP address, name, or email is stored.
- Participants or researchers may withdraw and delete session data using the `DELETE /api/sessions/{session_id}` endpoint.

## 5. Scope Limitations on Psychological Claims
- **Strict Boundary**: The platform describes physical, measurable typing characteristics (e.g. "Frequent corrections were observed", "One long pause was recorded").
- **Forbidden Terms**: The software **never** outputs statements inferring stress, anxiety, cognitive load, fatigue, or any psychological condition.
