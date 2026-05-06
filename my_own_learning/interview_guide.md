# Agent 项目面试指南

这份文档用于把项目整理成面试时能讲清楚、能演示、能回答追问的作品。

## 1 分钟介绍

> 我做了一个从零实现的个人知识库数据 Agent 项目。它没有直接使用 LangChain，而是自己实现了 Agent Core、Tool Calling、RAG、Memory、Skills、MCP、Evaluation、Trace 和 CI。这个项目的目标是帮助我理解标准 Agent 系统的内部结构：模型如何选择工具、工具结果如何回填、RAG 如何提供外部知识、Memory 如何管理上下文，以及如何用测试和 trace 让 Agent 行为可验证、可调试。

## 3 分钟介绍

可以按这个顺序讲：

1. **项目目标**：不是做聊天机器人，而是做一个标准 Agent 工程骨架。
2. **Agent Core**：自研 ReAct 循环，支持 tool call、skill route、memory 和 trace。
3. **Tool Calling**：SQL、计算、文件、Python、搜索、图表、CSV、RAG 都统一成 Tool。
4. **RAG**：实现文档加载、切片、Embedding、向量存储、BM25、rerank、manifest 索引更新。
5. **Memory**：短期、长期、情景、工作记忆分层。
6. **LLM Adapter**：支持 Anthropic / OpenAI 兼容接口，避免业务层绑定 provider。
7. **Harness / Eval / Trace**：用标准 harness 收集工具轨迹和 trace，用 benchmark 做评估，用 CI 做回归。
8. **工程化**：有 `make check`、CI、doctor、fake embedding 测试。
9. **安全性**：SQL 只允许 SELECT，路径边界校验，Python 子进程沙箱。

## 项目亮点

### 1. 自研 Agent Core

面试表达：

> 我没有直接用 LangChain 的 Agent，而是自己实现 ReAct 控制循环，这样能理解 Agent 到底如何组装 prompt、调用 LLM、解析 tool call、执行工具并把 observation 回填给模型。

对应源码：

- `src/agent/core.py`
- `src/tools/base.py`
- `src/llm/client.py`

### 2. Tool Calling 体系完整

面试表达：

> 我把所有外部能力抽象成 Tool，每个 Tool 都有稳定 name、description、JSON Schema parameters 和 execute 方法。这样 LLM 可以基于 schema 选择工具，Agent 可以统一执行和记录 trace。

可讲工具：

- SQL 查询
- 文件读取
- 数学计算
- Python 执行
- 搜索
- 图表生成
- CSV 导入
- RAG 检索和索引

### 3. RAG 不只是向量检索

面试表达：

> 项目的 RAG 包含 loader、chunker、embedder、vector store、BM25、reranker 和索引 manifest。向量检索解决语义相似，BM25 补关键词匹配，manifest 解决文档变化后索引过期的问题。

对应源码：

- `src/rag/`
- `src/rag/retriever.py`
- `src/rag/rag_tool.py`

### 4. 可观测性和评估

面试表达：

> Agent 项目不能只看最终回答，还要知道它为什么这么回答。我加了 TraceRecorder，记录每次 LLM 调用、工具调用、耗时、token usage、错误事件，并通过 Streamlit 面板展示。

对应源码：

- `src/observability.py`
- `src/eval/benchmark.py`
- `tests/`

### 5. 默认测试稳定

面试表达：

> 我把 embedding 相关测试 mock 掉，默认 CI 不依赖真实模型下载或外部网络；真实 embedding 测试通过显式 marker 单独运行。这样项目更适合持续集成。

对应文件：

- `pytest.ini`
- `tests/test_rag.py`
- `tests/test_agent.py`
- `Makefile`

### 6. 标准 Harness

面试表达：

> 我新增了 Agent harness，用脚本化 LLM 稳定触发工具调用，统一收集最终回答、工具轨迹、skill、trace、耗时和校验结果。这样 demo、回归测试和评估可以共用一套标准运行外壳，而不是只靠手动试问。

对应源码：

- `src/harness/`
- `data/harness_cases.yaml`
- `tests/test_harness.py`

## 推荐 Demo 路线

### Demo：业务指标分析

用户问题：

> 帮我分析本月 GMV，并生成图表。

理想链路：

1. Agent 识别这是数据分析任务。
2. 使用 RAG 查询 GMV 业务定义。
3. 使用 SQL 查询订单数据。
4. 使用计算或 Python 做汇总。
5. 使用图表工具生成可视化。
6. 返回分析结论。
7. 打开 Trace 面板展示完整工具链路。

