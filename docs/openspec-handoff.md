# OpenSpec Handoff

Implemented change:

- `openspec/changes/bootstrap-open-intent-router`

Primary reference document:

- `docs/开源意图识别项目需求分析文档.md`

Current implementation follows the proposal, design, and specs generated for `bootstrap-open-intent-router`.

Important MVP exclusions remain intentional:

- No Feishu sync.
- No built-in Coze/Dify/FastGPT adapter.
- No Milvus indexing in core.
- No frontend UI.
- No distributed worker system.
- No complex `session_state` dependency.
