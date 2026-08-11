from __future__ import annotations
from typing import Optional

import json
import re
import uuid
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .config import DEMO_BASE_DATE
from .models import (
    Anomaly,
    AuditLog,
    ConnectorExecution,
    InboxEvent,
    OutboxEvent,
    RuleVersion,
    RuntimeLog,
    TaskEvent,
    TripartiteTask,
    UniversityRule,
)
from .workflow import EVENT_BY_ACTOR, FLOWS, WORKFLOW_VERSIONS


def now_dt() -> str:
    return f"{DEMO_BASE_DATE} {datetime.now().strftime('%H:%M:%S')}"


def now_time() -> str:
    return datetime.now().strftime("%H:%M:%S")


def resolved_rule_version(rule: UniversityRule) -> Optional[str]:
    if rule.publish_status == "Published":
        return rule.latest_version
    return rule.last_published_version


def add_event(session: Session, task: TripartiteTask, source: str, message: str, result: str = "完成", event_type: str = "DOMAIN_EVENT", event_id: Optional[str] = None) -> str:
    eid = event_id or f"EVT-{task.id}-{uuid.uuid4().hex[:10]}"
    session.add(TaskEvent(task_id=task.id,event_id=eid,occurred_at=now_dt(),source=source,result=result,message=message,event_type=event_type))
    return eid


def add_outbox(session: Session, task: TripartiteTask, event_type: str, payload: dict) -> None:
    session.add(OutboxEvent(aggregate_id=task.id,event_type=event_type,payload_json=json.dumps(payload, ensure_ascii=False),status="PENDING",created_at=now_dt()))


def add_audit(session: Session, actor: str, action: str, entity_type: str, entity_id: str, before: Optional[dict], after: Optional[dict], trace_id: Optional[str] = None) -> None:
    session.add(AuditLog(actor=actor,action=action,entity_type=entity_type,entity_id=entity_id,before_json=json.dumps(before, ensure_ascii=False) if before else None,after_json=json.dumps(after, ensure_ascii=False) if after else None,trace_id=trace_id,occurred_at=now_dt()))


def create_anomaly(session: Session, task: TripartiteTask, type_: str, description: str, analysis: str, suggestion: str, level: int = 2, risk: str = "中", state: str = "待处理", status: str = "待处理") -> Anomaly:
    existing = session.scalar(select(Anomaly).where(Anomaly.task_id == task.id, Anomaly.type == type_, Anomaly.state != "已解决"))
    if existing:
        return existing
    count = session.scalar(select(func.count()).select_from(Anomaly)) or 0
    rule = session.get(UniversityRule, task.university_id)
    anomaly = Anomaly(id=f"AN{count + 1:03d}",task_id=task.id,candidate_name=task.candidate_name,university_name=rule.name,type=type_,description=description,days=0,risk=risk,analysis=analysis,suggestion=suggestion,level=level,state=state,status=status)
    session.add(anomaly)
    return anomaly


def source_for_step(step: dict) -> str:
    if step.get("actor") == "RPA":
        return "RPA"
    if step.get("actor") == "AI":
        return "AI"
    return "Workflow"


