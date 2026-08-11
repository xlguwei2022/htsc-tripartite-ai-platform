from __future__ import annotations
from typing import Optional
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base


class UniversityRule(Base):
    __tablename__ = "university_rules"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    code: Mapped[str] = mapped_column(String(16), nullable=False)
    mode: Mapped[str] = mapped_column(String(32), nullable=False)
    mode_label: Mapped[str] = mapped_column(String(32), nullable=False)
    platform: Mapped[str] = mapped_column(String(256), nullable=False)
    initiator: Mapped[str] = mapped_column(String(32), nullable=False)
    needs_seal: Mapped[bool] = mapped_column(Boolean, default=False)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=True)
    automation: Mapped[str] = mapped_column(String(64), nullable=False)
    sla_days: Mapped[int] = mapped_column(Integer, default=5)
    issues: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(256), default="")
    updated: Mapped[str] = mapped_column(String(16), default="")
    enterprise_reg: Mapped[str] = mapped_column(Text, default="")
    company_materials: Mapped[str] = mapped_column(Text, default="")
    latest_version: Mapped[str] = mapped_column(String(32), nullable=False)
    publish_status: Mapped[str] = mapped_column(String(32), nullable=False)
    last_published_version: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    effective_from: Mapped[str] = mapped_column(String(32), default="—")
    verified_by: Mapped[str] = mapped_column(String(128), default="待复核")
    verified_at: Mapped[str] = mapped_column(String(32), default="—")
    evidence_id: Mapped[str] = mapped_column(String(64), default="")
    maintainer: Mapped[str] = mapped_column(String(128), default="华泰证券 HR数字化组")
    verified: Mapped[str] = mapped_column(String(16), default="待核验")
    versions: Mapped[list["RuleVersion"]] = relationship(back_populates="university", cascade="all, delete-orphan")


class RuleVersion(Base):
    __tablename__ = "rule_versions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    university_id: Mapped[str] = mapped_column(ForeignKey("university_rules.id"), index=True)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    date: Mapped[str] = mapped_column(String(16), nullable=False)
    change_note: Mapped[str] = mapped_column(Text, default="")
    university: Mapped[UniversityRule] = relationship(back_populates="versions")
    __table_args__ = (UniqueConstraint("university_id", "version", name="uq_rule_version"),)


class TripartiteTask(Base):
    __tablename__ = "tripartite_tasks"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    candidate_name: Mapped[str] = mapped_column(String(128), nullable=False)
    university_id: Mapped[str] = mapped_column(ForeignKey("university_rules.id"), index=True)
    position: Mapped[str] = mapped_column(String(256), nullable=False)
    offer_date: Mapped[str] = mapped_column(String(16), nullable=False)
    deadline: Mapped[str] = mapped_column(String(16), nullable=False)
    current_step: Mapped[int] = mapped_column(Integer, default=2)
    node_entered_at: Mapped[str] = mapped_column(String(32), nullable=False)
    completed_at: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    risk: Mapped[str] = mapped_column(String(32), default="normal")
    rule_version_pinned: Mapped[str] = mapped_column(String(32), default="待发布")
    rule_source_pinned: Mapped[str] = mapped_column(String(256), default="")
    workflow_version: Mapped[str] = mapped_column(String(64), nullable=False)
    trace_id: Mapped[str] = mapped_column(String(96), nullable=False, unique=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, unique=True)


class TaskEvent(Base):
    __tablename__ = "task_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("tripartite_tasks.id"), index=True)
    event_id: Mapped[str] = mapped_column(String(96), unique=True, nullable=False)
    occurred_at: Mapped[str] = mapped_column(String(32), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    result: Mapped[str] = mapped_column(String(32), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), default="DOMAIN_EVENT")


class Anomaly(Base):
    __tablename__ = "anomalies"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    task_id: Mapped[Optional[str]] = mapped_column(ForeignKey("tripartite_tasks.id"), nullable=True, index=True)
    candidate_name: Mapped[str] = mapped_column(String(128), nullable=False)
    university_name: Mapped[str] = mapped_column(String(128), nullable=False)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    days: Mapped[int] = mapped_column(Integer, default=0)
    risk: Mapped[str] = mapped_column(String(16), nullable=False)
    analysis: Mapped[str] = mapped_column(Text, nullable=False)
    suggestion: Mapped[str] = mapped_column(Text, nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=0)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)


class ConnectorExecution(Base):
    __tablename__ = "connector_executions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("tripartite_tasks.id"), index=True)
    connector_type: Mapped[str] = mapped_column(String(32), nullable=False)
    node_id: Mapped[str] = mapped_column(String(32), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=1)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[str] = mapped_column(String(32), nullable=False)
    finished_at: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)


class InboxEvent(Base):
    __tablename__ = "inbox_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_event_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    task_id: Mapped[str] = mapped_column(String(64), index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    received_at: Mapped[str] = mapped_column(String(32), nullable=False)


class OutboxEvent(Base):
    __tablename__ = "outbox_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    aggregate_id: Mapped[str] = mapped_column(String(64), index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING")
    created_at: Mapped[str] = mapped_column(String(32), nullable=False)
    published_at: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(96), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(96), nullable=False)
    before_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    after_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    trace_id: Mapped[Optional[str]] = mapped_column(String(96), nullable=True)
    occurred_at: Mapped[str] = mapped_column(String(32), nullable=False)


class RuntimeLog(Base):
    __tablename__ = "runtime_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    time: Mapped[str] = mapped_column(String(16), nullable=False)
    level: Mapped[str] = mapped_column(String(16), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
