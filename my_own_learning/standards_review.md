# 标准做法对照 Review

这份文档记录本项目在 Agent Core、Skills、Harness、RAG、Eval、Trace 等部分参考了哪些主流标准做法，以及当前做到什么程度、后续还可以怎么补。

## 参考的一手资料

- OpenAI Agents SDK Tracing：<https://openai.github.io/openai-agents-python/tracing/>
- Agent Skills Specification：<https://agentskills.io/specification>
- Anthropic Agent Skills Docs：<https://docs.claude.com/en/docs/agents-and-tools/agent-skills>
- LangSmith / AgentEvals Trajectory Evaluation：<https://docs.langchain.com/langsmith/trajectory-evals>
- Google ADK Evaluation：<https://google.github.io/adk-docs/evaluate/>
- LangGraph Durable Execution：<https://docs.langchain.com/oss/python/langgraph/durable-execution>
- LlamaIndex Evaluation：<https://docs.llamaindex.ai/en/stable/module_guides/evaluating/>
- LlamaIndex Retrieval Evaluation：<https://docs.llamaindex.ai/en/stable/examples/evaluation/retrieval/retriever_eval/>

## 1. Agent Core

标准做法：

- Agent 不是只调用一次 LLM，而是一个可观察的 run / loop。
- 标准 loop 通常包含：用户输入、上下文构建、LLM 推理、工具选择、工具执行、结果回填、最终回答。
- 需要限制最大轮数，避免工具调用无限循环。

本项目现状：

- `src/agent/core.py` 已实现 ReAct 风格循环。
- 支持 tool call、observation 回填、skill route、memory 注入、trace 记录。
- 支持 `max_iterations` 防止无限循环。

判断：

- 作为学习项目是规范的。
- 后续生产化可以进一步引入显式状态机，例如 LangGraph 风格的 node / edge / state。

## 2. Tool Calling

标准做法：

- 每个工具要有稳定名称、清晰描述、参数 schema 和统一执行接口。
- 工具层必须自己做安全校验，不能只依赖 prompt。
- 工具调用结果要能进入 trace / trajectory。

本项目现状：

- `src/tools/base.py` 定义统一 Tool 接口和 ToolRegistry。
- SQL、文件、Python、CSV 等工具都有基本安全边界。
- Agent trace 会记录工具名、输入摘要、输出摘要、耗时和成功状态。

判断：

- 结构清晰，适合学习 Tool Calling。
- 后续建议增加工具权限分级，例如 safe / medium / high-risk，并对高风险工具增加用户确认。

## 3. Agent Skills

标准做法：

- Agent Skills 标准强调：一个 skill 是一个目录，至少包含 `SKILL.md`。
- `SKILL.md` 使用 YAML frontmatter，必须有 `name` 和 `description`。
- description 很关键，要说明“做什么”和“什么时候用”。
- 使用 progressive disclosure：启动时只加载元数据，触发后再加载完整说明和资源。

本项目现状：

- 当前 `src/skills/` 是代码内 SkillRegistry，不是文件系统 `SKILL.md` 标准。
- 新增 `skills/` 文件系统说明层，每个 Skill 一个目录，每个目录包含 `SKILL.md`。
- 每个 `SKILL.md` 包含 `name`、`description`、`version`、`tools`、`runtime_mapping` 等 frontmatter。
- 已有 keyword / embedding / hybrid 路由。
- Skill 能表达任务策略和推荐工具。

判断：

- 作为自研 Agent 学习项目是合理的。
- 当前已经具备标准 Skills 文件系统雏形。
- 后续可以让 `SkillRegistry` 自动读取 `SKILL.md` 元数据，实现代码路由和文件说明统一来源。

## 4. Harness

标准做法：

- Harness 是标准运行外壳，负责稳定运行 Agent task，并收集过程数据。
- 它应该定义任务目标、成功标准和执行边界，而不只是保存几个 prompt 样例。
- 它应该记录输入、输出、工具 trajectory、artifact、trace、耗时、校验结果和违规原因。
- 它应该同时验证 final response 和 trajectory，例如是否先检索业务规则、再查数据库、最后生成图表。
- dry-run 应该离线稳定，不依赖真实 LLM、真实 Embedding 或外部网络。
- live-run 才调用真实 Agent / LLM。

本项目现状：

- 新增 `src/harness/`。
- 新增 `data/harness_cases.yaml`。
- 新增 `make harness` 和 `make harness-live`。
- dry-run 使用 `ScriptedLLM` 和 `ScriptedTool`，稳定触发 tool-call loop，但不执行真实工具副作用。
- harness case 已包含 `goal`、`success_criteria`、`limits`、`expect` 和 `script`。
- harness 会校验必须工具、禁止工具、工具顺序、工具调用次数、关键词、来源、skill、artifact 和耗时。
- harness result 会记录 `run_id`、状态、trajectory、trace、检查项和违规原因。

