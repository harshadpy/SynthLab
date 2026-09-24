# ArXiv RAG Research Lab — Command Reference Guide

This document lists all essential commands to configure, run, test, and build both the **Backend** (FastAPI) and **Frontend** (Vite + React + Tailwind) of the ArXiv RAG Research Lab.

---

## 1. Virtual Environment (`venv`) Setup & Activation

### Step 1: Create the Virtual Environment
Open a terminal in the project root directory (`c:\Users\Jarvis\Downloads\researchsystem`):

```powershell
python -m venv .venv
```

### Step 2: Activate the Virtual Environment

#### On Windows PowerShell:
```powershell
.\.venv\Scripts\Activate.ps1
```

> **Note:** If PowerShell blocks execution of scripts, run this command once to allow script execution for the current session:
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> ```

#### On Windows Command Prompt (`cmd.exe`):
```cmd
.\.venv\Scripts\activate.bat
```

#### On macOS / Linux:
```bash
source .venv/bin/activate
```

---

## 2. Backend (FastAPI + Python)

*Ensure your virtual environment is activated before running these commands.*

### Install / Upgrade Dependencies:
```powershell
python -m pip install --upgrade pip
pip install -r apps\api\requirements.txt
```

### Start the FastAPI Backend Server:
```powershell
# Using Python module runner (recommended for Windows PowerShell)
python -m uvicorn apps.api.main:app --reload --port 8000

# Or directly specifying the venv Python binary:
.\.venv\Scripts\python.exe -m uvicorn apps.api.main:app --reload --port 8000
```

- **Backend API Base**: `http://localhost:8000`
- **Interactive API Documentation (Swagger)**: `http://localhost:8000/docs`
- **Alternative Docs (ReDoc)**: `http://localhost:8000/redoc`
- **Health Check**: `http://localhost:8000/health`

---

## 3. Frontend (Vite + React + TypeScript + Tailwind)

Open a **separate terminal** window in the project root.

### Navigate to the Web App Directory:
```powershell
cd apps\web
```

### Install Node Dependencies:
```powershell
npm install
```

### Start the Vite Development Server (Auto-opens Browser):
```powershell
npm run dev
```

> **Note:** `vite.config.ts` is configured with `open: true`, so running `npm run dev` automatically opens your default browser directly to the application.
> You can also run:
> ```powershell
> npm run dev -- --open
> ```

- **Web Application UI**: `http://localhost:5173` (or the active port displayed in terminal)
- **Live Reverse Proxy**: All `/api` requests are automatically proxied to `http://localhost:8000`

---

## 4. Running Automated Tests

Run tests inside the activated virtual environment (`.venv`) from the project root:

### Run All Tests:
```powershell
python -m pytest tests/ -v
```

### Run Specific Test Suites:
```powershell
# Test ArXiv search & ID cleaner
python -m pytest tests/test_arxiv.py -v

# Test 5 RAG architectures with live inference
python -m pytest tests/test_rag_pipelines.py -v

# Test LLM-as-a-judge evaluation benchmark
python -m pytest tests/test_evaluation.py -v
```

---

## 5. Building for Production

### Build the Frontend Bundle:
```powershell
cd apps\web
npm run build
```
*(The compiled production assets will be generated in `apps/web/dist/`)*

### Preview Production Frontend Build:
```powershell
cd apps\web
npm run preview
```

---

## 6. Docker Deployment (Optional)

To run the entire system via Docker:

```powershell
# Build and start both API and Web containers
docker-compose up --build

# Run in background (detached mode)
docker-compose up -d

# View container logs
docker-compose logs -f

# Stop and remove containers
docker-compose down
```

---

## 7. Quick Cheat Sheet (Daily Workflow)

| Task | Command | Directory |
|---|---|---|
| **Activate venv** | `.\.venv\Scripts\Activate.ps1` | Project Root |
| **Run Backend** | `uvicorn apps.api.main:app --reload --port 8000` | Project Root |
| **Run Frontend** | `npm run dev` | `apps/web` |
| **Run Tests** | `python -m pytest tests/ -v` | Project Root |
| **Build Web** | `npm run build` | `apps/web` |