def run_until_wait(session: Session, task: TripartiteTask) -> TripartiteTask:
    rule = session.get(UniversityRule, task.university_id)
    flow = FLOWS[rule.mode]
    while task.current_step < len(flow):
        step = flow[task.current_step]
        if not step.get("auto"):
            break
        if step["id"] == "S2":
            executable = resolved_rule_version(rule)
            if not executable:
                task.risk = "warning"
                task.rule_version_pinned = "待发布"
                add_event(session, task, "Workflow", f"规则治理拦截：{rule.name} {rule.latest_version} 为 {rule.publish_status}，无 Published 基线", "等待中", "RULE_GUARD_BLOCKED")
                create_anomaly(session, task, "规则待核验", "高校规则尚未完成核验/发布，自动化流程已被 Governance Guard 阻断", "规则知识库存在 Draft 版本。为避免未核验规则驱动外部操作，Workflow Runtime 在规则匹配节点停止。", "由 HR 核验公开来源与流程要求，完成双人复核并发布规则版本后恢复任务。", level=2, risk="中", state="待处理", status="规则治理拦截，等待 HR 核验发布")
                add_outbox(session, task, "RULE_GUARD_BLOCKED", {"university_id": rule.id, "rule_version": rule.latest_version})
                task.version += 1
                session.flush()
                return task
            if task.rule_version_pinned in (None, "待发布", ""):
                task.rule_version_pinned = executable
                task.rule_source_pinned = rule.source
            if rule.publish_status != "Published":
                add_event(session, task, "Workflow", f"最新 {rule.latest_version} 为 Draft，自动固定上一已发布版本 {executable}", "完成", "RULE_PINNED")
        if step.get("actor") in {"RPA", "AI"}:
            execution = ConnectorExecution(task_id=task.id,connector_type=step["actor"],node_id=step["id"],state="RUNNING",attempts=1,started_at=now_dt())
            session.add(execution)
            session.flush()
            if task.university_id == "nju" and step["actor"] == "RPA":
                execution.state = "FAILED"
                execution.attempts = 3
                execution.last_error = "页面元素「确认签约」未找到；连续重试 3 次失败"
                execution.finished_at = now_dt()
                task.risk = "warning"
                add_event(session, task, "RPA", f"Connector 降级：{step['name']} 执行失败，连续重试 3 次后转人工接管", "失败", "CONNECTOR_FAILED")
                create_anomaly(session, task, "RPA执行失败", "高校就业系统页面变化，RPA 连续重试失败", "确定性自动化执行失败，已触发 Connector 降级策略。", "暂停自动重试，保留失败证据并由 HR/运维人工接管。", level=2, risk="中", state="待处理", status="RPA失败已转人工接管")
                session.add(RuntimeLog(time=now_time(),level="error",source="RPA",message=f"[{rule.name}] {task.candidate_name} · {step['name']} 连续失败 3 次，Connector 降级"))
                add_outbox(session, task, "CONNECTOR_FAILED", {"node": step["id"], "connector": "RPA", "attempts": 3})
                task.version += 1
                session.flush()
                return task
            execution.state = "SUCCEEDED"
            execution.finished_at = now_dt()
        add_event(session, task, source_for_step(step), f"{step['name']} 自动执行完成", "完成", "NODE_COMPLETED")
        add_outbox(session, task, "NODE_COMPLETED", {"node": step["id"], "name": step["name"]})
        task.current_step += 1
        task.node_entered_at = DEMO_BASE_DATE
        task.version += 1
        if task.current_step >= len(flow) - 1:
            task.current_step = len(flow) - 1
            task.risk = "done"
            task.completed_at = DEMO_BASE_DATE
            add_event(session, task, "Workflow", "签约流程完成，协议归档闭环结束", "完成", "TASK_COMPLETED")
            add_outbox(session, task, "TASK_COMPLETED", {"completed_at": task.completed_at})
            break
    session.flush()
    return task


def _same_create_request(task: TripartiteTask, data) -> bool:
    return task.candidate_name == data.candidate_name.strip() and task.university_id == data.university_id and task.position == data.position.strip() and task.offer_date == data.offer_date and task.deadline == data.deadline


def create_task(session: Session, data) -> TripartiteTask:
    if data.idempotency_key:
        existing = session.scalar(select(TripartiteTask).where(TripartiteTask.idempotency_key == data.idempotency_key))
        if existing:
            if not _same_create_request(existing, data):
                raise HTTPException(409, detail="同一 idempotency_key 已用于不同的任务创建请求")
            return existing
    rule = session.get(UniversityRule, data.university_id)
    if not rule:
        raise HTTPException(404, "高校规则不存在")
    count = session.scalar(select(func.count()).select_from(TripartiteTask)) or 0
    task_id = f"T{data.offer_date.replace('-', '')}-{count + 1:03d}"
    while session.get(TripartiteTask, task_id):
        count += 1
        task_id = f"T{data.offer_date.replace('-', '')}-{count + 1:03d}"
    task = TripartiteTask(id=task_id,candidate_name=data.candidate_name.strip(),university_id=rule.id,position=data.position.strip(),offer_date=data.offer_date,deadline=data.deadline,current_step=2,node_entered_at=DEMO_BASE_DATE,risk="normal",rule_version_pinned=resolved_rule_version(rule) or "待发布",rule_source_pinned=rule.source,workflow_version=WORKFLOW_VERSIONS[rule.mode],trace_id=f"TRC-{task_id.replace('-', '')}-{uuid.uuid4().hex[:6].upper()}",version=1,idempotency_key=data.idempotency_key)
    session.add(task)
    session.flush()
    add_event(session, task, "Workflow", f"Offer Accepted → 自动创建三方任务 {task.id}", "完成", "TASK_CREATED")
    add_audit(session, "SYSTEM", "CREATE_TASK", "TripartiteTask", task.id, None, {"candidate": task.candidate_name, "university": rule.name}, task.trace_id)
    add_outbox(session, task, "TASK_CREATED", {"task_id": task.id})
    run_until_wait(session, task)
    session.commit()
    return task


