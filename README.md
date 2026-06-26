# open-intent-router

`open-intent-router` 是一个轻量级、可插拔的意图识别与 Agent 编排后端，面向多 Agent 应用、企业内部工具、AI 工作流入口和需要统一路由层的智能应用。

它帮助宿主应用接收自然语言请求，识别用户意图，筛选可用 Agent / Tool / Workflow，返回结构化路由决策，并在需要时执行基础的后端调用。同时，项目提供会话上下文、事件、计划、执行结果和路由日志等后端能力。

## 适合解决的问题

- 将用户自然语言意图路由到多个已注册 Agent 中的一个。
- 根据角色、用户组、租户和用户属性过滤可用 Agent。
- 为宿主应用返回稳定、可审计的路由决策结构。
- 提供基础 `route-and-invoke` 能力，支持路由后直接调用目标 Agent。
- 使用数据库注册表作为主数据源，并支持 YAML / JSON 本地文件兜底。
- 通过可选 Evidence Provider 支持固定问法命中、意图提示和候选 Agent 收窄。

## 不适合解决的问题

- 不提供前端控制台或可视化搭建器。
- 不内置飞书、多维表格、OAC、银行私行业务等专有系统耦合。
- 不在 MVP 中内置 Coze、Dify、FastGPT、LangGraph 等平台适配器。
- 不替代 LangChain / LangGraph 的工作流编排能力，而是作为上游意图路由与调用入口。
- 不提供完整知识库管理、向量索引构建或分布式任务调度系统。

## MVP 范围

当前已经实现的核心能力：

- FastAPI 后端服务。
- 通用 Agent Definition Schema。
- Agent Registry 的文件、数据库、混合模式设计。
- SQLite 本地默认数据库，以及兼容 PostgreSQL 的 SQLAlchemy 模型。
- OpenAI-compatible LLM Client 和 Mock LLM。
- 基础 Invoker：`mock`、`http`、`local_function`、`ui_handoff`。
- 会话消息、Agent 事件、Agent Run / Result、Plan 和 Route Log。
- Admin Token 保护的注册表变更接口。
- 可选 Evidence Provider 插件，以及文件型固定问题命中插件。

暂未纳入 MVP 的能力：

- 前端 UI。
- 飞书同步注册表。
- Coze / Dify / FastGPT / LangGraph 内置适配器。
- Milvus 索引和完整知识文件管理。
- 分布式 Worker。
- 复杂会话状态机。

## 快速开始

```bash
cd /Users/lijingtong/project/open_intent_router
python -m venv .venv
. .venv/bin/activate
pip install -e ".[test]"
cp .env.example .env
uvicorn app.main:app --reload
```

本地默认配置：

- `REGISTRY_BACKEND=file`
- `REGISTRY_FILE_PATH=./config/agents.example.yaml`
- `ROUTER_LLM_PROVIDER=mock`
- `DATABASE_URL=sqlite+aiosqlite:///./data/open-intent-router.db`

启动后可访问：

- 健康检查：`GET /health`
- 就绪检查：`GET /ready`
- API 文档：`GET /docs`

## 核心 API

路由与调用：

- `POST /api/v1/route`
- `POST /api/v1/route-and-invoke`
- `POST /api/v1/invoke`

Agent 查询：

- `GET /api/v1/agents`
- `GET /api/v1/agents/{agent_id}`
- `POST /api/v1/agents/available`

事件、执行记录与计划：

- `POST /api/v1/events/agent`
- `POST /api/v1/runs/{run_id}/events`
- `GET /api/v1/runs/{run_id}`
- `GET /api/v1/plans/{plan_id}`
- `POST /api/v1/plans/{plan_id}/actions`
- `GET /api/v1/sessions/{session_id}/messages`

管理接口需要传入 `X-Admin-Token` 或 `Authorization: Bearer <token>`：

- `GET /api/v1/admin/agents`
- `POST /api/v1/admin/agents`
- `PUT /api/v1/admin/agents/{agent_id}`
- `PATCH /api/v1/admin/agents/{agent_id}/enabled`
- `DELETE /api/v1/admin/agents/{agent_id}`
- `POST /api/v1/admin/registry/reload`

## 路由请求示例

```json
{
  "session_id": "sess_001",
  "user": {
    "id": "user_001",
    "roles": ["operator"],
    "groups": ["default"],
    "attributes": {"tenant_id": "tenant_a"}
  },
  "input": {
    "type": "text",
    "text": "summarize this text"
  }
}
```

在默认 Mock 配置下，路由器会基于本地 `config/agents.example.yaml` 中的 Agent 定义返回路由决策。使用 `route-and-invoke` 时，如果目标 Agent 支持后端调用，会继续返回调用结果。

## 文档

- 需求分析：[docs/开源意图识别项目需求分析文档.md](/Users/lijingtong/project/open_intent_router/docs/开源意图识别项目需求分析文档.md)
- Agent 定义：[docs/agent-definition.md](/Users/lijingtong/project/open_intent_router/docs/agent-definition.md)
- API 概览：[docs/api.md](/Users/lijingtong/project/open_intent_router/docs/api.md)
- Evidence Provider：[docs/evidence-provider.md](/Users/lijingtong/project/open_intent_router/docs/evidence-provider.md)
- OAC 迁移说明：[docs/oac-migration.md](/Users/lijingtong/project/open_intent_router/docs/oac-migration.md)

## 设计原则

- 核心模型保持通用，不绑定具体业务系统或第三方 Agent 平台。
- 平台相关字段放入 `invocation.config`、`provider_config` 或 `metadata`，避免污染核心 Schema。
- 数据库注册表用于生产环境，本地文件注册表用于开发、测试和故障兜底。
- 路由决策、Agent 调用和事件记录分层实现，方便后续替换 LLM、Invoker 或 Registry Source。
