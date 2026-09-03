# 100x Resume — Agentic Resume Verification

**Verify any developer resume with public evidence, not claims.**

> Upload PDF/DOCX → AI parses → auto-detects GitHub, LeetCode, HackerRank, InterviewBit → live scrape → 10 explainable scores → recruiter-ready report (PDF).

![Next.js](https://img.shields.io/badge/Next.js-16-black) ![FastAPI](https://img.shields.io/badge/FastAPI-0.136-009688) ![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB) ![License](https://img.shields.io/badge/license-MIT-blue)

Demo: `http://localhost:3000` · API docs: `http://localhost:8000/docs` · Team **grow100x**

---

## Why 100x Resume

Resumes are unverified. Recruiters lose weeks to manual screening and bias. **100x Resume** never accuses — it shows *what is publicly verifiable* with confidence, evidence and explainable 0–100 scores.

## Features

- **AI Resume Parse** — PyMuPDF + LLM (Genkit) extracts personal, education, experience, 10-category skills, projects, achievements.
- **Auto-detect Handles** — scans `raw_text` + personal fields for `github.com/*`, `linkedin.com/in/*`, `leetcode.com/*`, `hackerrank.com/*`, `interviewbit.com/profile/*` (regex + blocking).
- **Live Scraping (no auth)** — `GitHub` (real API), `LeetCode` (GraphQL), `HackerRank` (REST), `InterviewBit` (REST) with 1-hour TTL cache; others simulated with deterministic mock.
- **Verification** — every skill/project/achievement matched to public code with `Verified / Strong / Partial / Limited / No Evidence`.
- **Scoring** — 10 scores (Completeness, Credibility, Technical, GitHub Eng, Coding, Projects, OSS, Docs, Learning, Overall) + DSA Depth (LeetCode/HackerRank/InterviewBit/Codeforces/CodeChef/GFG weighted).
- **Report** — 12-section radar, evidence, strengths/improvements, AI summary, print/PDF via ReportLab.
- **HR Batch** — upload N resumes, auto-connect all, rank by overall.

---

## Quick Start (Step-by-Step)

### Option A: One-Click Launch (Windows)
Double-click `start.bat` in the project root. It will automatically:
1. Create and configure the virtual environment in `backend/venv`
2. Install Python backend requirements and Playwright Chromium
3. Install frontend Node modules and start both servers

---

### Option B: Manual Setup

#### 1. Backend Setup (Python 3.10+)

> **IMPORTANT**: Always use a Python virtual environment to avoid package version collisions with global Python libraries.

```bash
# Navigate to backend
cd backend

# Create virtual environment (if not already created)
python -m venv venv

# Activate the virtual environment:
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On Windows (CMD):
venv\Scripts\activate.bat
# On macOS / Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the FastAPI backend server
python -m uvicorn app.main:app --port 8000 --host 127.0.0.1
```

*Backend Swagger documentation will be available at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)*

---

#### 2. Frontend Setup (Node.js 18+)

```bash
# Navigate to frontend (from project root)
cd frontend

# Install Node modules
npm install

# Start development server with Turbopack
npm run dev
```

