# BehavePass-Lite

> **Keystroke Dynamics-Based Password Strength Predictor Using BiLSTM & Neural Password Guesser Feedback**

BehavePass-Lite is a cybersecurity research platform investigating whether creation-time keystroke dynamics (dwell time, inter-key flight time, press-to-press latency, pauses, and backspaces) provide predictive signals for password guessability beyond static string analysis (`zxcvbn`, Shannon entropy, character distribution).

---

## 🔒 Privacy & Cybersecurity Research Policy

1. **Do NOT enter real passwords.** Create unique, synthetic passwords exclusively for this study.
2. **Zero Plaintext Storage:** Plaintext passwords are analyzed **in-memory only** inside the client browser. No plaintext passwords, password hashes, or raw character keys are ever logged, sent across network APIs, or saved to the database.
3. **No Psychological Diagnosis:** The platform measures physical typing timing metrics only. It makes **zero** claims regarding stress, cognitive load, anxiety, or fatigue.

---

## 🏗️ Repository Architecture

```text
behavepass-lite/
├── frontend/             # React + Vite + TypeScript + Tailwind CSS + zxcvbn
│   ├── src/
│   │   ├── components/   # UI components (Header, PasswordTaskCard, FeedbackCard, AnalyticsModal)
│   │   ├── hooks/        # Keystroke collector custom hook
│   │   ├── services/     # API client
│   │   ├── types/        # TypeScript schemas
│   │   └── utils/        # Client static feature & keystroke dynamics extractors
│   └── ...
├── backend/              # Python FastAPI + SQLAlchemy + Pydantic v2 + SQLite
│   ├── app/
│   │   ├── api/          # Endpoints (/health, /sessions, /analytics, /export, /predict)
│   │   ├── core/         # Config & security guardrails
│   │   ├── database/     # SQLite ORM session engine
│   │   ├── models/       # Database models (Participant, Session, KeystrokeFeature)
│   │   ├── schemas/      # Pydantic request/response validation schemas
│   │   └── services/     # Feature validator, transparent behavioural rules, session service
│   └── tests/            # pytest suite (privacy, feature validation, session lifecycle)
├── ml/                   # Machine learning preparation module & BiLSTM stub
├── docs/                 # Research specifications (ARCHITECTURE, DATA_DICTIONARY, PRIVACY, EXPERIMENT_PROTOCOL)
└── README.md
```

---

## 🚀 Windows Local Setup & Quick Start

### 1. Prerequisites
- Python 3.10+
- Node.js v18+ & npm

### 2. Backend Setup & Run

Open a command prompt or PowerShell terminal in `c:\BehavePass\backend`:

```powershell
cd c:\BehavePass\backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Install backend dependencies
pip install -r requirements.txt

# Launch FastAPI development server
uvicorn app.main:app --reload --port 8000
```
The backend service will run at `http://localhost:8000`. Access Swagger documentation at `http://localhost:8000/docs`.

### 3. Frontend Setup & Run

Open a second terminal window in `c:\BehavePass\frontend`:

```powershell
cd c:\BehavePass\frontend

# Install frontend dependencies
npm install

# Run Vite dev server
npm run dev
```
The React interface will run at `http://localhost:5173`.

---

## 🧪 Running Automated Tests

### Backend Unit Tests
In the backend terminal with virtual environment active:

```powershell
cd c:\BehavePass\backend
pytest -v
```

### Frontend Utility Tests
In the frontend terminal:

```powershell
cd c:\BehavePass\frontend
npm run test
```

---

## 📊 Dataset CSV Export

Research team members can view session summaries or download the complete dataset CSV via the web interface dashboard, or directly by calling:

```text
GET http://localhost:8000/api/export/csv
```

The CSV dataset contains non-sensitive derived timing features, static password scores, and anonymous participant metadata ready for ML training.

---

## 📄 License & Course Project Attribution

Cybersecurity Course Research Project — Vellore Institute of Technology (VIT).
- Aadi Rawat (Reg No: 23BCE2177)
- Uday Pisharody (Reg No: 23BCE2165)
