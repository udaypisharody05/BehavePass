# Data Dictionary - BehavePass-Lite

All timing metrics are represented in **milliseconds (ms)** unless explicitly stated otherwise.

---

## 1. Participant Table (`participants`)

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer (PK) | Auto-increment primary key. |
| `participant_code` | String (Index) | Reusable anonymous code (e.g. `PART-8921`) enabling participant-independent dataset splitting. |
| `created_at` | DateTime | Initial participant registration timestamp. |

---

## 2. Session Table (`sessions`)

### Metadata
| Field Name | Type | Description |
| :--- | :--- | :--- |
| `id` | String UUID | Unique session identifier. |
| `task_id` | String | Task designation (e.g. `TASK-01`). |
| `task_type` | String | Task category (e.g. `creation`). |
| `attempt_number` | Integer | Attempt counter for current task (starts at 1). |
| `condition` | String | Experimental mode: `timed` or `untimed`. |
| `timed_limit_ms` | Float (Nullable) | Time limit in ms (e.g. `15000.0` or `null` if untimed). |
| `completed_within_limit` | Boolean (Nullable) | `true` if typed before time limit; `false` if timed out; `null` if untimed. |
| `timed_out` | Boolean | `true` if countdown timer reached zero before submission. |
| `pause_threshold_ms` | Float | Threshold for pause classification (default `500.0` ms). |
| `collector_version` | String | Version of client keystroke engine (`1.0.0`). |
| `feature_schema_version` | String | Version of derived feature schema (`1.0.0`). |
| `consent_version` | String | Privacy protocol consent version (`1.0.0`). |
| `is_valid` | Boolean | Validity flag (`true` if typed naturally without paste, autofill, or focus loss). Included in CSV export for research audit. |
| `invalid_reason` | String (Nullable) | Diagnostic reason if session was flagged invalid. |
| `device_type` | String | Participant client device type (`desktop`). |

> [!NOTE]
> **Dataset Filter Rule for ML Training**: The dataset CSV export (`GET /api/export/csv`) contains both valid and invalid sessions to support audit logging. Model training pipelines must filter strictly using `is_valid == true` so that only genuine keystroke sequences are used to train the BiLSTM model.

---

### Static Password Features (Browser Derived - In-Memory)
| Field Name | Type | Unit | Description |
| :--- | :--- | :--- | :--- |
| `password_length` | Integer | chars | Total number of characters typed in final password ($L$). |
| `lowercase_count` | Integer | count | Number of lowercase ASCII characters (`a-z`). |
| `uppercase_count` | Integer | count | Number of uppercase ASCII characters (`A-Z`). |
| `digit_count` | Integer | count | Number of numeric digits (`0-9`). |
| `symbol_count` | Integer | count | Number of special symbols/punctuation. |
| `unique_character_count` | Integer | count | Number of distinct characters in password string. |
| `repeated_character_count` | Integer | count | Count of duplicate characters (`length - unique_count`). |
| `repeated_substring_count` | Integer | count | Count of multi-character substrings (length $k \ge 2$) that appear more than once in the password string. |
| `sequential_character_count` | Integer | count | Count of adjacent character transitions $(c_i, c_{i+1})$ where $|\text{ASCII}(c_{i+1}) - \text{ASCII}(c_i)| = 1$ (e.g., `ab`, `bc`, `12`, `32`, `zy`). |
| `zxcvbn_score` | Integer | $0-4$ | `zxcvbn` strength score ($0-4$). |
| `log10_estimated_guesses` | Float | $\log_{10}$ | $\log_{10}(\text{zxcvbn estimated guesses} + 1)$. |
| `empirical_character_entropy` | Float | bits | Shannon entropy $H = -\sum p_i \log_2 p_i$ based on character frequency distribution. |
| `character_pool_entropy_estimate` | Float | bits | Calculated as $L \times \log_2(R)$, where $R$ is the defined character pool size from present character classes. Does **NOT** use unique character count. |

#### `zxcvbn` Score to UI Strength Tier Mapping
| `zxcvbn_score` | UI Strength Tier | Description |
| :---: | :--- | :--- |
| **0** | **Very Weak** | Easily guessable within $10^3$ guesses. |
| **1** | **Weak** | Guessable within $10^6$ guesses. |
| **2** | **Moderate** | Guessable within $10^8$ guesses. |
| **3** | **Strong** | Guessable within $10^{10}$ guesses. |
| **4** | **Very Strong** | Very resistant to guessing ($>10^{10}$ guesses). |

