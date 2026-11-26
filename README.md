# StudyFlow — Vivek's customized fork

A study-planning platform with a React frontend and FastAPI backend. This repository is a customized fork of [shreyas5080/studyflow](https://github.com/shreyas5080/studyflow), which is released under the MIT License. The upstream LICENSE file is retained; see **My changes** below for additions in this fork.

## Stack

- **Frontend:** React 19, Vite, React Router
- **Backend:** FastAPI, SQLAlchemy, Pydantic
- **Data and services:** PostgreSQL, Redis (OTP storage), Docker Compose
- **AI timetable generation:** optional external model credentials configured by the upstream application

## Current capabilities

- Account registration, email OTP verification, and JWT login
- Subject and syllabus-topic management
- Study timetable generation
- Docker Compose development environment
- Liveness and dependency-readiness health endpoints
- Configurable Redis connection and explicit CORS origin allowlist

## My changes

- Added `GET /health/live` for process liveness.
- Added `GET /health/ready` to check PostgreSQL and Redis and return HTTP 503 when a required dependency is unavailable.
- Replaced wildcard CORS with a configurable allowlist from `CORS_ORIGINS`.
- Made Redis connection details configurable through `REDIS_URL`, including Docker Compose service networking.
- Corrected the sample database URL to match the PostgreSQL service and added clearer local-versus-Docker setup notes.

## Run with Docker Compose

1. Copy `backend/.env.example` to `backend/.env`.
2. Replace `SECRET_KEY` with a long random value. Configure `BREVO_API_KEY` to enable email OTP delivery.
3. Start the services from the repository root:

   ```bash
   docker compose up --build
   ```

4. Create the database tables:

   ```bash
   docker compose exec backend python -m src.init_db
   ```

5. Open the frontend at `http://localhost:5173`. The API is at `http://localhost:8000`; interactive API documentation is at `http://localhost:8000/docs`.

The Docker environment file uses the internal service names `postgresql` and `redis`. If you run the API directly on your computer, change `SQL_URL` to use `localhost:5433` and `REDIS_URL` to `redis://localhost:6379/0`.

## Health checks

- `GET /health/live` returns `{"status":"alive"}` while the API process is running.
- `GET /health/ready` returns the status of PostgreSQL and Redis. It responds with `200` when both are reachable and `503` otherwise.

## Repository structure

- `FrontEnd/` — React/Vite client
- `backend/` — FastAPI application and API routes
- `docker-compose.yml` — frontend, API, PostgreSQL, and Redis services

## Attribution

This fork builds on work by [Shreyas](https://github.com/shreyas5080) and other contributors. Upstream code remains covered by the original MIT License. Changes made in this fork are documented above.
