# 项目进度记录

## 总览

| 模块 | 状态 | 说明 |
|------|------|------|
| Agent 核心 | 已完成 | ReAct 循环、Tool Use、Skill 路由 |
| 工具层 | 已完成 | 6 个工具全部实现 |
| Skills 系统 | 已完成 | 4 个 Skill + 关键词匹配路由 |
| RAG 系统 | 已完成 | 完整流水线 + 真实 Embedding |
| MCP 协议 | 已完成 | 2 个 Server + Client |
| 记忆系统 | 已完成 | 4 种记忆类型 |
| 多 Agent | 已完成 | Orchestrator + 3 个 SubAgent |
| 评估体系 | 已完成 | 指标 + 基准测试 + 测试用例 |
| 微调模块 | 已完成 | 数据准备 + 训练脚本 + 推理 |
| 前端界面 | 已完成 | Streamlit 对话 + 记忆管理 |
| 测试 | 已完成 | 4 个测试文件，全部通过 |
| 文档 | 已完成 | README + PROGRESS + .env.example |

---

## 详细记录

### 第一阶段：基础骨架

- [x] 项目结构搭建
- [x] Agent 核心 ReAct 循环（感知 → 思考 → 行动 → 观察）
- [x] Tool 基类 + ToolRegistry（统一注册和 Claude API 格式转换）
- [x] SQLTool：Text-to-SQL，SELECT 白名单，token 级关键词检测
- [x] CalculatorTool：AST 安全求值，替代 eval()
- [x] FileReadTool / FileListTool：路径遍历防护（resolve + startswith）
- [x] SQLite 模拟数据（6 张表：部门、员工、产品、客户、订单、订单明细）
- [x] Streamlit 基础界面（对话 + 工具调用展示 + 记忆管理）

### 第二阶段：RAG 模块

- [x] DocumentLoader：支持 PDF/MD/TXT，目录批量加载
- [x] TextChunker：固定切片 / 递归切片 / 语义切片（Markdown 标题）
- [x] Embedder：三级回退（本地 sentence-transformers → Voyage API → 哈希）
- [x] SimpleVectorStore：纯 Python 实现，JSON 持久化，余弦相似度
- [x] Retriever：混合检索（向量相似度 + BM25 关键词），中文分词优化
- [x] Reranker：LLM 重排序 + 简单关键词重排序
- [x] RAGSearchTool / RAGIndexTool：集成到 Agent 工具链
- [x] 三个 Embedding 模型全部下载就绪（chinese / multilingual / english）

### 第三阶段：Skills + MCP

- [x] Skill 基类 + SkillRegistry（关键词匹配路由）
- [x] 4 个 Skill：数据分析、SQL 专家、报告生成、文档问答
- [x] SQLite MCP Server（list_tables / describe_table / query）
- [x] Knowledge MCP Server（search / add_document / list_sources）
- [x] MCP Client（JSON-RPC stdio 通信，进程管理，错误处理）

### 第四阶段：记忆 + 多 Agent

- [x] 短期记忆：滑动窗口消息管理
- [x] 长期记忆：向量化持久存储，语义检索
- [x] 情景记忆：JSON 持久化交互摘要
- [x] 工作记忆：当前任务状态和步骤追踪
- [x] Orchestrator：LLM 任务分解 → SubAgent 分配 → 结果聚合
- [x] 3 个 SubAgent：数据分析师、信息检索员、报告撰写员

### 第五阶段：微调 + 评估

- [x] DataPrep：合成训练数据生成，JSONL 格式
- [x] LoRA 训练脚本（需 GPU 环境运行）
- [x] FineTunedClassifier 推理封装
- [x] 评估指标：工具准确率、检索质量、回答质量、延迟成本
- [x] Benchmark 自动化运行 + Markdown 报告生成
- [x] 10 个测试用例（sql / calculation / rag / analysis）

---

## 代码质量优化记录

以下是开发过程中做过的重要优化：

1. **安全性**
   - calculator_tool：eval() → AST 安全求值
   - file_tool：路径遍历防护（resolve + startswith）
   - sql_tool：token 级 SQL 注入检测
   - python_tool：沙箱执行，禁止危险模块和内置函数
   - MCP Server：正则表名验证，文件名校验

2. **架构**
   - 统一配置系统（settings.yaml + 环境变量覆盖）
   - 所有模块读 config，消除硬编码
   - 统一 logging 初始化
   - __init__.py 规范导出

3. **Embedding 升级**
   - 从哈希伪向量升级到真实 sentence-transformers
   - 检索相关度从 0.12 提升到 0.47-0.55
   - 支持三种模型切换（chinese / multilingual / english）

4. **健壮性**
   - SQLite 连接使用 with 上下文管理
   - JSON 文件加载增加异常处理
   - MCP Client 增加 BrokenPipeError 处理
   - Agent 对话存储修复（raw blocks → text string）
   - BM25 中文分词修复（单字符 → 字词混合）

