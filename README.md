# BehavePass-Lite

> **Keystroke Dynamics-Based Password Strength Predictor Using BiLSTM & Neural Password Guesser Feedback**

BehavePass-Lite is a cybersecurity research platform investigating whether creation-time keystroke dynamics provide predictive signals for password guessability beyond static string analysis.

## Privacy and cybersecurity research policy

1. **Do not enter real passwords.** Create unique, synthetic passwords exclusively for this study.
2. **Zero plaintext storage:** Plaintext passwords are analyzed in memory only inside the client browser. No plaintext passwords, password hashes, or raw character keys are logged, sent across network APIs, or saved to the database.
3. **No psychological diagnosis:** The platform measures physical typing timing metrics only and makes no claims regarding stress, cognitive load, anxiety, or fatigue.

## Prerequisites

- Git
- Python 3.10, 3.11, or 3.12 (Python 3.12 recommended)
- Node.js 20 LTS or newer, with npm

The backend uses SQLite and does not require a separate database server for local development.

## Clone the repository

```text
git clone https://github.com/udaypisharody05/BehavePass.git
cd BehavePass
```

All commands below start in the cloned repository root. Keep the backend and frontend running in separate terminals.

## Backend setup on Windows PowerShell

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

If PowerShell blocks activation, use a process-scoped policy change and activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

## Backend setup on macOS/Linux

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

The backend runs at [http://localhost:8000](http://localhost:8000), with Swagger UI at [http://localhost:8000/docs](http://localhost:8000/docs).

By default, local data is stored in `backend/behavepass.db`, independent of the launch directory. Set `DATABASE_URL` before starting the server to use a different SQLAlchemy database URL.

## Frontend setup on Windows and macOS/Linux

Open another terminal in the repository root:

```text
cd frontend
npm install
npm run dev
```

The Vite frontend runs at [http://localhost:5173](http://localhost:5173) and proxies API requests to the backend on port 8000.

## Tests and checks

Run backend tests from `backend` with its virtual environment active:

```text
python -m pytest -v
```

Run frontend tests and the production build from `frontend`:

```text
npm run test
npm run build
```

`npm run build` runs the TypeScript check before creating the Vite production bundle. A no-output TypeScript check is also available as `npm run lint`.

## Apple Silicon

The declared Python packages and frontend build tools support macOS ARM64 for the recommended Python and Node.js versions; no architecture-specific project configuration is required. Use an ARM64-native Python installation (for example, from Homebrew or python.org) rather than mixing an Intel Python environment with ARM64 packages. If installation selects source builds instead of wheels, confirm that the active Python is 3.10-3.12 and that the terminal and Python process use the same architecture.

## Repository architecture

```text
BehavePass/
|-- frontend/   # React, Vite, TypeScript, Tailwind CSS, and zxcvbn
|-- backend/    # FastAPI, SQLAlchemy, Pydantic, and SQLite
|-- ml/         # ML preparation module and BiLSTM stub
|-- docs/       # Research and architecture specifications
`-- README.md
```

## Dataset CSV export

Research team members can download the derived dataset from the web interface or directly from:

```text
GET http://localhost:8000/api/export/csv
```

The export contains non-sensitive derived timing features, static password scores, and anonymous participant metadata ready for ML training.

## License and course project attribution

Cybersecurity Course Research Project — Vellore Institute of Technology (VIT).

- Aadi Rawat (Reg No: 23BCE2177)
- Uday Pisharody (Reg No: 23BCE2165)
