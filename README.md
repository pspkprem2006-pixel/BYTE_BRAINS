# ByteBrains

**ByteBrains** is an AI-powered adaptive study companion for students.
It will help students upload study material, learn with an AI tutor, take
AI-generated quizzes, and follow an adaptive study plan that targets their
weak topics.

> Current status: **Phase 2 — frontend UI shell**. The full application shell
> (sidebar, top bar, responsive navigation), all 8 routes, and the dashboard,
> AI tutor, subjects, materials, quizzes, progress, study plan and settings
> pages are built on demo data. No authentication, database schema, AI, or
> backend features are implemented yet.

## Technology stack

| Layer      | Technology                          |
| ---------- | ----------------------------------- |
| Frontend   | React 19, Vite 7, TypeScript, Tailwind CSS 4 |
| Backend    | Python 3.13, FastAPI, Pydantic      |
| Database   | PostgreSQL (configured in a later phase) |
| Tooling    | Git, `.env` environment variables   |

### Why TypeScript?

TypeScript was chosen over plain JavaScript because ByteBrains will grow into
a large, feature-rich application (AI tutor, quizzes, dashboards). Types make
data shapes explicit — exactly like Pydantic does on the backend — catch
errors at compile time instead of at runtime, and make refactoring safer as
features are added phase by phase.

## Project structure

```
ByteBrains/
├── frontend/          # React + Vite + TypeScript + Tailwind app
│   ├── src/
│   │   ├── components/    # layout (shell), ui primitives, domain components
│   │   ├── pages/         # one component per route
│   │   └── data/          # mockData.ts (temporary demo data)
│   └── .env.example
├── backend/           # FastAPI service
│   ├── app/
│   │   ├── api/routes/   # HTTP endpoints (health lives here)
│   │   ├── core/         # configuration
│   │   ├── schemas/      # Pydantic request/response models
│   │   ├── services/     # business logic (later phases)
│   │   └── models/       # database ORM models (later phases)
│   └── .env.example
├── database/          # PostgreSQL configuration documentation
├── docs/              # Documents (PHASES.md roadmap)
└── README.md
```

## Environment setup

Prerequisites: Node.js 20.19+ (or 22.12+), npm, Python 3.10+.

1. Clone the repository.
2. Copy `.env.example` to `.env` where one is provided
   (`frontend/.env.example`, `backend/.env.example`) and adjust values.
   Real `.env` files are gitignored; never commit secrets.

### Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 in the browser.

### Run the backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows (PowerShell)
source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API runs at http://localhost:8000. Interactive docs are at
http://localhost:8000/docs.

### Test `GET /health`

```bash
curl http://localhost:8000/health
# or in PowerShell:
Invoke-RestMethod http://localhost:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "ByteBrains API"
}
```

## Development phases

See `docs/PHASES.md` for the full roadmap. The project is deliberately built
one phase at a time — features beyond the current phase are not implemented.