判断：

- 这个设计符合学习型 Agent 项目的标准做法。
- 它不是生产级调度器，也不负责真正的持久化恢复；如果后续要做长任务和断点恢复，可以参考 LangGraph durable execution。
- 重点修正点：dry-run 必须不触发真实 RAG / Embedding，这一点已经通过脚本化工具解决。

## 5. Evaluation / Benchmark

标准做法：

- Eval 不只是测试最终答案，还应该评估 agent trajectory。
- LangSmith / AgentEvals 强调工具调用轨迹可以做 deterministic match 或 LLM judge。
- Eval 和 Test 不同：Test 保证基本正确，Eval 衡量质量和回归。

本项目现状：

- `src/eval/benchmark.py` 支持 benchmark dry-run / live。
- `src/harness/` 已开始收集 trajectory。
- 默认测试稳定，不依赖真实模型。

判断：

- 当前已经有学习项目所需的雏形。
- 后续建议把 `src/eval/` 和 `src/harness/` 更深度打通：由 harness 产出 run result，再由 eval 模块计算 score。

## 6. RAG

标准做法：

- RAG 评估要分成 retrieval evaluation 和 response evaluation。
- Retrieval eval 常见指标包括 hit-rate、MRR、Precision、Recall、NDCG。
- Response eval 关注 answer relevancy、faithfulness、context relevancy 等。
- 检索结果应保留 source / node id / metadata，便于引用和评估。

本项目现状：

- 有 loader、chunker、embedder、vector store、BM25、reranker、manifest。
- RAG 是轻量自研版，适合学习。
- chunk metadata 已包含稳定 `chunk_id`、`chunk_hash`、`section`、`citation`，便于引用、去重和评估。
- `rag_search` 输出 source、chunk_id、section、score 和 citation，Agent 可以基于片段回答并保留来源。
- manifest 记录 schema version、chunk 配置、embedding 模型和文档签名，避免 chunk schema 或配置变化后复用旧索引。
- 新增 `data/rag_eval_cases.yaml` 和 `src/eval/rag_eval.py`，可离线输出 Source Hit@K、Source Recall@K、Context Precision@K、Keyword Coverage、MRR。
- 新增 `data/rag_response_eval_cases.yaml` 和 `src/eval/rag_response_eval.py`，可离线输出 citation hit、faithfulness 和 coverage，判断最终回答是否基于检索上下文。
- RAG 索引和离线评估默认使用 semantic chunk，更适合保留指标定义、表结构和标题语义。
- Retriever 修复了 BM25 结果元数据保留，并增加轻量 lexical score，提升表名/字段名这类精确查询。

判断：

- 当前 RAG 原理链路清晰，已具备标准学习项目需要的检索、引用和检索评估能力。
- 下一步可以补 metadata filter 和 query rewrite。

## 7. Observability / Trace

标准做法：

- OpenAI Agents SDK 把一次完整 run 视为 trace，并把 LLM、tool、guardrail、handoff 等步骤记录为 spans。
- Trace 用于 debug、可视化、监控和生产排查。
- 应记录耗时、输入输出摘要、错误、token usage 等。

本项目现状：

- `src/observability.py` 有 TraceRecorder。
- Agent 会记录 LLM 调用、工具调用、错误和 token usage。
- Streamlit UI 展示 Trace / 性能面板。

判断：

- 学习项目已经合格。
- 后续可改成更标准的 trace/span 层级结构，支持 trace_id、span_id、parent_id、metadata 和导出文件。

## 8. 安全与权限

标准做法：

- Agent 工具越强，安全边界越重要。
- 高风险工具需要隔离、权限控制、审计和用户确认。
- 第三方 skills 也应该被视为潜在风险来源，只安装可信来源。

本项目现状：

- SQL 只允许安全查询。
- 文件和 CSV 做路径边界校验。
- Python 使用子进程沙箱、超时、输出截断和白名单限制。
- 已安装 Codex 安全相关 skills：`security-best-practices`、`security-threat-model`，重启 Codex 后可用于继续审查。

判断：

- 已具备基础安全意识。
- 后续建议补工具权限模型和 threat model 文档。

## 总体结论

当前项目已经适合作为“标准 Agent 学习项目”：

- 模块完整。
- 关键概念清晰。
- 默认验证离线稳定。
- 文档和学习路径逐步完善。

最值得继续补的三件事：

1. RAG eval：扩大评估集，并区分 retrieval eval 和 response eval。
2. Tool permissions：补工具风险等级和用户确认机制。
3. Skills standardization：尝试把当前 `src/skills/` 映射到 `SKILL.md` 文件系统标准。
