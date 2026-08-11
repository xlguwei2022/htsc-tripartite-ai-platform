from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Response
from fastapi.responses import FileResponse
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from .config import APP_ENV, APP_NAME, APP_VERSION, DATABASE_KIND, DEMO_BASE_DATE, FRONTEND_PATH
from .db import SessionLocal, init_db
from .models import AuditLog, OutboxEvent, UniversityRule
from .schemas import (
    AcceptAnomalyIn,
    PublishRuleIn,
    ResolveAnomalyIn,
    TaskCreate,
    TaskEventIn,
)
from .seed import reset_seed
from .serializers import anomaly_dict, bootstrap, rule_dict, task_dict
from .service import (
    accept_anomaly,
    complete_current_node,
    create_task,
    manual_takeover,
    publish_rule,
    reconcile,
    resolve_anomaly,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    with SessionLocal() as db:
        if not db.scalar(select(UniversityRule.id).limit(1)):
            reset_seed(db)
    yield


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=(
        "校招三方协议全流程 Runtime PoC：规则治理、Workflow 状态机、"
        "Connector Mock、Inbox/Outbox、审计与异常人工接管。"
    ),
    lifespan=lifespan,
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(FRONTEND_PATH)


@app.head("/", include_in_schema=False)
def index_head():
    # Render's port detector probes HEAD /. Return 200 without loading the UI body.
    return Response(status_code=200)


@app.get("/api/health", tags=["Runtime"])
def health(db: Session = Depends(get_db)):
    # Readiness includes a minimal database round-trip.
    db.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "version": APP_VERSION,
        "runtime": f"FastAPI + {DATABASE_KIND} + Workflow Engine",
        "database": DATABASE_KIND,
        "environment": APP_ENV,
        "persistence": True,
        "demo_base_date": DEMO_BASE_DATE,
    }


@app.get("/api/bootstrap", tags=["Runtime"])
def api_bootstrap(db: Session = Depends(get_db)):
    return bootstrap(db)


@app.post("/api/tasks", tags=["Tasks"])
def api_create_task(body: TaskCreate, db: Session = Depends(get_db)):
    task = create_task(db, body)
    return task_dict(db, task)


@app.post("/api/tasks/{task_id}/events", tags=["Tasks"])
def api_task_event(task_id: str, body: TaskEventIn, db: Session = Depends(get_db)):
    task, duplicate = complete_current_node(
        db,
        task_id,
        body.external_event_id,
        body.event_type,
        body.expected_version,
    )
    return {"duplicate": duplicate, "task": task_dict(db, task)}


@app.post("/api/rules/{university_id}/publish", tags=["Rules"])
def api_publish_rule(
    university_id: str,
    body: PublishRuleIn,
    db: Session = Depends(get_db),
):
    rule = publish_rule(db, university_id, body.actor, body.change_note)
    return rule_dict(db, rule)


@app.post("/api/anomalies/{anomaly_id}/resolve", tags=["Anomalies"])
def api_resolve(
    anomaly_id: str,
    body: ResolveAnomalyIn,
    db: Session = Depends(get_db),
):
    return anomaly_dict(resolve_anomaly(db, anomaly_id, body.actor))


@app.post("/api/anomalies/{anomaly_id}/accept", tags=["Anomalies"])
def api_accept(
    anomaly_id: str,
    body: AcceptAnomalyIn,
    db: Session = Depends(get_db),
):
    return anomaly_dict(accept_anomaly(db, anomaly_id, body.actor))


@app.post("/api/anomalies/{anomaly_id}/takeover", tags=["Anomalies"])
def api_takeover(
    anomaly_id: str,
    body: AcceptAnomalyIn,
    db: Session = Depends(get_db),
):
    return anomaly_dict(manual_takeover(db, anomaly_id, body.actor))


@app.post("/api/reconcile", tags=["Operations"])
def api_reconcile(db: Session = Depends(get_db)):
    return reconcile(db)


@app.post("/api/reset", tags=["Operations"])
def api_reset(db: Session = Depends(get_db)):
    # PoC-only endpoint: restores deterministic simulated demo data.
    init_db()
    reset_seed(db)
    return {"ok": True}


@app.get("/api/outbox", tags=["Observability"])
def api_outbox(db: Session = Depends(get_db)):
    rows = db.scalars(
        select(OutboxEvent).order_by(OutboxEvent.id.desc()).limit(100)
    ).all()
    return [
        {
            "id": row.id,
            "aggregate_id": row.aggregate_id,
            "event_type": row.event_type,
            "status": row.status,
            "created_at": row.created_at,
        }
        for row in rows
    ]


@app.get("/api/audit", tags=["Observability"])
def api_audit(db: Session = Depends(get_db)):
    rows = db.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(100)).all()
    return [
        {
            "id": row.id,
            "actor": row.actor,
            "action": row.action,
            "entity_type": row.entity_type,
            "entity_id": row.entity_id,
            "trace_id": row.trace_id,
            "occurred_at": row.occurred_at,
        }
        for row in rows
    ]
