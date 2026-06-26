# API 概览

本文档说明 `open-intent-router` MVP 阶段提供的主要接口边界。接口以 FastAPI 暴露，完整字段定义以代码中的 Pydantic Schema 和运行时 OpenAPI 文档为准。

## 健康检查

- `GET /health`：服务进程健康检查。
- `GET /ready`：服务就绪检查，会校验关键依赖是否可用。

## 路由

### `POST /api/v1/route`

只执行意图识别和路由决策，不调用目标 Agent。

典型返回内容包括：

- 候选 Agent 列表。
- 最终选中的 `target_agent_id`。
- 路由动作，例如 `invoke_agent`、`ui_handoff` 或 `clarify`。
- 置信度、理由、缺失输入、Evidence 命中信息。
- 路由日志 ID，便于后续审计。

### `POST /api/v1/route-and-invoke`

先执行路由，再在目标 Agent 可调用且输入满足要求时执行调用。

适用场景：

- 宿主应用希望后端直接完成“识别意图 + 调用工具”。
- 目标 Agent 是 HTTP API、本地函数或 Mock Agent。
- 调用过程需要统一记录 Agent Run、事件和结果。

如果目标 Agent 只能由前端或宿主系统处理，例如 `ui_handoff`，接口会返回路由交接信息，而不会执行外部调用。

## 显式调用

### `POST /api/v1/invoke`

根据 `agent_id` 显式调用目标 Agent，不再重新做意图识别。

MVP 支持的 Invoker：

- `mock`：返回配置好的 Mock 响应，适合本地开发和测试。
- `http`：调用配置的 HTTP Endpoint。
- `local_function`：调用受信任的本地注册函数。
- `ui_handoff`：返回宿主应用所需的路由交接数据，不执行外部系统调用。

## Agent 查询

公开查询接口：

- `GET /api/v1/agents`
- `GET /api/v1/agents/{agent_id}`
- `POST /api/v1/agents/available`

公开接口会隐藏敏感配置，例如密钥、Header Token、私有调用参数等。宿主应用可通过 `available` 接口按用户角色、用户组、租户和属性过滤可用 Agent。

## Agent 管理

管理接口需要传入 Admin Token：

- Header：`X-Admin-Token: <token>`
- 或：`Authorization: Bearer <token>`

接口列表：

- `GET /api/v1/admin/agents`
- `POST /api/v1/admin/agents`
- `PUT /api/v1/admin/agents/{agent_id}`
- `PATCH /api/v1/admin/agents/{agent_id}/enabled`
- `DELETE /api/v1/admin/agents/{agent_id}`
- `POST /api/v1/admin/registry/reload`

说明：

- `database` 模式支持完整 CRUD。
- `file` 模式主要用于只读加载，不适合运行时变更。
- `hybrid` 模式以数据库为主，数据库不可用时才使用本地文件兜底。

## 事件

事件接口用于接收 Agent 执行过程中的状态变化、进度、日志和结果片段。

- `POST /api/v1/events/agent`
- `POST /api/v1/runs/{run_id}/events`

事件 ID 具备幂等语义。重复提交相同事件 ID 不应产生重复副作用。

## Run 查询

- `GET /api/v1/runs/{run_id}`

Run 用于记录一次 Agent 调用的生命周期，包括调用输入、调用状态、结果摘要、错误信息和事件序列。

## Plan

计划接口用于表达需要用户确认或分步执行的 Agent 操作。

- `GET /api/v1/plans/{plan_id}`
- `POST /api/v1/plans/{plan_id}/actions`

当前支持的 Plan Action：

- `confirm`：确认继续执行。
- `cancel`：取消计划。

## Session

- `GET /api/v1/sessions/{session_id}/messages`

Session 用于保存用户与路由器之间的消息上下文。MVP 只提供轻量会话消息能力，不实现复杂会话状态机。
