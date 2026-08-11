from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def reset():
    response = client.post("/api/reset")
    assert response.status_code == 200


def create_fudan(name="测试候选人", key=None):
    payload = {
        "candidate_name": name,
        "university_id": "fudan",
        "position": "FinTech-后端工程师",
        "offer_date": "2026-08-10",
        "deadline": "2026-08-25",
    }
    if key:
        payload["idempotency_key"] = key
    response = client.post("/api/tasks", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def test_health_and_bootstrap():
    reset()
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["persistence"] is True
    assert health.json()["version"].startswith("1.5")
    data = client.get("/api/bootstrap").json()
    assert len(data["rules"]) == 12
    assert len(data["tasks"]) == 12
    assert len(data["anomalies"]) == 5


def test_fudan_auto_runs_until_student_wait_and_persists():
    reset()
    task = create_fudan("后端测试候选人", "test-create-1")
    assert task["ruleVersionPinned"] == "v2.0"
    assert task["currentStep"] == 4
    assert task["risk"] == "normal"
    assert task["version"] >= 3
    persisted = next(item for item in client.get("/api/bootstrap").json()["tasks"] if item["id"] == task["id"])
    assert persisted["currentStep"] == 4
    assert any("企业发起网签 自动执行完成" in e["msg"] for e in persisted["events"])


def test_create_task_idempotency_returns_same_task():
    reset()
    first = create_fudan("创建幂等", "CREATE-KEY-001")
    second = create_fudan("创建幂等", "CREATE-KEY-001")
    assert first["id"] == second["id"]
    assert len(client.get("/api/bootstrap").json()["tasks"]) == 13


def test_create_task_idempotency_conflict_on_different_payload():
    reset()
    create_fudan("创建幂等", "CREATE-KEY-002")
    response = client.post("/api/tasks", json={"candidate_name":"另一个人","university_id":"fudan","position":"FinTech-后端工程师","offer_date":"2026-08-10","deadline":"2026-08-25","idempotency_key":"CREATE-KEY-002"})
    assert response.status_code == 409


def test_inbox_idempotency_and_optimistic_lock():
    reset()
    task = create_fudan("事件幂等测试")
    body = {"external_event_id":"EV-EXT-001","event_type":"STUDENT_COMPLETED","expected_version":task["version"]}
    first = client.post(f"/api/tasks/{task['id']}/events", json=body)
    assert first.status_code == 200
    version_after_first = first.json()["task"]["version"]
    duplicate = client.post(f"/api/tasks/{task['id']}/events", json=body)
    assert duplicate.status_code == 200
    assert duplicate.json()["duplicate"] is True
    assert duplicate.json()["task"]["version"] == version_after_first
    conflict = client.post(f"/api/tasks/{task['id']}/events", json={"external_event_id":"EV-EXT-002","event_type":"SCHOOL_COMPLETED","expected_version":1})
    assert conflict.status_code == 409


def test_event_type_guard_rejects_wrong_actor_event():
    reset()
    task = create_fudan("事件类型校验")
    response = client.post(f"/api/tasks/{task['id']}/events", json={"external_event_id":"EV-WRONG-TYPE","event_type":"SCHOOL_COMPLETED","expected_version":task["version"]})
    assert response.status_code == 422


def test_full_fudan_flow_completes_after_student_and_school_events():
    reset()
    task = create_fudan("闭环测试")
    response = client.post(f"/api/tasks/{task['id']}/events", json={"external_event_id":"EV-CLOSE-1","event_type":"STUDENT_COMPLETED","expected_version":task["version"]})
    task = response.json()["task"]
    assert task["currentStep"] == 5
    response = client.post(f"/api/tasks/{task['id']}/events", json={"external_event_id":"EV-CLOSE-2","event_type":"SCHOOL_COMPLETED","expected_version":task["version"]})
    task = response.json()["task"]
    assert task["risk"] == "done"
    assert task["currentStep"] == 8
    assert task["completedAt"] == "2026-08-10"


def test_tsinghua_governance_guard_then_publish_resumes():
    reset()
    response = client.post("/api/tasks", json={"candidate_name":"规则测试","university_id":"tsinghua","position":"开发工程师","offer_date":"2026-08-10","deadline":"2026-08-25"})
    task = response.json()
    assert task["currentStep"] == 2
    assert task["risk"] == "warning"
    assert task["ruleVersionPinned"] == "待发布"
    data = client.get("/api/bootstrap").json()
    assert any(a["cand"] == "规则测试" and a["type"] == "规则待核验" and a["state"] != "已解决" for a in data["anomalies"])
    published = client.post("/api/rules/tsinghua/publish", json={"actor":"测试规则管理员","change_note":"测试发布"})
    assert published.status_code == 200
    data = client.get("/api/bootstrap").json()
    task_after = next(x for x in data["tasks"] if x["id"] == task["id"])
    assert task_after["ruleVersionPinned"] == "v1.0"
    assert task_after["currentStep"] == 4
    assert task_after["risk"] == "normal"


def test_nanjing_connector_failure_creates_execution_and_anomaly():
    reset()
    response = client.post("/api/tasks", json={"candidate_name":"RPA测试","university_id":"nju","position":"开发工程师","offer_date":"2026-08-10","deadline":"2026-08-25"})
    task = response.json()
    assert task["currentStep"] == 3
    assert task["risk"] == "warning"
    data = client.get("/api/bootstrap").json()
    assert any(a["cand"] == "RPA测试" and a["type"] == "RPA执行失败" for a in data["anomalies"])
    executions = [x for x in data["connector_executions"] if x["task_id"] == task["id"]]
    assert executions
    assert executions[0]["state"] == "FAILED"
    assert executions[0]["attempts"] == 3


def test_resolve_anomaly_synchronizes_task_risk():
    reset()
    response = client.post("/api/anomalies/AN004/resolve", json={"actor":"测试HR"})
    assert response.status_code == 200
    data = client.get("/api/bootstrap").json()
    task = next(x for x in data["tasks"] if x["id"] == "T20260809-006")
    assert task["risk"] == "normal"


def test_outbox_and_audit_are_written():
    reset()
    task = create_fudan("审计测试")
    outbox = client.get("/api/outbox").json()
    audit = client.get("/api/audit").json()
    assert any(x["aggregate_id"] == task["id"] and x["event_type"] == "TASK_CREATED" for x in outbox)
    assert any(x["entity_id"] == task["id"] and x["action"] == "CREATE_TASK" for x in audit)
