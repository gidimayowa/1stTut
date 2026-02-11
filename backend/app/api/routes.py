from io import BytesIO

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AnalysisRun, ComputedMetric, Event, Session as SessionModel
from app.schemas import AnalysisRequest
from app.services.analysis import run_analysis
from app.services.exclusions import apply_exclusions
from app.services.ingestion import hash_content, parse_and_validate, persist_raw_artifact
from app.services.metrics import compute_session_metrics
from app.services.reporting import write_analysis_report

router = APIRouter()


@router.post("/ingest")
def ingest(files: list[UploadFile] = File(...), db: Session = Depends(get_db)):
    results = []
    for file in files:
        content = file.file.read()
        content_hash = hash_content(content)

        existing = db.scalar(select(SessionModel).where(SessionModel.content_hash == content_hash))
        if existing:
            results.append({"filename": file.filename, "status": "duplicate", "session_id": existing.session_id})
            continue

        try:
            parsed = parse_and_validate(file.filename, content)
        except ValueError as exc:
            results.append({"filename": file.filename, "status": "error", "detail": str(exc)})
            continue

        artifact_path = persist_raw_artifact(file.filename, content_hash, content)
        summary = parsed.session_summary
        session = SessionModel(
            session_id=summary.session_id,
            participant_id=summary.participant_id,
            study_id=summary.study_id,
            condition_id=summary.condition_id,
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

        for event in parsed.events:
            db.add(
                Event(
                    event_id=event.event_id,
                    session_id=summary.session_id,
                    participant_id=event.participant_id,
                    study_id=event.study_id,
                    condition_id=event.condition_id,
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
            )

        db.commit()
        results.append({"filename": file.filename, "status": "ingested", "session_id": summary.session_id})

    return {"results": results}


@router.post("/metrics/recompute")
def recompute_metrics(study_id: str, db: Session = Depends(get_db)):
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

    return {"computed": int(len(metric_df))}


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
        tests_run={"dependent": request.dependent_variable, "group": request.group_variable},
        result_summary=results,
    )
    db.add(run)
    db.commit()

    return {"provenance": provenance, "results": results}


@router.get("/exports/cleaned.csv")
def export_cleaned(study_id: str, db: Session = Depends(get_db)):
    sessions = db.execute(select(SessionModel).where(SessionModel.study_id == study_id)).scalars().all()
    df = pd.DataFrame(
        [
            {
                "participant_id": s.participant_id,
                "study_id": s.study_id,
                "condition_id": s.condition_id,
                "session_id": s.session_id,
                "duration_sec": s.duration_sec,
                "task_completion_time_sec": s.task_completion_time_sec,
                "total_errors": s.total_errors,
            }
            for s in sessions
        ]
    )
    output = BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)

    path = "artifacts/exports/cleaned_dataset.csv"
    with open(path, "wb") as f:
        f.write(output.read())
    return FileResponse(path=path, filename="cleaned_dataset.csv", media_type="text/csv")


@router.delete("/participants/{participant_id}")
def delete_participant(participant_id: str, db: Session = Depends(get_db)):
    sessions = db.execute(select(SessionModel).where(SessionModel.participant_id == participant_id)).scalars().all()
    for session in sessions:
        db.delete(session)
    db.commit()
    return {"deleted_participant_id": participant_id, "deleted_sessions": len(sessions)}


@router.post("/analysis/report")
def create_report(payload: dict):
    run_id = payload.get("run_id", "manual")
    paths = write_analysis_report(run_id, payload)
    return {"artifacts": paths}
