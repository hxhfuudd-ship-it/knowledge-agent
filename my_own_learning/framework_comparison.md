# Agent 框架对比

这份文档帮助你理解：这个项目和 LangChain、LangGraph、LlamaIndex、CrewAI、AutoGen 等框架的区别。

## 结论先说

这个项目属于：

> 自研轻量级 Agent 框架 / From-scratch Agent / Vanilla Python ReAct Agent

它不是：

- LangChain 项目
- LlamaIndex 项目
- CrewAI 项目
- AutoGen 项目

但它实现了这些框架中常见的核心概念：

- Agent loop
- Tool calling
- RAG
- Memory
- Multi-agent
- Harness / standard runner
- Evaluation
- Observability

## 为什么不直接用框架

学习阶段不直接用框架的好处：

- 能看清 Agent 主循环。
- 能理解 tool call 消息格式。
- 能理解工具结果如何回填。
- 能理解 RAG 每个步骤。
- 能理解测试为什么要 mock LLM / Embedding。
- 面试时更容易讲底层原理。

坏处：

- 很多基础能力要自己写。
- 生产级状态管理、持久化、追踪和部署能力不如成熟框架。
- 需要自己维护 adapter 和兼容逻辑。

## 框架对比表

| 框架 | 核心定位 | 适合场景 | 和本项目的关系 |
|---|---|---|---|
| LangChain | 通用 LLM 应用开发框架 | 快速串 LLM、Tool、Retriever、Memory | 本项目手写了它的一部分核心概念 |
| LangGraph | 状态机式 Agent 编排 | 复杂流程、多分支、可恢复 Agent | 可替换本项目的 ReAct 主循环 |
| LlamaIndex | 数据连接与 RAG 框架 | 文档问答、企业知识库、索引管理 | 可替换或增强本项目的 RAG 层 |
| CrewAI | 角色化多 Agent 协作 | 多角色任务分工，例如研究员/分析师/写作者 | 类似本项目 multi_agent 的高层封装 |
| AutoGen | 多 Agent 对话协作 | Agent 互相对话、自动任务分解 | 可用于增强多 Agent 协作实验 |
| Semantic Kernel | 插件化 AI 编排 | 微软生态、企业插件、Planner | 类似 Tool/Skill 插件化思想 |
| Haystack | 搜索与问答 Pipeline | RAG、搜索系统、问答系统 | 可替代部分 RAG pipeline |
| DSPy | Prompt / Pipeline 优化 | 自动优化 prompt、few-shot、模块组合 | 可用于后续优化 prompt 和评估 |
| PydanticAI | 类型安全轻量 Agent | Python 类型约束、结构化输出 | 可借鉴结构化 schema 设计 |

## 本项目对应成熟框架的哪些模块

| 本项目模块 | 成熟框架中类似概念 |
|---|---|
| `src/agent/core.py` | LangChain Agent、LangGraph StateGraph |
| `src/tools/base.py` | LangChain Tool、OpenAI function tool |
| `src/llm/` | LangChain ChatModel、provider adapter |
| `src/rag/` | LlamaIndex / LangChain Retriever |
| `src/skills/` | CrewAI role、Semantic Kernel skill/plugin |
| `src/memory/` | LangChain memory、LangGraph checkpoint |
| `src/mcp/`、`mcp_servers/` | MCP tool server/client |
| `src/harness/` | OpenAI Agents SDK Runner/Evals 思路、LangSmith trajectory eval 的运行外壳 |
| `src/eval/` | LangSmith eval、custom benchmark |
| `src/observability.py` | LangSmith tracing、OpenTelemetry 思路 |

## 如果用 LangGraph 改造

可能变化：

- `src/agent/core.py` 的 while 循环会变成 graph nodes。
- 状态会变成显式 `AgentState`。
- LLM 节点、Tool 节点、Memory 节点分开。
- 可以更容易做分支、重试、人工确认、恢复。

适合引入 LangGraph 的情况：

- Agent 流程越来越复杂。
- 有多分支决策。
- 需要人工审批节点。
- 需要持久化状态和恢复。

## 如果用 LlamaIndex 改造

可能变化：

- `src/rag/loader.py`
- `src/rag/chunker.py`
- `src/rag/vector_store.py`
- `src/rag/retriever.py`

这些可以部分交给 LlamaIndex。

适合引入 LlamaIndex 的情况：

- 文档类型很多。
- 知识库很大。
- 需要更强索引策略。
- 需要 citation、node parser、metadata filter。

## 如果用 LangChain 改造

可能变化：

- Tool 可以用 LangChain `BaseTool` 或 `@tool`。
- LLM 可以用 LangChain ChatModel。
- Retriever 可以接 LangChain retriever。
- Agent executor 可以替换当前循环。

但要注意：

- 抽象更重。
- Debug 需要理解框架内部。
- 版本变化可能带来迁移成本。

## 面试回答模板

面试官问：

> 你为什么不用 LangChain？

可以回答：

> 这个项目的目标是学习 Agent 底层机制，所以我选择从零实现核心模块，包括 ReAct loop、ToolRegistry、LLM Adapter、RAG、Memory 和 Trace。这样我能理解 LangChain 这类框架到底帮我封装了什么。如果生产化，我会考虑用 LangGraph 做复杂状态编排，用 LlamaIndex 增强 RAG，但工具安全、评估和可观测性这些工程原则仍然保留。

面试官问：

> 你的项目能算框架吗？

可以回答：

> 它是一个轻量教学型 Agent 框架骨架，不是通用生产框架。它具备框架的核心抽象，比如 Agent Core、Tool、Skill、Memory、RAG、LLM Adapter，但目标是帮助学习和演示标准 Agent 架构。

## 总结

成熟框架适合快速生产和生态集成；这个项目适合学习底层机制和面试讲解。

最理想的学习路线是：

1. 先用这个项目理解 Agent 原理。
2. 再学 LangGraph、LlamaIndex 等框架。
3. 最后知道什么时候自研，什么时候使用框架。
