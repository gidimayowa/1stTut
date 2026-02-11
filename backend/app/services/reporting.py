import uuid
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


EXPORT_DIR = Path("artifacts/exports")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def write_analysis_report(payload: dict) -> dict[str, str]:
    run_id = payload.get("run_id", "manual")
    artifact_id = str(uuid.uuid4())
    html_path = EXPORT_DIR / f"analysis_{artifact_id}.html"
    pdf_path = EXPORT_DIR / f"analysis_{artifact_id}.pdf"

    html = f"""
    <html><body>
      <h1>Analysis Report {run_id}</h1>
      <h2>Dataset summary</h2>
      <pre>{payload.get('dataset_summary', {})}</pre>
      <h2>Exclusions applied</h2>
      <pre>{payload.get('provenance', {})}</pre>
      <h2>Tests run & results</h2>
      <pre>{payload.get('results', {})}</pre>
    </body></html>
    """
    html_path.write_text(html, encoding="utf-8")

    c = canvas.Canvas(str(pdf_path), pagesize=A4)
    c.drawString(40, 800, f"Analysis Report: {run_id}")
    c.drawString(40, 780, f"Dataset summary: {str(payload.get('dataset_summary', {}))[:110]}")
    c.drawString(40, 760, f"Exclusions: {str(payload.get('provenance', {}))[:110]}")
    c.drawString(40, 740, f"Results: {str(payload.get('results', {}))[:110]}")
    c.save()

    return {
        "artifact_id": artifact_id,
        "html": str(html_path),
        "pdf": str(pdf_path),
    }
