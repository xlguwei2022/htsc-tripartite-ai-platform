# 华泰证券三方协议智能运营中台 — Public Runtime PoC v1.5

## 项目定位

v1.5 在 v1.4.1 可运行 Runtime PoC 的基础上增加公网部署能力。核心业务实现保持不变：FastAPI REST API、服务端 Workflow Engine、Rule Version Pinning、Governance Guard、Inbox/Outbox、Audit、Trace ID、ConnectorExecution、异常人工接管与自动化测试。

公网部署时使用 PostgreSQL；本地运行时如果没有配置 `DATABASE_URL`，系统自动回退 SQLite。Frontend 与 Backend 由同一个 FastAPI Web Service 提供，因此老师访问公网 URL 时不需要安装 Python、打开 Terminal 或单独配置前端。

> 所有页面数据均为 PoC 模拟/脱敏数据。公网版本禁止写入真实候选人个人信息、真实协议文件或真实系统凭证。

## 目录

```text
Tripartite_Public_v1.5/
├── START_HERE_公网版先看我.md
├── DEPLOY_PUBLIC_公网部署说明.md
├── README.md
├── render.yaml                    # Render 免费答辩 Blueprint
├── deploy/render-stable.yaml      # 长期稳定版 Blueprint
├── .python-version
├── requirements.txt               # 本地 SQLite Runtime
├── requirements-public.txt        # 公网 PostgreSQL Runtime
├── Dockerfile
├── docker-compose.public.yml
├── run.py
├── app/
├── frontend/
├── data/                           # 本地 SQLite fallback
├── tests/
├── docs/
└── offline_backup/
```

## 公网部署

最推荐 Render Blueprint：

1. 将本目录完整上传 GitHub。
2. Render 新建 Blueprint，选择该仓库。
3. Render 读取 `render.yaml`，自动创建 Web Service + PostgreSQL。
4. 部署完成后直接把 `https://<service>.onrender.com` 发给老师。
5. Swagger 位于 `https://<service>.onrender.com/docs`。

详细步骤见 `DEPLOY_PUBLIC_公网部署说明.md`。

## 本地运行

macOS 可继续双击 `start_demo.command`。本地未配置 `DATABASE_URL` 时默认使用 `data/tripartite_poc.db`。

```text
http://127.0.0.1:8013
http://127.0.0.1:8013/docs
```

## Runtime 数据库策略

```text
DATABASE_URL 已配置
    ↓
PostgreSQL（公网）

DATABASE_URL 未配置
    ↓
SQLite（本地）
```

`/api/health` 会返回实际数据库类型；前端顶部 Runtime Badge 也会显示 `PostgreSQL` 或 `SQLite`。

## 核心 API

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

## 测试

```bash
python -m pytest -q
```

Public v1.5 本地兼容性回归：`11 passed`。

## 答辩建议

最终准备三条链路：

1. 公网 URL：老师直接体验。
2. 公网 `/docs`：技术追问时展示真实 API。
3. `start_demo.command` + Offline HTML：公网/网络异常时本地兜底。

项目定位仍然是企业级技术 PoC，而不是已接入华泰或高校真实生产环境的正式系统。
