# GDPR-aware XR Research Data Platform (FastAPI + React + PostgreSQL)

This repository now includes a complete MVP web platform for ingesting Unity XR session logs, validating them, computing metrics, running statistical analysis, and exporting research artifacts.

## What is included

- `backend/` FastAPI API with ingestion, metrics, analyses, exclusions, and exports.
- `frontend/` React + Plotly dashboard shell.
- `backend/migrations/0001_init.sql` SQL migration for PostgreSQL schema.
- `scripts/generate_sample_data.py` synthetic dataset generator (20+ sessions).
- `docs/unity_logging_guide.md` exact Unity log formatting guide.
- `docker-compose.yml` for local stack (frontend + backend + PostgreSQL).

## Quick start (local)

```bash
docker compose up --build
```

Services:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/docs
- PostgreSQL: localhost:5432

## Backend development without Docker

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/xr_research
uvicorn app.main:app --reload
```

## Ingestion contract

Upload `.jsonl` or `.csv` files where each file is one session.

- Deduplication uses SHA-256 content hash.
- Raw uploads are stored immutably under `backend/artifacts/raw_uploads/`.
- Schema errors return per-file details.

## Database tables

- `studies`
- `participants`
- `sessions`
- `events`
- `computed_metrics`
- `analysis_runs`
- `users`

## Exclusion rules supported (MVP)

- `exclude_pretest_score_gt`
- `exclude_duration_lt`
- `exclude_missing_timestamp_pct_gt`

Each analysis run stores exclusion provenance (rules + removed counts).

## Statistical analyses

- Descriptives (mean, median, SD, CI)
- Shapiro-Wilk normality checks
- Two-group: Welch t-test + Mann-Whitney + Cohen's d
- Multi-group: ANOVA + Kruskal-Wallis + eta squared
- Repeated sessions: mixed effects model (statsmodels mixedlm)
- Multiple-comparison note (Holm-Bonferroni for post-hoc)

## Exports

- Cleaned dataset CSV via API (`/api/exports/cleaned.csv?study_id=...`)
- Computed metrics table available in DB/API recompute response
- Report artifacts can be added in `backend/artifacts/exports/`
- Plotly charts in frontend are exportable via built-in modebar

## Running tests

```bash
cd backend
PYTHONPATH=. pytest -q
```

## How to add new metrics

1. Open `backend/app/services/metrics.py`.
2. Add metric computation inside `compute_session_metrics`.
3. Add assertions in `backend/tests/test_metrics.py`.
4. Re-run tests.

## How to add new statistical tests

1. Open `backend/app/services/analysis.py`.
2. Add test logic in `run_analysis` and include p-values/effect sizes.
3. Extend API response contract if needed.
4. Add unit tests for the new branch.

## GDPR/privacy notes implemented

- Participant identifiers are pseudonymous only (no names in schema).
- Raw upload audit trail is immutable.
- Secrets are env-driven (`DATABASE_URL`); deploy with secret manager.
- Add TLS at reverse proxy (Nginx/Caddy/Traefik) for HTTPS in deployment.
- Per-study retention field is included on `studies.retention_days`.
- To delete a participant, remove participant-linked sessions/events (cascade) and record audit action.

## Deployment guidance

- Use managed PostgreSQL with backups.
- Deploy backend container behind HTTPS reverse proxy.
- Restrict CORS to approved dashboard domains.
- Configure encrypted secrets via environment or vault.

## Unity integration

Follow `docs/unity_logging_guide.md` exactly. Use `scripts/generate_sample_data.py` for end-to-end pipeline testing before collecting participant data.