def complete_current_node(session: Session, task_id: str, external_event_id: str, event_type: str, expected_version: int) -> tuple[TripartiteTask, bool]:
    task = session.get(TripartiteTask, task_id)
    if not task:
        raise HTTPException(404, "任务不存在")
    duplicate = session.scalar(select(InboxEvent).where(InboxEvent.external_event_id == external_event_id))
    if duplicate:
        return task, True
    if task.risk == "done":
        raise HTTPException(409, "任务已完成，不接受新的推进事件")
    if task.version != expected_version:
        raise HTTPException(409, detail={"message":"版本冲突","expected_version":expected_version,"actual_version":task.version})
    rule = session.get(UniversityRule, task.university_id)
    flow = FLOWS[rule.mode]
    step = flow[task.current_step]
    if step.get("auto"):
        raise HTTPException(409, "当前节点由系统自动执行，不接受外部完成事件")
    required_event = EVENT_BY_ACTOR.get(step.get("actor"))
    if required_event and event_type != required_event:
        raise HTTPException(422, detail={"message":"事件类型与当前节点不匹配","required":required_event,"current_actor":step.get("actor")})
    session.add(InboxEvent(external_event_id=external_event_id,task_id=task.id,event_type=event_type,received_at=now_dt()))
    before = {"step": task.current_step, "version": task.version}
    source = "External" if step.get("actor") in {"学生", "学校"} else "HR"
    add_event(session, task, source, f"{step['name']} 已完成 → 接收 {event_type}", "完成", event_type, event_id=f"IN-{external_event_id}")
    task.current_step += 1
    task.node_entered_at = DEMO_BASE_DATE
    task.version += 1
    add_outbox(session, task, "EXTERNAL_EVENT_ACCEPTED", {"external_event_id": external_event_id, "event_type": event_type})
    add_audit(session, step.get("actor", "EXTERNAL"), "ADVANCE_TASK", "TripartiteTask", task.id, before, {"step": task.current_step, "version": task.version}, task.trace_id)
    run_until_wait(session, task)
    session.commit()
    return task, False


def publish_rule(session: Session, university_id: str, actor: str, change_note: str) -> UniversityRule:
    rule = session.get(UniversityRule, university_id)
    if not rule:
        raise HTTPException(404, "高校规则不存在")
    old_version = rule.latest_version
    match = re.match(r"v(\d+)\.(\d+)", old_version or "v0.9")
    if match:
        major, minor = int(match.group(1)), int(match.group(2))
        new_version = "v1.0" if major == 0 and minor >= 9 else f"v{major}.{minor + 1}"
    else:
        new_version = "v1.0"
    before = {"version": old_version, "status": rule.publish_status}
    rule.latest_version = new_version
    rule.publish_status = "Published"
    rule.last_published_version = new_version
    rule.verified = "已核验"
    rule.updated = DEMO_BASE_DATE
    rule.effective_from = DEMO_BASE_DATE
    rule.verified_by = "校招运营 + HR数字化双人复核"
    rule.verified_at = now_dt()
    session.add(RuleVersion(university_id=rule.id,version=new_version,status="Published",date=DEMO_BASE_DATE,change_note=change_note))
    add_audit(session, actor, "PUBLISH_RULE", "UniversityRule", rule.id, before, {"version":new_version,"status":"Published"})
    session.flush()
    blocked_tasks = session.scalars(select(TripartiteTask).where(TripartiteTask.university_id == rule.id, TripartiteTask.rule_version_pinned == "待发布")).all()
    for task in blocked_tasks:
        task.rule_version_pinned = new_version
        task.rule_source_pinned = rule.source
        task.risk = "normal"
        task.version += 1
        anomalies = session.scalars(select(Anomaly).where(Anomaly.task_id == task.id, Anomaly.type == "规则待核验", Anomaly.state != "已解决")).all()
        for anomaly in anomalies:
            anomaly.state = "已解决"
            anomaly.status = f"规则 {new_version} 已发布，Workflow 自动恢复"
        add_event(session, task, "Workflow", f"规则 {new_version} 已发布，Governance Guard 解除，流程自动恢复", "完成", "RULE_PUBLISHED")
        run_until_wait(session, task)
    session.commit()
    return rule


