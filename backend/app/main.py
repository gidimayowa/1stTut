from fastapi import FastAPI

from app.api.routes import router
from app.database import Base, engine

app = FastAPI(title="GDPR-aware XR Research Platform")
app.include_router(router, prefix="/api")


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
