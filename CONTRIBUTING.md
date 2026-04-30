# 贡献指南

这个项目是一个用于学习和实践的标准 Agent 工程骨架。贡献代码时优先保持结构清晰、默认测试稳定、安全边界明确，而不是追求一次性堆叠功能。

## 贡献目标

- 让每个模块都能作为标准 Agent 项目的学习样例。
- 保持默认测试不依赖真实 LLM、真实 Embedding 模型或外部网络。
- 新增能力时同步补齐配置、测试、文档和入口命令。
- 尽量修根因，不用 prompt 或临时判断掩盖工程问题。

## 本地开发流程

```bash
# 1. 安装运行依赖
pip install -r requirements.txt

# 2. 安装开发依赖
pip install -r requirements-dev.txt

# 3. 初始化示例数据库
make init-db

# 4. 检查本地环境
make doctor

# 5. 运行质量门禁
make check
```

启动 UI：

```bash
make run-app
```

运行 dry-run 评估：

```bash
make benchmark
```

只有在确实需要真实模型时再运行：

```bash
make test-embedding
make benchmark-live
```

## 分支与提交建议

- 分支名建议使用 `codex/<short-topic>` 或 `feature/<short-topic>`。
- 每次改动聚焦一个主题，例如 `add-tool-tests`、`improve-rag-indexing`。
- 提交前至少运行 `make check`。
- 不要提交 `.env`、本地模型、临时缓存、生成报告和个人数据库。

## 代码规范

### 通用原则

- 业务代码不要直接读取散落的环境变量，优先通过 `src/config.py` 和 `config/settings.yaml`。
- 不要把 LLM provider SDK 调用散落到业务模块，统一放在 `src/llm/` adapter 层。
- 不要在默认测试里调用真实网络、真实 LLM 或下载真实模型。
- 不要硬编码绝对路径、模型名、数据库路径或 API Key。
- 新增用户输入入口时必须考虑路径、SQL、代码执行和 prompt 注入风险。

### 安全边界

- 文件路径校验优先复用 `src/path_utils.py`。
- SQL 表名、项目名、上传文件名必须做白名单或正则校验。
- Python 执行类能力必须保留超时、隔离、输出截断和 import/builtin 限制。
- 工具层必须自己做输入校验，不能只依赖 system prompt。
- 默认能力应当安全失败，并返回可解释的错误信息。

### 可观测性

- 新增 LLM 调用时应保留耗时、stop reason、token usage 等信息。
- 新增工具调用路径时应能进入 Agent trace。
- 错误不要只打印到控制台，应该能进入返回结果或 trace，便于 UI 和测试验证。

## 新增模块清单

### 新增 Tool

1. 在 `src/tools/` 新增工具文件，继承统一 Tool 基类。
2. 定义清晰的 `name`、`description`、`parameters`。
3. 在 `execute` 内完成输入校验、错误处理和安全边界控制。
4. 注册到 `ToolRegistry` 或 Agent 初始化路径。
5. 添加单元测试，默认不依赖外部服务。
6. 如影响用户能力，更新 `README.md`、`docs/agent_architecture.md` 或 `docs/development.md`。

### 新增 Skill

1. 在 `src/skills/` 新增 Skill。
2. 明确适用场景、关键词、语义描述和推荐工具集。
3. 确保 keyword / embedding / hybrid 路由可测试。
4. 新增或更新 Agent 测试，优先使用 fake embedder / fake LLM。
5. 在学习文档中说明该 Skill 代表的 Agent 设计模式。

### 新增 RAG 能力

1. 明确影响的是 loader、chunker、embedder、retriever、reranker 还是 vector store。
2. 索引变更必须考虑 manifest 或可恢复机制。
3. 默认测试使用假 Embedding 或哈希回退。
4. 真实模型验证放到 `@pytest.mark.embedding` 或显式命令中。
5. 更新 benchmark case 或检索质量验证说明。

### 新增 LLM Provider

1. 在 `src/llm/` 新增 adapter。
2. 统一输出 `LLMResponse` 和 `ToolCall`。
3. 适配 tool schema、tool result message、streaming 和 usage。
4. 通过 fake response 或 mock 测试 adapter 行为。
5. 更新 `.env.example` 和配置说明。

### 新增 MCP Server

1. Server 放在 `mcp_servers/`，Client 能通过 `src/mcp/` 访问。
2. 明确工具发现、参数 schema、错误返回格式。
3. 对外部资源做最小权限限制。
4. 添加协议层或 smoke test。
5. 文档说明该 MCP Server 暴露了什么能力。

## 测试要求

默认质量门禁：

```bash
make check
```

它包含：

- `ruff check .`
- `compileall`
- 默认 pytest 测试集

测试分层建议：

| 层级 | 目的 | 是否默认运行 |
|---|---|---|
| Unit | 工具、配置、纯函数、路径安全 | 是 |
| Agent Loop | fake LLM + fake tool 验证 ReAct 链路 | 是 |
| RAG | fake/hash embedding 验证检索流程 | 是 |
| Embedding | 真实 sentence-transformers / API | 否，显式运行 |
| Live Benchmark | 真实 Agent/LLM 端到端评估 | 否，显式运行 |

## 文档要求

新增能力后按影响范围更新：

- `README.md`：用户如何运行、主要能力和常用命令。
- `docs/agent_architecture.md`：该能力在标准 Agent 架构中的位置。
- `docs/development.md`：开发者如何扩展、测试和排查。
- `PROGRESS.md`：阶段性进展记录。
- `.env.example`：新增环境变量或 provider 时必须更新。

## Pull Request 检查清单

提交前确认：

- [ ] `make check` 通过。
- [ ] 默认测试不依赖真实 LLM、真实 Embedding 或外部网络。
- [ ] 新增配置有默认值或 `.env.example` 示例。
- [ ] 新增用户输入入口做了安全校验。
- [ ] 新增工具或 Agent 行为有测试覆盖。
- [ ] 相关文档已更新。
- [ ] 没有提交 `.env`、缓存、模型文件、生成报告或个人数据。

## 问题排查

- 环境异常先跑 `make doctor`。
- 默认测试失败先跑 `make test` 获取更短输出。
- LLM 或 provider 问题先检查 `.env` 和 `config/settings.yaml`。
- RAG 结果异常先检查知识库文档、manifest、vector store 和 BM25 索引恢复。
- Agent 行为异常优先看 trace：LLM 调用了什么工具、工具输入输出是什么、在哪一步失败。
