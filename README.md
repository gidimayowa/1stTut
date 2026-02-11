# GDPR-aware XR Research Data Platform (FastAPI + React + PostgreSQL)

## Run locally

```bash
docker compose up --build
```

Services:
- Frontend: http://localhost:5173
- Backend docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

## Upload sample data workflow

1. Generate sample files:
```bash
python scripts/generate_sample_data.py
```
2. In UI, open **Ingest Data** card.
3. Set `study_id` and `condition_id`.
4. Select multiple `sample_data/*.jsonl` and/or `sample_data/*.csv` files.
5. Click **Upload & ingest**.
6. Recompute metrics (automatic after upload, can be run manually too).

## Frontend capabilities delivered

- Multi-file CSV/JSONL upload with per-file ingest results.
- Global filters (study/condition/task/date/anomalies).
- KPI strip (participants, sessions, completion stats, error stats, last ingest).
- Metrics recompute action.
- Analysis runner with exclusion rule editor and run history.
- Exports (cleaned CSV + generated report download link).
- Session inspector table and event timeline plot.
- Anomaly badge support.

## API endpoints powering the UI

### Existing + enhanced
- `POST /api/ingest` (multipart: files + study_id + condition_id + optional task_id)
- `POST /api/metrics/recompute`
- `POST /api/analysis/run`
- `GET /api/exports/cleaned.csv`
- `POST /api/analysis/report`
- `DELETE /api/participants/{participant_id}`

### Added
- `GET /api/studies`
- `GET /api/conditions?study_id=...`
- `GET /api/tasks?study_id=...`
- `GET /api/summary`
- `GET /api/sessions`
- `GET /api/sessions/{session_id}`
- `GET /api/sessions/{session_id}/events`
- `GET /api/analysis/runs`
- `GET /api/analysis/runs/{run_id}`
- `GET /api/artifacts/{artifact_id}`

## Environment configuration

Frontend API URL is configured via:
- `VITE_API_URL` (default: `http://localhost:8000`)

## Backend notes

- CORS is enabled for `http://localhost:5173`.
- Backend Docker image creates `/app/artifacts/*` directories at build time, so no host-side manual artifact folder creation is required.