---

## 学习知识点索引

| 知识点 | 对应文件 | 核心概念 |
|--------|----------|----------|
| Agent 架构 | src/agent/core.py | ReAct 循环、Tool Use |
| Function Calling | src/tools/base.py | JSON Schema 参数定义 |
| RAG 流水线 | src/rag/ | 切片、Embedding、混合检索 |
| MCP 协议 | src/mcp/ + mcp_servers/ | JSON-RPC、Server/Client |
| Skill 编排 | src/skills/ | Tool 组合 + 专用 Prompt |
| 记忆系统 | src/memory/ | 短期/长期/情景/工作记忆 |
| 多 Agent | src/multi_agent/ | 任务分解、编排、聚合 |
| 评估 | src/eval/ | LLM-as-Judge、Benchmark |
| 微调 | src/finetune/ | LoRA、数据准备 |
| 安全实践 | 各 tool 文件 | AST 求值、路径防护、SQL 过滤 |

---

## 开发日志

### Day 1 — 方案设计 + 基础骨架

1. 讨论项目方向，确定「个人知识库数据 Agent」作为学习载体
2. 编写完整开发方案（10 个模块、6 个阶段、技术选型）
3. 搭建项目目录结构（src/ 下 8 个子包）
4. 实现 Agent 核心 ReAct 循环（core.py）
5. 实现 3 个基础工具：sql_tool、calculator_tool、file_tool
6. 创建 SQLite 模拟数据（6 张表，data/init_db.py）
7. 编写知识库文档（business_rules.md、data_dictionary.py）
8. 实现 RAG 全流程：loader → chunker → embedder → vector_store → retriever → reranker
9. 实现 Skills 系统：4 个 Skill（数据分析、SQL 专家、报告生成、文档问答）
10. 实现 MCP：2 个 Server（SQLite、Knowledge）+ Client
11. 实现记忆系统：短期 / 长期 / 情景 / 工作记忆
12. 实现多 Agent 编排器 + 3 个 SubAgent
13. 实现评估体系：metrics + benchmark + 10 个测试用例
14. 实现微调模块：data_prep + train + inference
15. 搭建 Streamlit 前端界面

### Day 2 — 代码审查 + 质量优化

1. 全面代码审查，发现 55 个优化点
2. 安全修复：
   - calculator_tool 的 eval() 替换为 AST 安全求值
   - file_tool 路径遍历防护升级（resolve + startswith）
   - sql_tool 关键词检测从字符串包含改为 token 级匹配
   - MCP Server 增加正则表名验证和文件名校验
3. 架构优化：
   - 创建 src/config.py 统一配置加载（settings.yaml + 环境变量覆盖）
   - 所有模块从 config 读取参数，消除硬编码
   - Tool 基类从 abstract property 改为 class attribute（兼容性更好）
   - Agent 对话存储修复（response.content blocks → 纯文本）
4. 健壮性优化：
   - SQLite 连接改用 with 上下文管理
   - JSON 文件加载增加 JSONDecodeError / IOError 处理
   - MCP Client 增加 BrokenPipeError 和进程超时处理
   - BM25 中文分词修复（单字符切分 → 字词混合分词）
5. Python 3.9 兼容性修复（dict[str] → Dict[str]，X | Y → Optional[X]）
6. ChromaDB 编译失败 → 替换为纯 Python SimpleVectorStore
7. 所有 __init__.py 补充规范导出

### Day 3 — Embedding 升级 + 补齐缺失

1. Embedding 从哈希伪向量升级到 sentence-transformers 真实模型
2. 下载 3 个模型：chinese（text2vec-base-chinese）、english（all-MiniLM-L6-v2）、multilingual（paraphrase-multilingual-MiniLM-L12-v2）
3. 使用 hf-mirror.com 镜像加速下载
4. RAG 检索质量验证：相关度从 0.12 提升到 0.47-0.55
5. 修正 requirements.txt（移除 chromadb/sqlalchemy，加入 sentence-transformers）
6. 创建 .env.example
7. 添加统一 logging 配置（src/__init__.py）
8. Orchestrator 硬编码模型名改为读 config
9. 补齐 3 个缺失工具：
   - python_tool：沙箱执行（禁止危险模块和内置函数）
   - search_tool：演示模式（列出可接入的搜索 API）
   - chart_tool：matplotlib 图表生成（柱状图/折线图/饼图）
10. 编写 4 个测试文件（test_tools / test_agent / test_memory / test_rag），全部通过
11. 编写 README.md（项目介绍、快速开始、结构说明、Embedding 配置）
12. 编写 PROGRESS.md（进度总览、详细记录、优化记录、知识点索引）

### Day 3（续）— 功能性 Bug 修复

