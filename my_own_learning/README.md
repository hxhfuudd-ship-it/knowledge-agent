# 我的 Agent 学习资料包

这个文件夹集中放置“为了学习和面试而补充”的资料。它不替代项目正式文档，而是作为你自己的学习路线、讲解稿、框架对比和演示脚本。

## 推荐阅读顺序

1. `learning_path.md`：按模块学习标准 Agent 项目。
2. `framework_comparison.md`：理解这个项目和 LangChain、LangGraph、LlamaIndex 等框架的区别。
3. `standards_review.md`：对照官方资料判断项目各模块是否规范。
4. `demo_scenarios.md`：准备能现场演示的 Agent 场景。
5. `interview_guide.md`：整理成面试时能讲清楚的项目表达。

## 这个项目的定位

这个项目不是直接使用 LangChain / LlamaIndex / CrewAI 搭出来的 demo，而是一个从零实现的轻量 Agent 工程骨架：

- Agent Core：自己实现 ReAct 循环。
- LLM Adapter：自己封装 Anthropic / OpenAI 兼容接口。
- Tools：自己定义工具基类、参数 schema、注册和执行逻辑。
- RAG：自己实现文档加载、切片、Embedding、向量存储、BM25 和重排。
- Memory：自己实现短期、长期、情景、工作记忆。
- MCP：自己实现 client/server 接入示例。
- Eval / Trace / CI：自己实现评估、可观测性和质量门禁。

所以它非常适合用来学习 Agent 的底层机制。后续如果生产化，可以再把部分模块替换成 LangGraph、LlamaIndex、LangSmith 等成熟工具。

## 学习目标

学完这个项目，你应该能回答：

- Agent 和普通 Chatbot 的区别是什么？
- ReAct 循环如何工作？
- LLM 是如何选择工具的？
- Tool schema 为什么重要？
- RAG 为什么不只是向量检索？
- Memory 有哪些类型，各自解决什么问题？
- MCP 解决了什么工程问题？
- 为什么 Agent 必须有 Evaluation 和 Observability？
- 自研 Agent 和使用 LangChain / LangGraph 有什么差异？

## 面试表达核心句

可以用下面这句话概括项目：

> 这是一个我从零实现的标准 Agent 学习项目，不依赖 LangChain，而是手写了 Agent Core、Tool Calling、RAG、Memory、MCP、Evaluation、Trace 和 CI，用来理解 Agent 系统的底层结构和工程化边界。
