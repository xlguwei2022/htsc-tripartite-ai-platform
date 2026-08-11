# 公网部署说明（Render Blueprint）

本仓库已经包含 `render.yaml`，可一次性创建：

- FastAPI Web Service
- Render PostgreSQL
- `/api/health` 健康检查
- 同域 Frontend + Backend
- 自动部署 `main` 分支

## 一键部署

点击：

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/xlguwei2022/htsc-tripartite-ai-platform)

登录 Render 后检查 Blueprint 资源，确认创建 Web Service 与 PostgreSQL，然后点击 Deploy / Apply。

## 部署成功后

Render 会给 Web Service 分配一个 `onrender.com` 地址，例如：

```text
https://htsc-tripartite-ai-platform.onrender.com
```

实际地址以 Render Dashboard 显示为准。

主系统：

```text
https://<你的服务域名>/
```

API 文档：

```text
https://<你的服务域名>/docs
```

健康检查：

```text
https://<你的服务域名>/api/health
```

健康检查成功时应看到：

```json
{
  "status": "ok",
  "database": "PostgreSQL",
  "persistence": true
}
```

## Render Blueprint 说明

`render.yaml` 已固定：

- Region: Singapore
- Python runtime
- Build: `pip install -r requirements-public.txt`
- Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Database: PostgreSQL 17
- `DATABASE_URL`：由 Render Database 自动注入
- `APP_ENV=render-public-demo`

公网运行时 `DATABASE_URL` 存在，因此应用使用 PostgreSQL；本地没有该变量时自动回退 SQLite。

## 第一次部署验证清单

1. Web Service 状态为 Live。
2. Database 状态为 Available。
3. 打开 `/api/health`，确认 `database = PostgreSQL`。
4. 打开 `/`，页面顶部显示 `Public Runtime · PostgreSQL 持久化`。
5. 打开 `/docs`，确认 FastAPI Swagger 可用。
6. 在网站创建一条测试任务，刷新页面后仍存在。
7. 在“自动化控制中心”检查 Outbox / Audit。
8. 演示结束可点击“重置 PoC 基线数据”。

## 公网 Demo 使用边界

此版本仅用于课题答辩和技术 PoC：

- 页面数据均为模拟/脱敏数据。
- RPA、AI、电子签、高校系统均为 Mock Connector 或目标接入能力。
- 禁止录入真实候选人个人信息、真实三方协议文件、真实账号密码、API Key 或生产凭证。
- 正式生产化需要接入企业 SSO/OIDC、RBAC、Secrets Manager、真实 Connector、日志审计、安全评审与数据库迁移工具。

## 免费资源注意事项

本仓库的默认 Blueprint 使用 Render Free Web Service + Free PostgreSQL，适合答辩 PoC，不适合长期生产运行。若需要长期稳定保留数据库，请在 Render Dashboard 将数据库升级为付费实例，或改用仓库中的长期稳定部署配置。

## 常见问题

### 1. 网站第一次打开较慢

免费 Web Service 可能需要从休眠状态启动，等待一会后刷新即可。

### 2. Blueprint 提示无法创建 Free PostgreSQL

一个 Render Workspace 同时只能有一个 Free PostgreSQL。可删除已有的 Free Database，或者将 `render.yaml` 的数据库计划改为付费实例。

### 3. Build 失败

优先检查：

```text
requirements-public.txt
.python-version
Build Command
```

### 4. 网站打开但显示 Runtime 连接失败

访问 `/api/health` 和 `/api/bootstrap`，并查看 Render Web Service 的 Logs。

### 5. 数据库为空

应用启动时如果检测到 `UniversityRule` 为空，会自动执行 PoC Seed，因此首次部署不需要手动导入 SQLite 文件。