1. Retriever.add_documents ID 冲突修复 — 新文档 ID 从已有数量开始编号，避免覆盖
2. RAGSearchTool 和 RAGIndexTool 共享 Retriever — 通过模块级单例 _get_retriever() 保证索引状态一致
3. Agent.conversation 无限增长修复 — 添加 _trim_conversation()，与 short_term 同步截断
4. BASE_SYSTEM_PROMPT 更新 — 补充 python_exec、create_chart、web_search 三个新工具的描述
5. MCP Server PRAGMA 注入防护 — table_info(%s) 改为 table_info([%s])，配合正则校验双重保护
6. Skill 匹配升级 — SkillRegistry 支持三种策略：keyword（关键词）、embedding（语义）、hybrid（混合）
   - 语义匹配基于 Embedding 余弦相似度，阈值 0.35
   - hybrid 模式：关键词优先，无命中时回退语义匹配
   - 新增 match_with_scores() 方法，返回所有 Skill 的匹配分数，方便调试对比
   - Agent 默认使用 hybrid 策略
7. Streamlit 示例问题更新 — 增加图表和业绩相关的示例
8. settings.yaml 新增 agent.skill_match 配置项
9. 测试覆盖 Skill 语义匹配 — 新增 test_skill_embedding_match、test_skill_hybrid_match、test_skill_match_with_scores
10. Streamlit 界面升级：
    - 新增 Skill 路由详情面板（展示每个 Skill 的语义匹配分数和关键词命中情况）
    - RAG 检索结果可视化（rag_search 工具输出按片段分块展示）
    - 工具调用面板优化（区分 RAG 检索和普通工具输出）
11. Embedder 单例缓存 — 新增 get_embedder() 工厂函数，同一模型参数共享实例，避免重复加载
    - Retriever、LongTermMemory、SkillRegistry 统一使用 get_embedder()
12. Agent 流式输出 — 新增 chat_stream() 生成器方法
    - yield token/tool_call/done/error 事件
    - Streamlit 界面实时显示生成文本（带光标动画）
    - 工具调用过程中继续流式输出后续回答
13. 对话压缩 — ShortTermMemory 超长时自动压缩早期对话
    - 优先用 LLM 压缩（保留数据发现、用户偏好、重要结论）
    - LLM 不可用时回退到简单截断
    - 压缩摘要注入 system prompt，保持上下文连贯
    - 修复 ThinkingBlock 兼容问题（过滤非 text 类型的 content block）

### Day 3（续2）— 细节打磨

1. Reranker 硬编码模型名修复 — 改为读 config
2. Reranker response.content[0].text ThinkingBlock 兼容修复
3. finetune/data_prep 合成数据补齐新工具 — 增加 python_exec、create_chart、web_search 样本
4. 创建 .gitignore — 忽略 __pycache__、.env、生成数据、模型文件等
5. test_cases.yaml 补充新工具测试用例 — 增加 Python 执行和图表生成用例（共 12 个）
6. rag/__init__.py 导出 get_embedder — 保持公开 API 完整

### Day 4 — LLM 多模型抽象层

1. 创建 src/llm/ 包 — Provider Adapter 模式
   - models.py：标准化响应模型（LLMResponse, ToolCall）
   - base_adapter.py：抽象适配器接口
   - anthropic_adapter.py：Anthropic Claude 适配器
   - openai_adapter.py：OpenAI 兼容适配器（DeepSeek / Kimi / OpenAI 等）
   - client.py：LLMClient 门面 + create_llm_client() 工厂函数
2. 迁移 4 个调用方：
   - src/agent/core.py — ReAct 循环 + 流式输出，全部改用 LLMClient
   - src/multi_agent/orchestrator.py — SubAgent 和 Orchestrator
   - src/rag/reranker.py — LLM 重排序
   - src/memory/short_term.py — 对话压缩
3. 关键设计决策：
   - stop_reason 统一映射（OpenAI "stop"→"end_turn", "tool_calls"→"tool_use"）
   - 工具格式自动转换（Claude input_schema ↔ OpenAI parameters）
   - 工具结果消息格式适配（Anthropic 打包 vs OpenAI 独立消息）
   - 助手消息构建适配（build_assistant_message）
4. 配置更新：
   - settings.yaml 新增 provider / base_url / api_key_env 配置项
   - config.py 新增 AGENT_LLM_PROVIDER / AGENT_LLM_BASE_URL 环境变量覆盖
   - .env.example 增加 DeepSeek 配置示例
   - requirements.txt 增加 openai>=1.0.0
5. Tavily 搜索接入 — search_tool 从演示模式升级为真实搜索
   - 配置 TAVILY_API_KEY 后自动启用 Tavily API
   - 未配置时回退到演示模式并提示获取方式
   - requirements.txt 增加 tavily-python
