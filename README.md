# 100x Resume — Agentic Resume Verification

**Verify any developer resume with public evidence, not claims.**

> Upload PDF/DOCX → AI parses → auto-detects GitHub, LeetCode, HackerRank, InterviewBit → live scrape → 10 explainable scores → recruiter-ready report (PDF).

![Next.js](https://img.shields.io/badge/Next.js-16-black) ![FastAPI](https://img.shields.io/badge/FastAPI-0.136-009688) ![Python](https://img.shields.io/badge/Python-3.13-3776AB) ![License](https://img.shields.io/badge/license-MIT-blue)

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

## Quick Start

```bash
# 1. Backend (requires Python 3.13, FFmpeg not needed)
cd backend
py -m pip install -r requirements.txt
# genkit 0.9.0 needs --no-deps dance, already in requirements
py -m uvicorn app.main:app --port 8000 --host 127.0.0.1

# 2. Frontend
cd ../frontend
npm install
npm run dev   # http://localhost:3000
# Next rewrites /api -> 127.0.0.1:8000 (see next.config.ts)
```

Or double-click `start.bat` (creates `.venv` on first run, launches both).

## Usage

1. `http://localhost:3000/analyze` → drop PDF (or *Load demo candidate* Aarav Mehta).
2. Review parsed skills, *Auto-connect all* (detects `gajananhp13` etc) or manual handles.
3. *Run verification* → SSE pipeline → `ReportView` (`/report/[id]`).
4. HR: `/hr` → multi-upload → *Connect all* → *Run validation* → ranked table.

## API

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/resume/upload` | FormData `file` → extracted text |
| `POST` | `/api/resume/parse` | `{text}` → `ParsedResume` |
| `GET` | `/api/integrations/platforms` | catalog |
| `POST` | `/api/integrations/detect` | `{resume}` → handles |
| `POST` | `/api/integrations/connect` | `{platform,handle,resume}` → `ConnectedProfile` |
| `POST` | `/api/integrations/auto-connect` | detect+collect all |
| `POST` | `/api/analysis/run` | SSE `stage` → `report_id` |
| `GET` | `/api/report/{id}` / `/pdf` | fetch / PDF |

## Project Structure

```
backend/
  app/main.py, api/routes_*.py, core/{parsers,integrations/platforms/{leetcode,hackerrank,interviewbit,github}, analysis/{coding,scoring}, ai}
  data/reports/*.json, linkedin_scraper/
frontend/
  app/{page.tsx, analyze/page.tsx, hr/page.tsx, report/[id]/page.tsx, globals.css}
  components/{ui.tsx, charts.tsx, platform-icon.tsx, report/}
  lib/{api.ts, platforms.ts, cn.ts, types.ts}
start.bat, .gitignore
```

## Tech

Frontend: Next.js 16 (Turbopack), Tailwind 4, Inter/JetBrains Mono, lucide-react, simple-icons. Backend: FastAPI, Pydantic, httpx, PyMuPDF, python-docx, ReportLab, Genkit 0.9.0 + OpenAI (mock fallback).

## Team grow100x

Gajanan Patange — Coditas SWE Intern (React/JS, CI/CD) + Ethosh AI Intern (React/TS/FastAPI, AWS Bedrock/S3/EC2). Built Scrapify (Next.js/Genkit/Playwright) & Beachrecs (Leaflet/Gemini). 1st Rank InterviewBit (institute), 2× Hackathon Winner, DIPEX Finalist, CoCubes 585.

## License

MIT