#### Character-Class Combination to Pool Size ($R$) Mapping Table
| Lowercase (`a-z`, 26) | Uppercase (`A-Z`, 26) | Digits (`0-9`, 10) | Symbols (32) | Pool Size ($R$) | Example |
| :---: | :---: | :---: | :---: | :---: | :--- |
| Yes | No | No | No | **26** | `password` |
| No | Yes | No | No | **26** | `PASSWORD` |
| No | No | Yes | No | **10** | `12345678` |
| No | No | No | Yes | **32** | `!@#$%^&*` |
| Yes | Yes | No | No | **52** | `PassWord` |
| Yes | No | Yes | No | **36** | `pass1234` |
| Yes | No | No | Yes | **58** | `pass!@#$` |
| No | Yes | Yes | No | **36** | `PASS1234` |
| No | Yes | No | Yes | **58** | `PASS!@#$` |
| No | No | Yes | Yes | **42** | `1234!@#$` |
| Yes | Yes | Yes | No | **62** | `Pass1234` |
| Yes | Yes | No | Yes | **84** | `Pass!@#$` |
| Yes | No | Yes | Yes | **68** | `pass123!` |
| No | Yes | Yes | Yes | **68** | `PASS123!` |
| Yes | Yes | Yes | Yes | **94** | `P@ss123!` |

---

### Session Timing & Behavioural Features
| Field Name | Type | Unit | Description |
| :--- | :--- | :--- | :--- |
| `total_typing_duration` | Float | ms | Total time from first keydown to final keyup event. |
| `total_key_presses` | Integer | count | Total physical keypress events (including backspaces). |
| `average_dwell_time` | Float | ms | Mean key press duration ($\text{keyup} - \text{keydown}$). |
| `dwell_time_std` | Float | ms | Standard deviation of dwell times. |
| `average_flight_time` | Float | ms | Mean inter-key flight time ($\text{keydown}_i - \text{keyup}_{i-1}$) for $i \ge 1$. |
| `flight_time_std` | Float | ms | Standard deviation of flight times (negative flight times allowed for key overlaps). |
| `average_press_latency` | Float | ms | Mean press-to-press latency ($\text{keydown}_i - \text{keydown}_{i-1}$) for $i \ge 1$. |
| `longest_interkey_delay` | Float | ms | Maximum press-to-press latency recorded in session. |
| `pause_count` | Integer | count | Count of press-to-press latencies $\ge \text{pause\_threshold\_ms}$. |
| `total_pause_duration` | Float | ms | Cumulative sum of pause interval durations. |
| `backspace_count` | Integer | count | Total number of backspace keys pressed. |
| `backspace_rate` | Float | ratio | `backspace_count / total_key_presses`. |
| `correction_burst_count` | Integer | count | Sequences of $\ge 2$ consecutive backspace actions. |
| `characters_per_second` | Float | char/s | $\text{password\_length} / (\text{duration} / 1000)$. |
| `behavioural_model_status` | String (Nullable) | - | Runtime fusion-model status. `null` identifies historical sessions recorded before inference persistence. |
| `fusion_log10_estimated_guesses` | Float (Nullable) | $\log_{10}$ | Experimental behavior-augmented estimate. Remains `null` when inference is unavailable or was not recorded. |

---

## 3. Keystroke Features Sequence Table (`keystroke_features`)

| Field Name | Type | Unit | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer (PK) | - | Sequence item primary key. |
| `session_id` | String (FK) | - | Foreign key reference to parent `sessions.id`. |
| `sequence_index` | Integer | index | $0$-based position index in typing sequence. |
| `dwell_time` | Float | ms | Dwell duration ($\text{keyup} - \text{keydown}$). |
| `flight_time` | Float (Nullable) | ms | Inter-key flight time ($\text{keydown}_i - \text{keyup}_{i-1}$). Represented as `null` for sequence index 0. |
| `press_to_press_latency` | Float (Nullable) | ms | Press-to-press latency ($\text{keydown}_i - \text{keydown}_{i-1}$). Represented as `null` for sequence index 0. |
| `is_backspace` | Boolean | bool | `true` if key action was Backspace. |
| `is_pause` | Boolean | bool | `true` if press-to-press latency $\ge \text{pause\_threshold\_ms}$. |

The CSV export includes this sequence deterministically in
`keystroke_sequence_json`, ordered by `sequence_index`. Each JSON item contains
only the six fields above; it contains no password text, character identity, or
raw key code.
