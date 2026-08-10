# Database (PostgreSQL)

ByteBrains uses PostgreSQL as its database. This document explains, step by
step, how to get the database running on Windows and connect the backend to
it. Migrations are managed with **Alembic** — the migration files are the
source of truth for the schema.

## 1. Install PostgreSQL (if you don't have it)

1. Download the installer from https://www.postgresql.org/download/windows/
2. Run the installer and note the **postgres superuser password** you set
   during installation (you will need it below).
3. Leave the default port `5432`.
4. After installation, the PostgreSQL service should be running. You can
   check in Windows Services (`services.msc`, look for
   `postgresql-x64-18`) or run:
   ```powershell
   & "C:\Program Files\PostgreSQL\18\bin\pg_isready.exe"
   ```
   Expected output: `:5432 - accepting connections`

## 2. Create the ByteBrains database

Run this command from PowerShell (replace the password with yours):

```powershell
$env:PGPASSWORD = "YOUR_PASSWORD"
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost -c "CREATE DATABASE bytebrains;"
Remove-Item Env:PGPASSWORD
```

Expected output: `CREATE DATABASE`

## 3. Configure DATABASE_URL

1. In the backend folder, copy the template:
   ```powershell
   Copy-Item .env.example .env
   ```
2. Open `backend\.env` and edit the `DATABASE_URL` value:
   ```
   DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/bytebrains
   ```
   - `postgresql+psycopg` — the psycopg (psycopg 3) driver
   - `postgres` — username (the superuser from step 1)
   - `YOUR_PASSWORD` — the password from step 1
   - `localhost:5432` — server address and port
   - `bytebrains` — the database name from step 2
3. **Special characters** in the password must be percent-encoded
   (`@` becomes `%40`, `#` becomes `%23`). If your password is `my@secret`,
   the URL would be `...postgres:my%40secret@localhost:5432/bytebrains`.
4. `.env` is gitignored — the real credentials never enter Git.

### Database URL basics

| Part                  | Meaning                        | Example                  |
| --------------------- | ------------------------------ | ------------------------ |
| `postgresql+psycopg`  | Driver used by SQLAlchemy      | `postgresql+psycopg`     |
| `USER:PASSWORD@HOST`  | Login                          | `postgres:secret@localhost` |
| `:PORT`               | PostgreSQL port                | `5432`                   |
| `/DBNAME`             | Database name                  | `/bytebrains`            |

## 4. Activate the backend virtual environment

```powershell
cd D:\BYTE_BRAINS\backend
python -m venv .venv          # first time only
.\.venv\Scripts\activate      # PowerShell
pip install -r requirements.txt
```

## 5. Run Alembic migrations

From inside the backend folder (virtual environment active):

```powershell
alembic upgrade head
```

Expected output ends with:
`Running upgrade -> 8a8a027bf1c8, create initial tables`

The migration **creates all tables**, including foreign keys, indexes,
unique constraints and check constraints.

## 6. Verify the tables exist

```powershell
$env:PGPASSWORD = "YOUR_PASSWORD"
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost -d bytebrains -c "\dt"
Remove-Item Env:PGPASSWORD
```

You should see these tables (plus `alembic_version`, used by Alembic):

```
alembic_version   materials       quiz_attempts  study_plans  study_tasks
subjects          topics          user_progress  users
```

Alternatively, ask the API:
`http://localhost:8000/health/db` should return
`{"status": "ok", "database": "connected"}`.

## 7. Roll back the latest migration

```powershell
alembic downgrade base    # drops all tables (back to an empty database)
alembic upgrade head      # re-applies everything
```

Use this workflow when experimenting with schema changes.

## 8. Start the backend

```powershell
uvicorn app.main:app --reload
```

- API root: http://localhost:8000
- Health check: http://localhost:8000/health
- Database check: http://localhost:8000/health/db
- Interactive docs: http://localhost:8000/docs

## Quick reference (all commands)

```powershell
# one-time setup
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

# create database (needs your postgres password)
psql -U postgres -h localhost -c "CREATE DATABASE bytebrains;"

# configure backend\.env with DATABASE_URL, then:
alembic upgrade head

# verify
alembic current
psql -U postgres -h localhost -d bytebrains -c "\dt"

# rollback / reapply
alembic downgrade base
alembic upgrade head

# run the API
uvicorn app.main:app --reload
```

## Schema notes

- All primary keys are UUIDs.
- Timestamps are timezone-aware (`created_at`, `updated_at`).
- `user_progress` keeps one row per (user, topic) — enforced by a unique
  constraint.
- `mastery_score` and quiz `score` are percentages constrained to 0-100.
- `materials.processing_status` is a string limited to
  `uploaded / processing / processed / failed` by a check constraint.
- Cascade behavior: deleting a user deletes their data; deleting a subject
  keeps materials (their subject link becomes NULL) but blocks quiz-attempt
  deletion via RESTRICT only when attempts exist; deleting a topic keeps
  quiz attempts and study tasks (link becomes NULL).
- The database itself is never created by Python code — always create it
  with `CREATE DATABASE` first, then let Alembic build the schema.