你要强调：

- Agent 不是直接胡编答案，而是先查规则，再查数据，再分析。
- Trace 可以证明它调用了哪些工具。
- 工具层有安全边界。

## 常见面试问题与回答

### Q1：这个项目和 LangChain 有什么区别？

回答：

> LangChain 是现成框架，提供 Agent、Tool、Retriever、Memory 等抽象。我的项目没有使用 LangChain，而是自己实现这些核心模块，目的是学习底层原理。概念上两者类似，但这个项目更透明；如果要生产化，我可能会用 LangGraph 替换复杂状态编排，用 LlamaIndex 增强 RAG。

### Q2：为什么需要 Tool Calling？

回答：

> LLM 本身只会生成文本，不会真正查询数据库、读文件或画图。Tool Calling 把外部能力通过 schema 暴露给模型，模型决定调用哪个工具，Agent 负责执行工具并把结果返回给模型。

### Q3：RAG 和 Fine-tuning 的区别？

回答：

> RAG 是运行时检索外部知识，适合频繁变化、需要引用来源的知识；Fine-tuning 是把模式和风格学习进模型参数，适合稳定任务格式或分类能力。这个项目里 RAG 用来查业务规则和数据字典，微调用作可选学习模块。

### Q4：Memory 和 RAG 的区别？

回答：

> RAG 通常检索外部知识库，比如文档和业务规则；Memory 记录 Agent 和用户交互过程中产生的信息，比如用户偏好、历史任务、当前任务状态。RAG 更像外部资料库，Memory 更像 Agent 的经验和上下文管理。

### Q5：Agent 为什么需要 Trace？

回答：

> 因为 Agent 的行为是多步骤的。只看最终回答不知道它是否查了正确数据、是否调用了错误工具、哪里慢、哪里花 token。Trace 可以记录 LLM 调用、工具调用、耗时、token 和错误，方便调试、评估和优化。

### Q5.1：Harness、Benchmark、Test 有什么区别？

回答：

> Harness 负责标准化运行 Agent 并收集过程，比如回答、工具调用、trace 和耗时；Benchmark 负责定义评分和生成评估报告；Test 负责在 CI 里做自动断言，保证核心能力不退化。三者边界清楚后，Agent 项目更容易调试和持续改进。

### Q6：这个项目有什么安全设计？

回答：

> SQL 工具默认只允许 SELECT；文件和 CSV 工具有路径边界校验；Python 工具使用隔离子进程、超时、输出截断和 import/builtin 限制；MCP Server 对表名和文件名做校验。核心原则是工具层必须自己做安全校验，不能只依赖 prompt。

### Q7：为什么默认测试不用真实 Embedding？

回答：

> 真实 embedding 模型下载慢、环境依赖重，CI 容易不稳定。默认测试用 fake/hash embedding 验证流程正确性，真实模型测试通过 `make test-embedding` 显式运行。这是为了区分单元测试和集成测试。

### Q8：项目目前还缺什么？

回答：

> 作为学习项目已经比较完整。生产化还需要 FastAPI 服务层、工具权限系统、用户确认机制、结构化输出 schema、Docker 部署、监控日志、RAG 评估集和更强的 prompt 注入防护。

## 面试时不要这样说

不要说：

> 我做了一个聊天机器人。

更好的说法：

> 我做了一个标准 Agent 架构学习项目，重点是 Agent 的控制循环、工具调用、RAG、Memory、MCP、评估、可观测性和安全边界。

不要说：

> 我接了几个 API。

更好的说法：

> 我把不同 provider 封装成 LLM Adapter，业务层只依赖统一的 LLMResponse 和 ToolCall 模型。

## 简历写法

可以写：

> 从零实现个人知识库数据 Agent，包含 ReAct 控制循环、Tool Calling、RAG 检索增强、短期/长期/工作记忆、MCP client/server、LLM provider adapter、Harness 标准运行外壳、Benchmark 评估、Trace 可观测性和 CI 质量门禁；默认测试 mock Embedding，支持离线稳定验证。

## 最后总结

这个项目面试的核心竞争力不是“功能很多”，而是：

- 你能讲清 Agent 的底层机制。
- 你能解释每个模块为什么存在。
- 你能演示一次完整工具调用链路。
- 你能说明安全、评估、可观测性和工程化考虑。