*Web Application UI will be live at: [http://localhost:3000](http://localhost:3000)*  
*(Next.js automatically proxies `/api/*` requests to `http://127.0.0.1:8000` via `next.config.ts`)*

---

## Dependency & Conflict Resolution Notes

If you encounter dependency errors during manual installation, note the following configurations:

1. **`dotpromptz` and `genkit 0.9.0`**:
   - `genkit==0.9.0` requires `dotpromptz` for prompt management.
   - `dotpromptz-handlebars` is pinned to `0.1.3` (since `0.1.8` is unpublished on PyPI).
   - If installing manually without `requirements.txt`, run:
     ```bash
     pip install dotpromptz-handlebars==0.1.3 dotpromptz==0.1.3
     pip install genkit==0.9.0 genkit-openai==0.9.0 --no-deps
     ```
2. **Execution Context**:
   - Running `py -m uvicorn ...` without activating `venv` uses your global Python installation where `dotpromptz` may not be installed. Always run using `venv\Scripts\python -m uvicorn ...` or after activating `venv`.
   - Running `npm` commands must be done inside the `frontend/` directory where `package.json` resides.

---

## Usage Walkthrough

1. **Candidate Resume Upload**:
   - Open `http://localhost:3000/analyze` → Drag and drop any PDF/DOCX resume (or click **"Load demo candidate"** to test with Aarav Mehta).
2. **Review & Auto-Connect**:
   - Inspect parsed personal info and technical skills.
   - Click **"Auto-connect all"** to automatically discover profile handles (`GitHub`, `LeetCode`, `HackerRank`, `InterviewBit`).
3. **Run Real-Time Verification**:
   - Click **"Run verification"** to trigger the SSE pipeline and generate the full verification report.
4. **Export & Share**:
   - View radar charts, evidence matching, strengths, and download the recruiter-ready PDF report via `/api/report/[id]/pdf`.
5. **HR Batch Mode**:
   - Navigate to `http://localhost:3000/hr` → upload multiple resumes simultaneously → batch connect → view ranked leaderboard.

---

## API Reference

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Health check & AI provider status |
| `POST` | `/api/resume/upload` | Extract raw text from PDF/DOCX file |
| `POST` | `/api/resume/parse` | `{text}` → Structured `ParsedResume` JSON |
| `GET` | `/api/integrations/platforms` | Supported platform catalog |
| `POST` | `/api/integrations/detect` | Auto-detect profile handles from resume |
| `POST` | `/api/integrations/connect` | Connect & live-scrape single platform |
| `POST` | `/api/integrations/auto-connect` | Detect and scrape all platforms |
| `POST` | `/api/analysis/run` | SSE stream for 10-stage scoring analysis |
| `GET` | `/api/report/{id}` | Retrieve candidate evaluation report |
| `GET` | `/api/report/{id}/pdf` | Generate and download styled PDF report |
| `POST` | `/api/resume/batch` | Multi-file HR batch resume parsing |
| `POST` | `/api/analysis/batch` | Batch scoring leaderboard |

---

## Project Structure

```
100x/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI entrypoint
│   │   ├── api/                        # API route handlers
│   │   ├── core/
│   │   │   ├── ai/                     # Genkit flows & LLM summarizers
│   │   │   ├── analysis/               # 10-category scoring & evidence matching
│   │   │   ├── integrations/           # Live scrapers (GitHub, LeetCode, HR, IB)
│   │   │   └── parsers/                # PDF/DOCX text extraction
│   │   └── config.py
│   ├── requirements.txt                # Python backend dependencies
│   └── venv/                           # Python virtual environment
├── frontend/
│   ├── app/                            # Next.js App Router (pages & styles)
│   ├── components/                     # UI components, radar charts, reports
│   ├── lib/                            # API client & TypeScript types
│   ├── package.json                    # Node dependencies
│   └── next.config.ts                  # API rewrite proxy
├── docs/                               # PRD, SRS, & project specifications
├── start.bat                           # Windows launch script
└── README.md
```

---

## Tech Stack

- **Frontend**: Next.js 16 (App Router + Turbopack), Tailwind CSS v4, Lucide Icons, Simple Icons, Inter & JetBrains Mono fonts.
- **Backend**: FastAPI, Pydantic v2, PyMuPDF, python-docx, ReportLab (PDF generator), HTTPX, Playwright, Google Genkit 0.9.0 + OpenAI.

---

## Team grow100x

Gajanan Patange — Coditas SWE Intern (React/JS, CI/CD) + Ethosh AI Intern (React/TS/FastAPI, AWS Bedrock/S3/EC2). Built Scrapify (Next.js/Genkit/Playwright) & Beachrecs (Leaflet/Gemini). 1st Rank InterviewBit (institute), 2× Hackathon Winner, DIPEX Finalist, CoCubes 585.

---

## License

MIT

