-- Initial schema migration for XR research platform.

CREATE TABLE IF NOT EXISTS studies (
  id SERIAL PRIMARY KEY,
  study_id VARCHAR(64) UNIQUE NOT NULL,
  name VARCHAR(255) NOT NULL,
  retention_days INTEGER NOT NULL DEFAULT 365,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS participants (
  id SERIAL PRIMARY KEY,
  participant_id VARCHAR(128) UNIQUE NOT NULL,
  study_id VARCHAR(64) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sessions (
  id SERIAL PRIMARY KEY,
  session_id VARCHAR(128) UNIQUE NOT NULL,
  participant_id VARCHAR(128) NOT NULL,
  study_id VARCHAR(64) NOT NULL,
  condition_id VARCHAR(64) NOT NULL,
  task_id VARCHAR(64) NOT NULL DEFAULT 'unknown',
  start_time_utc TIMESTAMP NOT NULL,
  duration_sec DOUBLE PRECISION NOT NULL,
  completion_status VARCHAR(32) NOT NULL,
  total_errors INTEGER NOT NULL,
  hints_used INTEGER NOT NULL,
  task_completion_time_sec DOUBLE PRECISION NOT NULL,
  score DOUBLE PRECISION,
  content_hash VARCHAR(64) UNIQUE NOT NULL,
  raw_artifact_path TEXT NOT NULL,
  anomaly_flag BOOLEAN NOT NULL DEFAULT FALSE,
  anomaly_reason TEXT,
  uploaded_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS events (
  id SERIAL PRIMARY KEY,
  event_id UUID UNIQUE NOT NULL,
  session_id VARCHAR(128) NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
  participant_id VARCHAR(128) NOT NULL,
  study_id VARCHAR(64) NOT NULL,
  condition_id VARCHAR(64) NOT NULL,
  task_id VARCHAR(64) NOT NULL,
  event_type VARCHAR(64) NOT NULL,
  object_id VARCHAR(128),
  tool_id VARCHAR(128),
  hand VARCHAR(16) NOT NULL,
  timestamp_utc TIMESTAMP NOT NULL,
  time_since_session_start_ms INTEGER NOT NULL,
  position JSONB,
  rotation JSONB,
  extra JSONB NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS computed_metrics (
  id SERIAL PRIMARY KEY,
  session_id VARCHAR(128) NOT NULL,
  metric_name VARCHAR(128) NOT NULL,
  metric_value DOUBLE PRECISION NOT NULL,
  dimension JSONB NOT NULL DEFAULT '{}',
  computed_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS analysis_runs (
  id SERIAL PRIMARY KEY,
  run_id VARCHAR(64) UNIQUE NOT NULL,
  study_id VARCHAR(64) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  exclusions_applied JSONB NOT NULL DEFAULT '{}',
  tests_run JSONB NOT NULL DEFAULT '{}',
  result_summary JSONB NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS artifacts (
  id SERIAL PRIMARY KEY,
  artifact_id VARCHAR(64) UNIQUE NOT NULL,
  artifact_type VARCHAR(32) NOT NULL,
  path TEXT NOT NULL,
  mime_type VARCHAR(64) NOT NULL DEFAULT 'application/octet-stream',
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(32) NOT NULL DEFAULT 'viewer'
);
