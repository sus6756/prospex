# Prospex — AI-Powered Lead Discovery & Qualification Platform

A production-ready prototype that lets businesses **discover, qualify, and organize high-quality B2B leads** using AI.

Describe your Ideal Customer Profile (ICP) in plain English → AI parses it into structured criteria → the platform discovers matching companies across multiple data sources, enriches decision-maker contact information, scores every lead 0–100 with explanations, deduplicates automatically, and lets you search, filter, and export the results.

---

## Features

| # | Feature | Status |
|---|---------|--------|
| 1 | Natural language ICP input | ✅ |
| 2 | AI-powered ICP understanding (OpenAI, with deterministic fallback) | ✅ |
| 3 | Lead discovery from multiple data sources (parallel) | ✅ |
| 4 | Contact enrichment (names, emails, titles, LinkedIn, phones) | ✅ |
| 5 | AI lead scoring with per-criterion explanations | ✅ |
| 6 | Duplicate detection (fuzzy domain/name/email matching) | ✅ |
| 7 | Search, filter, and CSV/JSON export | ✅ |

Bonus: JWT authentication, per-user workspaces, pipeline overview dashboard, Docker deployment.

---

## Tech Stack

- **Frontend:** Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4
- **Backend:** Python 3.13, FastAPI, SQLAlchemy
- **Database:** SQLite for local dev; PostgreSQL in production (switch via `DATABASE_URL`)
- **AI:** OpenAI (structured JSON output). Falls back to a deterministic local engine when no API key is set.
- **Data sources:** Simulated web / Crunchbase / LinkedIn adapters + real **Hunter.io** integration with automatic fallback.

---

## Quick Start (local dev)

### 1. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000, create an account, and run your first ICP discovery.

> The frontend talks to the backend at `http://localhost:8000` by default.
> Override with `NEXT_PUBLIC_API_URL` if your backend runs elsewhere.

---

## Enabling the AI engine (optional)

The platform works **fully out of the box** using a built-in deterministic parser and scorer.
To enable AI-powered ICP understanding and richer scoring explanations, set credentials for
**any one** of the supported providers in `backend/.env`:

```bash
cp .env.example backend/.env
# then edit backend/.env — pick one:
GEMINI_API_KEY=your-gemini-key      # free tier — https://aistudio.google.com/apikey
GEMINI_MODEL=gemini-3.5-flash-lite
# OR
OPENAI_API_KEY=sk-...               # needs billing credits
OPENAI_MODEL=gpt-4o-mini
# OR
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-5
```

Provider priority is Anthropic → Gemini → OpenAI. `OPENAI_BASE_URL` can additionally route the
OpenAI path to any OpenAI-compatible endpoint (Ollama, Groq, OpenRouter, vLLM).

Any failure or missing key gracefully falls back to the local engine, so the app never breaks.
Scoring calls run in parallel (up to 8 concurrent), so a 15-lead discovery takes only a few seconds.

---

## Enabling real data sources (optional)

- Set `HUNTER_API_KEY` in `backend/.env` to query real domain/contact data from Hunter.io.
- The web / Crunchbase / LinkedIn adapters ship with a realistic simulation layer; swap them for live APIs by replacing the classes in `backend/data_sources/`.

---

## Docker

```bash
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Interactive API docs (Swagger): http://localhost:8000/docs

---

## Project Structure

```
lead-platform/
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── main.py              # FastAPI app entrypoint
│   ├── config.py            # Settings (env-driven)
│   ├── database.py          # SQLAlchemy engine/session
│   ├── models/              # User, ICP, Company, Contact, Lead
│   ├── schemas/             # Pydantic request/response models
│   ├── routers/             # auth, icp, leads, discovery, export
│   ├── services/
│   │   ├── icp_parser.py        # NL → structured ICP (AI + fallback)
│   │   ├── lead_discovery.py    # parallel multi-source orchestrator
│   │   ├── contact_enrichment.py
│   │   ├── lead_scorer.py       # 0–100 scoring + explanations
│   │   └── deduplication.py     # fuzzy duplicate detection/merge
│   ├── data_sources/        # web / crunchbase / linkedin / hunter.io
│   └── smoke_test.py        # 37-check end-to-end API test
└── frontend/
    └── src/
        ├── app/             # landing, auth, dashboard, ICP, leads, detail
        ├── components/      # AuthPage, DashboardShell, UI primitives
        ├── lib/api.ts       # typed API client + session helpers
        └── types/           # shared TypeScript types
```

---

## How it works

```
User types ICP in natural language (e.g. "Mid-sized US SaaS companies…")
  → AI / heuristic parser extracts industries, size, geography, tech, titles
  → User reviews & edits the structured criteria
  → Discovery engine queries 4 sources in parallel
  → Results are enriched & deduplicated (fuzzy domain/name/email match)
  → AI scores each lead 0–100 with per-criterion reasons
  → Leads ranked; user searches, filters, and exports CSV/JSON
```

Each `Lead` records its **score breakdown** (Industry, Company Size, Geography, Contact Relevance, Tech/Keyword Alignment) and a plain-English **explanation**, so sales teams know *why* a lead ranks where it does.

---

## Running the test suite

```bash
cd backend
.venv/bin/python smoke_test.py
```

Runs 37 checks covering auth, ICP parsing, discovery, enrichment, scoring, deduplication, search/filter, export, and cascade deletion. (37/37 passing.)

---

## License

Proprietary — all rights reserved by R Sashank Adithiyaa (GitHub: sus6756). Contact sashankmidhun@gmail.com for licensing requests. See [LICENSE](LICENSE).