def resolve_anomaly(session: Session, anomaly_id: str, actor: str = "HR") -> Anomaly:
    anomaly = session.get(Anomaly, anomaly_id)
    if not anomaly:
        raise HTTPException(404, "异常不存在")
    before = {"state": anomaly.state, "status": anomaly.status}
    anomaly.state = "已解决"
    anomaly.status = f"{actor} 已确认异常关闭"
    session.flush()
    if anomaly.task_id:
        task = session.get(TripartiteTask, anomaly.task_id)
        active_high_level = session.scalar(select(func.count()).select_from(Anomaly).where(Anomaly.task_id == task.id, Anomaly.state != "已解决", Anomaly.level >= 2)) or 0
        if active_high_level == 0 and task.risk in {"critical", "warning"}:
            task.risk = "normal"
        add_event(session, task, "HR", f"异常 {anomaly.id} 已关闭：{anomaly.type}", "完成", "ANOMALY_RESOLVED")
        add_audit(session, actor, "RESOLVE_ANOMALY", "Anomaly", anomaly.id, before, {"state":anomaly.state}, task.trace_id)
    session.commit()
    return anomaly


def accept_anomaly(session: Session, anomaly_id: str, actor: str = "HR") -> Anomaly:
    anomaly = session.get(Anomaly, anomaly_id)
    if not anomaly:
        raise HTTPException(404, "异常不存在")
    anomaly.state = "待验证"
    anomaly.status = f"{actor} 已接受 AI 建议，等待验证结果"
    if anomaly.task_id:
        task = session.get(TripartiteTask, anomaly.task_id)
        add_event(session, task, "HR", f"接受 AI 建议：{anomaly.type}", "完成", "AI_SUGGESTION_ACCEPTED")
    session.commit()
    return anomaly


def manual_takeover(session: Session, anomaly_id: str, actor: str = "HR") -> Anomaly:
    anomaly = session.get(Anomaly, anomaly_id)
    if not anomaly:
        raise HTTPException(404, "异常不存在")
    anomaly.state = "人工处理中"
    anomaly.status = f"{actor} 已接管，处理中"
    if anomaly.task_id:
        task = session.get(TripartiteTask, anomaly.task_id)
        add_event(session, task, "HR", f"人工接管异常：{anomaly.type}", "等待中", "MANUAL_TAKEOVER")
    session.commit()
    return anomaly


def reconcile(session: Session) -> dict:
    total = session.scalar(select(func.count()).select_from(TripartiteTask)) or 0
    nju = session.scalar(select(func.count()).select_from(TripartiteTask).where(TripartiteTask.university_id == "nju", TripartiteTask.risk != "done")) or 0
    active = session.scalar(select(func.count()).select_from(Anomaly).where(Anomaly.state != "已解决")) or 0
    checked = total - nju
    session.add(RuntimeLog(time=now_time(),level="info",source="RPA",message=f"[巡检] 手动触发全量状态巡检：{total} 份任务"))
    session.add(RuntimeLog(time=now_time(),level="done",source="Workflow",message=f"[巡检] 完成：总计 {total} 份，已检查 {checked} 份；活跃异常 {active} 份；南京大学 {nju} 份转人工接管"))
    session.commit()
    return {"total":total,"checked":checked,"active_anomalies":active,"nju_skipped":nju}
