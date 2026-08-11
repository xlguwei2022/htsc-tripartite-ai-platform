# 华泰证券三方协议智能运营中台 — Public Runtime PoC v1.5

一套面向校招三方协议管理的企业级技术 PoC：**Frontend + FastAPI Backend + Workflow Runtime + PostgreSQL/SQLite + Rule Governance + AI/RPA Mock Connector + Inbox/Outbox + Audit**。

> 当前仓库仅使用 PoC 模拟/脱敏数据，不代表已连接华泰生产系统或高校真实生产平台。请勿录入真实候选人个人信息、真实协议文件、账号密码或生产凭证。

## 一键部署到 Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/xlguwei2022/htsc-tripartite-ai-platform)

Render 会读取仓库根目录的 `render.yaml`，创建：

- FastAPI Web Service
- PostgreSQL Database
- `/api/health` 健康检查
- HTTPS 公网地址

部署完成后，老师只需要打开 Render 分配的公网 URL，不需要 Python、Terminal 或下载 ZIP。

详细步骤：[`DEPLOY_PUBLIC_公网部署说明.md`](./DEPLOY_PUBLIC_%E5%85%AC%E7%BD%91%E9%83%A8%E7%BD%B2%E8%AF%B4%E6%98%8E.md)

## 系统能力

- Offer Accepted 后创建 `TripartiteTask`
- 一校一策 `UniversityRule` / Rule Version Pinning
- Draft / Published 规则治理与 Governance Guard
- Workflow 自动节点推进 + 学生/学校/HR 外部事件推进
- API/RPA/AI Connector 执行抽象
- RPA 三次失败 → 降级 → 异常入队 → 人工接管
- AI 异常建议 + Level 0–3 Human-in-the-loop
- Inbox 幂等、Idempotency Key、Optimistic Lock / HTTP 409
- Domain Event、Transactional Outbox 设计、Audit、Trace ID
- PostgreSQL 公网持久化；本地自动回退 SQLite
- FastAPI Swagger `/docs`

## 目录

```text
.
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── db.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── seed.py
│   ├── serializers.py
│   ├── service.py
│   └── workflow.py
├── frontend/
│   └── index.html
├── tests/
│   └── test_runtime.py
├── render.yaml
├── Dockerfile
├── requirements.txt
├── requirements-public.txt
├── requirements-dev.txt
├── .python-version
├── env.example
├── run.py
└── DEPLOY_PUBLIC_公网部署说明.md
```

## 公网架构

```text
老师浏览器
    ↓ HTTPS
Render Web Service
    ├── Frontend
    └── FastAPI REST API
            ↓
      Workflow Runtime
            ↓
      Render PostgreSQL
            ↓
Event / Inbox / Outbox / Audit / ConnectorExecution
```

## 本地运行

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python run.py
```

访问：

```text
http://127.0.0.1:8013
http://127.0.0.1:8013/docs
```

未设置 `DATABASE_URL` 时使用 SQLite；Render Blueprint 自动注入 PostgreSQL `DATABASE_URL`。

## API

- `GET /api/health`
- `GET /api/bootstrap`
- `POST /api/tasks`
- `POST /api/tasks/{id}/events`
- `POST /api/rules/{id}/publish`
- `POST /api/anomalies/{id}/resolve`
- `POST /api/anomalies/{id}/accept`
- `POST /api/anomalies/{id}/takeover`
- `POST /api/reconcile`
- `POST /api/reset`
- `GET /api/outbox`
- `GET /api/audit`

## 自动化测试

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

当前 Runtime 回归基线：**11 tests**，覆盖任务创建与持久化、自动流程、完整签约闭环、创建幂等、Inbox 去重、事件类型 Guard、409 乐观锁冲突、规则治理阻断/恢复、RPA Failure、异常状态同步、Outbox 与 Audit。

## PoC 与 Production 边界

当前真实实现的是业务 Runtime 与一致性机制；高校真实 API、影刀真实 RPA、企业 AI Gateway、OCR、电子签和 SSO/OIDC 仍为目标 Connector。正式生产化还需要安全评审、RBAC、Secrets Manager、数据库迁移、真实 Connector、可观测平台和运维体系。
