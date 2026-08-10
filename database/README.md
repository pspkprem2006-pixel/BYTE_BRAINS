# Database (PostgreSQL)

ByteBrains uses PostgreSQL as its database. Schema and code arrive in a later
phase. This folder currently holds only configuration documentation.

## Connection configuration

Credentials are managed through environment variables only — never hardcoded.
The backend already loads them from `backend/.env` via `pydantic-settings`
(see `backend/app/core/config.py`).

Planned variables (not yet used):

| Variable        | Example value       | Purpose                |
| --------------- | ------------------- | ---------------------- |
| `DATABASE_URL`  | `postgresql+psycopg://user:pass@localhost:5432/bytebrains` | Full SQLAlchemy/async connection string |
| `DB_HOST`       | `localhost`         | PostgreSQL host        |
| `DB_PORT`       | `5432`              | PostgreSQL port        |
| `DB_USER`       | `bytebrains`        | Database user          |
| `DB_PASSWORD`   | *(your secret)*     | Database password      |
| `DB_NAME`       | `bytebrains`        | Database name          |

## Local PostgreSQL setup (reference for the database phase)

1. Install PostgreSQL and start the service.
2. Create a user and database:

   ```sql
   CREATE USER bytebrains WITH PASSWORD 'change-me';
   CREATE DATABASE bytebrains OWNER bytebrains;
   ```

3. Fill in the values in `backend/.env` (copy from `backend/.env.example`).

## Design notes

- The full schema (students, subjects, topics, materials, quizzes, results,
  performance metrics) is intentionally deferred until the database phase.
- Migrations tooling will be chosen and documented in that phase.