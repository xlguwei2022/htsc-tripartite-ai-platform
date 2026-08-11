from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import UniversityRule, RuleVersion, TripartiteTask, TaskEvent, Anomaly, RuntimeLog, ConnectorExecution, OutboxEvent, AuditLog
from .config import APP_ENV, APP_VERSION, DATABASE_KIND


def rule_dict(session: Session, u: UniversityRule):
    versions = session.scalars(select(RuleVersion).where(RuleVersion.university_id == u.id).order_by(RuleVersion.id.desc())).all()
    return {"id":u.id,"name":u.name,"code":u.code,"mode":u.mode,"modeLabel":u.mode_label,"platform":u.platform,"initiator":u.initiator,"needsSeal":u.needs_seal,"needsReview":u.needs_review,"automation":u.automation,"sla":u.sla_days,"issues":u.issues,"source":u.source,"updated":u.updated,"enterpriseReg":u.enterprise_reg,"companyMaterials":u.company_materials,"ruleVersion":u.latest_version,"maintainer":u.maintainer,"verified":u.verified,"publishStatus":u.publish_status,"effectiveFrom":u.effective_from,"verifiedBy":u.verified_by,"verifiedAt":u.verified_at,"evidenceId":u.evidence_id,"lastPublishedVersion":u.last_published_version,"lastPublishedAt":"2026-06-25" if u.last_published_version and u.last_published_version != u.latest_version else u.updated,"history":[{"version":v.version,"date":v.date,"status":v.status,"change":v.change_note} for v in versions]}


def task_dict(session: Session, t: TripartiteTask):
    events = session.scalars(select(TaskEvent).where(TaskEvent.task_id == t.id).order_by(TaskEvent.id.desc()).limit(12)).all()
    return {"id":t.id,"name":t.candidate_name,"uni":t.university_id,"position":t.position,"offerDate":t.offer_date,"deadline":t.deadline,"currentStep":t.current_step,"nodeEnteredAt":t.node_entered_at,"completedAt":t.completed_at,"risk":t.risk,"ruleVersionPinned":t.rule_version_pinned,"ruleSourcePinned":t.rule_source_pinned,"workflowVersion":t.workflow_version,"traceId":t.trace_id,"version":t.version,"events":[{"eventId":e.event_id,"time":e.occurred_at[5:16],"source":e.source,"result":e.result,"msg":e.message} for e in events]}


def anomaly_dict(a: Anomaly):
    return {"id":a.id,"taskId":a.task_id,"cand":a.candidate_name,"uni":a.university_name,"type":a.type,"desc":a.description,"days":a.days,"risk":a.risk,"analysis":a.analysis,"suggestion":a.suggestion,"level":a.level,"state":a.state,"status":a.status}


def bootstrap(session: Session):
    rules = session.scalars(select(UniversityRule).order_by(UniversityRule.id)).all()
    tasks = session.scalars(select(TripartiteTask).order_by(TripartiteTask.id)).all()
    anomalies = session.scalars(select(Anomaly).order_by(Anomaly.id)).all()
    logs = session.scalars(select(RuntimeLog).order_by(RuntimeLog.id.desc()).limit(100)).all()
    connectors = session.scalars(select(ConnectorExecution).order_by(ConnectorExecution.id.desc()).limit(100)).all()
    outbox = session.scalars(select(OutboxEvent).order_by(OutboxEvent.id.desc()).limit(50)).all()
    audits = session.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(50)).all()
    return {"mode":"backend","base_date":"2026-08-10","runtime":{"version":APP_VERSION,"database":DATABASE_KIND,"environment":APP_ENV,"persistence":True,"shared_demo_state":True},"rules":[rule_dict(session,u) for u in rules],"tasks":[task_dict(session,t) for t in tasks],"anomalies":[anomaly_dict(a) for a in anomalies],"runtime_logs":[{"time":l.time,"level":l.level,"source":l.source,"msg":l.message} for l in logs],"connector_executions":[{"task_id":c.task_id,"connector_type":c.connector_type,"node_id":c.node_id,"state":c.state,"attempts":c.attempts,"last_error":c.last_error} for c in connectors],"outbox":[{"id":o.id,"aggregate_id":o.aggregate_id,"event_type":o.event_type,"status":o.status,"created_at":o.created_at} for o in outbox],"audit":[{"id":a.id,"actor":a.actor,"action":a.action,"entity_type":a.entity_type,"entity_id":a.entity_id,"trace_id":a.trace_id,"occurred_at":a.occurred_at} for a in audits]}
