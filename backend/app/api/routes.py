from datetime import datetime
from io import BytesIO
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AnalysisRun, Artifact, ComputedMetric, Event, Session as SessionModel, Study
from app.schemas import AnalysisRequest
from app.services.analysis import run_analysis
from app.services.exclusions import apply_exclusions
from app.services.ingestion import hash_content, parse_and_validate, persist_raw_artifact
from app.services.metrics import compute_session_metrics
from app.services.reporting import write_analysis_report

router = APIRouter()


def apply_session_filters(query, study_id=None, condition_id=None, task_id=None, start_date=None, end_date=None, anomalies_only=False):
    if study_id:
        query = query.where(SessionModel.study_id == study_id)
    if condition_id:
        query = query.where(SessionModel.condition_id == condition_id)
    if task_id:
        query = query.where(SessionModel.task_id == task_id)
    if start_date:
        query = query.where(SessionModel.start_time_utc >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.where(SessionModel.start_time_utc <= datetime.fromisoformat(end_date))
    if anomalies_only:
        query = query.where(SessionModel.anomaly_flag.is_(True))
    return query


def detect_anomaly(events: list[Event], duration_sec: float) -> tuple[bool, str | None]:
    reasons: list[str] = []
    if duration_sec < 20 or duration_sec > 7200:
        reasons.append("duration_out_of_range")
    if events:
        ts = [e.timestamp_utc for e in events if e.timestamp_utc]
        missing = len(events) - len(ts)
        if len(events) and (missing / len(events)) > 0.2:
            reasons.append("missing_timestamps")
        if ts and any(ts[i] > ts[i + 1] for i in range(len(ts) - 1)):
            reasons.append("event_ordering")
    return (len(reasons) > 0, ",".join(reasons) if reasons else None)


@router.post("/ingest")
def ingest(
    files: list[UploadFile] = File(...),
    study_id: str = Form(...),
    condition_id: str = Form(...),
    task_id: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    results = []
    for file in files:
        content = file.file.read()
        content_hash = hash_content(content)

        existing = db.scalar(select(SessionModel).where(SessionModel.content_hash == content_hash))
        if existing:
            results.append(
                {
                    "filename": file.filename,
                    "status": "duplicate",
                    "session_id": existing.session_id,
                    "inserted_sessions": 0,
                    "inserted_events": 0,
                }
            )
            continue

        try:
            parsed = parse_and_validate(file.filename, content)
        except ValueError as exc:
            results.append(
                {
                    "filename": file.filename,
                    "status": "error",
                    "inserted_sessions": 0,
                    "inserted_events": 0,
                    "error": str(exc),
                }
            )
            continue

        artifact_path = persist_raw_artifact(file.filename, content_hash, content)
        summary = parsed.session_summary
        chosen_study = study_id or summary.study_id
        chosen_condition = condition_id or summary.condition_id
        chosen_task = task_id or (parsed.events[0].task_id if parsed.events else "unknown")

        session = SessionModel(
            session_id=summary.session_id,
            participant_id=summary.participant_id,
            study_id=chosen_study,
            condition_id=chosen_condition,
            task_id=chosen_task,
            start_time_utc=summary.start_time_utc,
            duration_sec=summary.duration_sec,
            completion_status=summary.completion_status.value,
            total_errors=summary.total_errors,
            hints_used=summary.hints_used,
            task_completion_time_sec=summary.task_completion_time_sec,
            score=summary.score,
            content_hash=content_hash,
            raw_artifact_path=artifact_path,
        )
        db.add(session)

        inserted_events = 0
        created_events: list[Event] = []
        for event in parsed.events:
            e = Event(
                event_id=event.event_id,
                session_id=summary.session_id,
                participant_id=event.participant_id,
                study_id=chosen_study,
                condition_id=chosen_condition,
                task_id=event.task_id,
                event_type=event.event_type,
                object_id=event.object_id,
                tool_id=event.tool_id,
                hand=event.hand.value,
                timestamp_utc=event.timestamp_utc,
                time_since_session_start_ms=event.time_since_session_start_ms,
                position=event.position,
                rotation=event.rotation,
                extra=event.extra,
            )
            created_events.append(e)
            db.add(e)
            inserted_events += 1

        session.anomaly_flag, session.anomaly_reason = detect_anomaly(created_events, session.duration_sec)

        if not db.scalar(select(Study).where(Study.study_id == chosen_study)):
            db.add(Study(study_id=chosen_study, name=chosen_study))

        db.commit()
        results.append(
            {
                "filename": file.filename,
                "status": "ingested",
                "session_id": summary.session_id,
                "inserted_sessions": 1,
                "inserted_events": inserted_events,
            }
        )

    return {"results": results, "ingested_at": datetime.utcnow().isoformat()}


@router.post("/metrics/recompute")
def recompute_metrics(study_id: str = Form(...), db: Session = Depends(get_db)):
    sessions = db.execute(select(SessionModel).where(SessionModel.study_id == study_id)).scalars().all()
    if not sessions:
        raise HTTPException(status_code=404, detail="No sessions for study")

    events = db.execute(select(Event).where(Event.study_id == study_id)).scalars().all()
    event_df = pd.DataFrame(
        [
            {
                "session_id": e.session_id,
                "event_type": e.event_type,
                "time_since_session_start_ms": e.time_since_session_start_ms,
                "task_id": e.task_id,
                "position": e.position,
            }
            for e in events
        ]
    )
    summary_df = pd.DataFrame(
        [
            {
                "session_id": s.session_id,
                "study_id": s.study_id,
                "condition_id": s.condition_id,
                "task_completion_time_sec": s.task_completion_time_sec,
            }
            for s in sessions
        ]
    )

    metric_df = compute_session_metrics(event_df, summary_df)
    db.query(ComputedMetric).delete()
    for row in metric_df.to_dict("records"):
        db.add(ComputedMetric(**row))
    db.commit()

    return {"computed": int(len(metric_df)), "updated_at": datetime.utcnow().isoformat()}


@router.post("/analysis/run")
def analysis_run(request: AnalysisRequest, db: Session = Depends(get_db)):
    sessions = db.execute(select(SessionModel).where(SessionModel.study_id == request.study_id)).scalars().all()
    if not sessions:
        raise HTTPException(status_code=404, detail="No sessions for study")

    df = pd.DataFrame(
        [
            {
                "participant_id": s.participant_id,
                "study_id": s.study_id,
                "condition_id": s.condition_id,
                "task_id": s.task_id,
                "session_id": s.session_id,
                "duration_sec": s.duration_sec,
                "task_completion_time_sec": s.task_completion_time_sec,
                "total_errors": s.total_errors,
                "missing_timestamps_pct": 0,
                "pretest_score": 0,
            }
            for s in sessions
        ]
    )
    filtered_df, provenance = apply_exclusions(df, [r.model_dump() for r in request.exclusions])
    results = run_analysis(filtered_df, request.dependent_variable, request.group_variable)

    run = AnalysisRun(
        run_id=results["run_id"],
        study_id=request.study_id,
        exclusions_applied=provenance,
        tests_run={
            "dependent": request.dependent_variable,
            "group": request.group_variable,
            "test_type": request.test_type,
            "auto_normality": request.auto_normality,
        },
        result_summary=results,
    )
    db.add(run)
    db.commit()

    return {"provenance": provenance, "results": results}


@router.get("/analysis/runs")
def list_analysis_runs(study_id: str | None = None, db: Session = Depends(get_db)):
    query = select(AnalysisRun)
    if study_id:
        query = query.where(AnalysisRun.study_id == study_id)
    runs = db.execute(query.order_by(AnalysisRun.created_at.desc())).scalars().all()
    return [{"run_id": r.run_id, "study_id": r.study_id, "created_at": r.created_at.isoformat()} for r in runs]


@router.get("/analysis/runs/{run_id}")
def get_analysis_run(run_id: str, db: Session = Depends(get_db)):
    run = db.scalar(select(AnalysisRun).where(AnalysisRun.run_id == run_id))
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return {
        "run_id": run.run_id,
        "study_id": run.study_id,
        "created_at": run.created_at.isoformat(),
        "exclusions_applied": run.exclusions_applied,
        "tests_run": run.tests_run,
        "result_summary": run.result_summary,
    }


@router.get("/exports/cleaned.csv")
def export_cleaned(study_id: str, db: Session = Depends(get_db)):
    sessions = db.execute(select(SessionModel).where(SessionModel.study_id == study_id)).scalars().all()
    df = pd.DataFrame(
        [
            {
                "participant_id": s.participant_id,
                "study_id": s.study_id,
                "condition_id": s.condition_id,
                "task_id": s.task_id,
                "session_id": s.session_id,
                "duration_sec": s.duration_sec,
                "task_completion_time_sec": s.task_completion_time_sec,
                "total_errors": s.total_errors,
                "anomaly_flag": s.anomaly_flag,
            }
            for s in sessions
        ]
    )
    output = BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)

    path = Path("artifacts/exports/cleaned_dataset.csv")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(output.read())
    return FileResponse(path=str(path), filename="cleaned_dataset.csv", media_type="text/csv")


@router.post("/analysis/report")
def create_report(payload: dict, db: Session = Depends(get_db)):
    report = write_analysis_report(payload)
    db.add(Artifact(artifact_id=report["artifact_id"], artifact_type="analysis_report", path=report["pdf"], mime_type="application/pdf"))
    db.commit()
    return {
        "artifact_id": report["artifact_id"],
        "artifact_path": report["pdf"],
        "download_url": f"/api/artifacts/{report['artifact_id']}",
    }


@router.get("/artifacts/{artifact_id}")
def download_artifact(artifact_id: str, db: Session = Depends(get_db)):
    artifact = db.scalar(select(Artifact).where(Artifact.artifact_id == artifact_id))
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return FileResponse(path=artifact.path, media_type=artifact.mime_type, filename=Path(artifact.path).name)


@router.delete("/participants/{participant_id}")
def delete_participant(participant_id: str, db: Session = Depends(get_db)):
    sessions = db.execute(select(SessionModel).where(SessionModel.participant_id == participant_id)).scalars().all()
    for session in sessions:
        db.delete(session)
    db.commit()
    return {"deleted_participant_id": participant_id, "deleted_sessions": len(sessions)}


@router.get("/studies")
def get_studies(db: Session = Depends(get_db)):
    studies = db.execute(select(Study.study_id).order_by(Study.study_id)).scalars().all()
    return studies


@router.get("/conditions")
def get_conditions(study_id: str, db: Session = Depends(get_db)):
    rows = db.execute(select(SessionModel.condition_id).where(SessionModel.study_id == study_id).distinct()).scalars().all()
    return rows


@router.get("/tasks")
def get_tasks(study_id: str, db: Session = Depends(get_db)):
    rows = db.execute(select(SessionModel.task_id).where(SessionModel.study_id == study_id).distinct()).scalars().all()
    return rows


@router.get("/summary")
def get_summary(
    study_id: str | None = None,
    condition_id: str | None = None,
    task_id: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    anomalies_only: bool = False,
    db: Session = Depends(get_db),
):
    query = apply_session_filters(select(SessionModel), study_id, condition_id, task_id, start_date, end_date, anomalies_only)
    sessions = db.execute(query).scalars().all()
    if not sessions:
        return {
            "participants": 0,
            "sessions": 0,
            "mean_completion_time": 0,
            "median_completion_time": 0,
            "mean_errors": 0,
            "last_ingest_timestamp": None,
        }

    completions = [s.task_completion_time_sec for s in sessions]
    errors = [s.total_errors for s in sessions]
    return {
        "participants": len({s.participant_id for s in sessions}),
        "sessions": len(sessions),
        "mean_completion_time": float(pd.Series(completions).mean()),
        "median_completion_time": float(pd.Series(completions).median()),
        "mean_errors": float(pd.Series(errors).mean()),
        "last_ingest_timestamp": max(s.uploaded_at for s in sessions).isoformat(),
    }


@router.get("/sessions")
def list_sessions(
    study_id: str | None = None,
    condition_id: str | None = None,
    task_id: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    anomalies_only: bool = False,
    limit: int = Query(default=200, le=1000),
    db: Session = Depends(get_db),
):
    query = apply_session_filters(select(SessionModel), study_id, condition_id, task_id, start_date, end_date, anomalies_only)
    sessions = db.execute(query.order_by(SessionModel.uploaded_at.desc()).limit(limit)).scalars().all()
    return [
        {
            "session_id": s.session_id,
            "participant_id": s.participant_id,
            "study_id": s.study_id,
            "condition_id": s.condition_id,
            "task_id": s.task_id,
            "duration_sec": s.duration_sec,
            "task_completion_time_sec": s.task_completion_time_sec,
            "total_errors": s.total_errors,
            "anomaly_flag": s.anomaly_flag,
            "anomaly_reason": s.anomaly_reason,
            "start_time_utc": s.start_time_utc.isoformat(),
        }
        for s in sessions
    ]


@router.get("/sessions/{session_id}")
def get_session(session_id: str, db: Session = Depends(get_db)):
    s = db.scalar(select(SessionModel).where(SessionModel.session_id == session_id))
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": s.session_id,
        "participant_id": s.participant_id,
        "study_id": s.study_id,
        "condition_id": s.condition_id,
        "task_id": s.task_id,
        "duration_sec": s.duration_sec,
        "task_completion_time_sec": s.task_completion_time_sec,
        "total_errors": s.total_errors,
        "hints_used": s.hints_used,
        "completion_status": s.completion_status,
        "anomaly_flag": s.anomaly_flag,
        "anomaly_reason": s.anomaly_reason,
    }


@router.get("/sessions/{session_id}/events")
def get_session_events(session_id: str, db: Session = Depends(get_db)):
    events = db.execute(select(Event).where(Event.session_id == session_id).order_by(Event.time_since_session_start_ms)).scalars().all()
    return [
        {
            "event_id": str(e.event_id),
            "event_type": e.event_type,
            "task_id": e.task_id,
            "time_since_session_start_ms": e.time_since_session_start_ms,
            "timestamp_utc": e.timestamp_utc.isoformat(),
            "hand": e.hand,
        }
        for e in events
    ]
