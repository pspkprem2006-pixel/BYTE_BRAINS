# ByteBrains

**ByteBrains** is an AI-powered adaptive study companion for students.
It will help students upload study material, learn with an AI tutor, take
AI-generated quizzes, and follow an adaptive study plan that targets their
weak topics.

> Current status: **all core features implemented**. Upload study materials
> (PDF/TXT) with automatic text extraction, chat with an AI tutor grounded in
> your material, generate and take AI quizzes, get an adaptive AI study plan,
> and track progress on the dashboard. Session data (quiz results, weak
> topics, study plans) is kept in memory; student authentication and data
> persistence across sessions arrive in a later phase.

## Technology stack

| Layer      | Technology                          |
| ---------- | ----------------------------------- |
| Frontend   | React 19, Vite 7, TypeScript, Tailwind CSS 4 |
| Backend    | Python 3.13, FastAPI, Pydantic      |
| Database   | PostgreSQL with Alembic migrations  |
| AI         | OpenRouter (any supported chat model) |
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
│   │   ├── store/         # in-memory session state (quizzes, study plans)
│   │   └── services/      # API client (calls the FastAPI backend)
│   └── .env.example
├── backend/           # FastAPI service
│   ├── app/
│   │   ├── api/routes/   # HTTP endpoints (health lives here)
│   │   ├── core/         # configuration
│   │   ├── schemas/      # Pydantic request/response models
│   │   ├── services/     # business logic, material extraction, AI calls
│   │   └── models/       # database ORM models
│   └── .env.example
├── database/          # PostgreSQL setup documentation
├── docs/              # Documents (PHASES.md roadmap)
└── README.md
```

## Environment setup

Prerequisites: Node.js 20.19+ (or 22.12+), npm, Python 3.10+, PostgreSQL 15+.

1. Clone the repository.
2. Copy `.env.example` to `.env` where one is provided
   (`frontend/.env.example`, `backend/.env.example`) and adjust values.
   Real `.env` files are gitignored; never commit secrets.
3. Create the PostgreSQL database — see `database/README.md` for
   Windows-specific steps (`CREATE DATABASE bytebrains`, then put the
   connection URL in `backend/.env` as `DATABASE_URL`).
4. Apply migrations:

   ```bash
   cd backend
   .venv\Scripts\activate
   python -m alembic upgrade head
   ```

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

## How the AI works

ByteBrains calls the OpenRouter API (model configurable via
`OPENROUTER_MODEL` in `backend/.env`) for three features:

- **AI tutor** — answers questions grounded in the uploaded material text.
- **AI quizzes** — generates 5-question quizzes on the material's topics.
- **AI study plans** — builds a day-by-day plan targeting your weak topics.

AI responses are parsed from JSON with tolerant extraction; if the service
times out, returns garbage, or the API key is missing, the frontend shows a
clear error with a Retry button instead of crashing.

## Golden demo flow

1. Open http://localhost:5173 — Subjects → **Create** a subject (e.g.
   "Database Management Systems").
2. Materials → **Upload** a study file (TXT or PDF, up to 10 MB).
3. Tutor → ask **"Explain normalization in simple terms with an example."**
4. Quizzes → **Generate quiz** (5 questions) → answer → submit to see your
   score and weak topics.
5. Study Plan → generate a 3–5 day plan — it reuses your quiz weak topics.

## Known limitations

- No authentication — a single development user owns all data; sessions
  (quiz history, weak topics, study plans) are kept in the frontend's memory
  and are lost on refresh.
- Uploads are stored locally in `backend/uploads/` — no cloud storage.
- The AI model varies by OpenRouter availability; the tutor's answers are
  grounded in your material text only.

## Development phases

See `docs/PHASES.md` for the full roadmap. The project is deliberately built
one phase at a time — features beyond the current phase are not implemented.