# 项目进度记录

## 总览

| 模块 | 状态 | 说明 |
|------|------|------|
| Agent 核心 | 已完成 | ReAct 循环、Tool Use、Skill 路由、流式输出、Trace 记录 |
| LLM 抽象层 | 已完成 | Anthropic / OpenAI 兼容适配器、统一 Tool Call 与 Usage 格式 |
| 工具层 | 已完成 | SQL、计算、文件、Python、搜索、图表、CSV、RAG 等核心工具 |
| Skills 系统 | 已完成 | 4 个 Skill + keyword / embedding / hybrid 路由 |
| RAG 系统 | 已完成 | 文档加载、切片、Embedding、向量检索、BM25、索引变更检测 |
| MCP 协议 | 已完成 | SQLite Server、Knowledge Server、JSON-RPC Client |
| 记忆系统 | 已完成 | 短期、长期、情景、工作记忆 |
| 多 Agent | 已完成 | Orchestrator + 3 个 SubAgent |
| 评估体系 | 已完成 | 指标、基准用例、dry-run/live Benchmark CLI、Markdown 报告 |
| 微调模块 | 已完成 | 数据准备、LoRA 训练脚本、推理封装 |
| 可观测性 | 已完成 | TraceRecorder、LLM/Tool 耗时、Token Usage、错误事件、前端 Trace 面板 |
| CI / 质量门禁 | 已完成 | Makefile、scripts/test.sh、scripts/lint.sh、GitHub Actions、pytest.ini |
| 环境检查 | 已完成 | make doctor / python -m src.doctor 检查配置、数据库、知识库和依赖 |
| 标准入口命令 | 已完成 | make run-app、make init-db、make benchmark、make check 等统一入口 |
| 前端界面 | 已完成 | Streamlit 对话、项目管理、CSV 导入、记忆管理、Trace 展示 |
| 测试 | 已完成 | 默认使用假 Embedding 稳定 CI；当前 35 passed、1 skipped |
| 文档 | 已完成 | README、PROGRESS、.env.example、docs/agent_architecture.md |

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
   - file_tool / csv_import_tool / MCP Knowledge Server：统一路径边界校验，防止路径遍历
   - sql_tool：token 级 SQL 注入检测，只允许安全查询形态
   - python_tool：从同进程 exec 升级为隔离子进程执行，增加超时、输出截断、代码长度限制和安全 import/builtin 白名单
   - MCP Server：SQL 表名、文件名、知识库路径均做显式校验

2. **架构**
   - 统一配置系统（settings.yaml + 环境变量覆盖）
   - LLM Provider Adapter 抽象：Agent 不再绑定单一模型厂商
   - requirements.txt / requirements-dev.txt 拆分运行依赖和开发依赖
   - Makefile + scripts/ 标准化本地入口命令
   - GitHub Actions 固化 CI 质量门禁

3. **RAG 与 Embedding**
   - 从哈希伪向量升级到 sentence-transformers / Voyage / 哈希三级回退
   - 默认测试使用 Fake/Hash Embedding，避免 CI 下载真实模型
   - 真实 Embedding 测试通过 pytest marker 单独启用
   - RAG 索引增加 manifest 变更检测，知识库文件变化后自动重建
   - BM25 索引可从持久化向量库恢复，避免重启后关键词检索失效

4. **健壮性**
   - SQLite 连接使用 with 上下文管理
   - JSON 文件加载增加异常处理
   - MCP Client 增加 BrokenPipeError 处理
   - Agent 对话存储修复（raw blocks → text string）
   - Agent 对话窗口增加自动裁剪与压缩
   - Benchmark 默认 dry-run，避免评估命令误触真实 LLM 调用

5. **可观测性**
   - TraceRecorder 记录每轮 Agent 执行过程
   - LLM 调用记录耗时、stop_reason、token usage
   - Tool 调用记录工具名、耗时、输入/输出摘要和成功状态
   - Streamlit 前端展示 Trace / 性能面板，便于调试 Agent 行为

6. **工程化**
   - make check 一条命令完成 lint + test
   - make doctor 一条命令检查运行环境
   - make benchmark / make benchmark-live 区分离线结构评估和真实模型评估
   - docs/agent_architecture.md 沉淀标准 Agent 项目模块说明

---

## 学习知识点索引

| 知识点 | 对应文件 | 核心概念 |
|--------|----------|----------|
| Agent 架构 | src/agent/core.py | ReAct 循环、Tool Use、流式输出、Trace 汇总 |
| LLM 抽象层 | src/llm/ | Provider Adapter、统一响应模型、Tool Call 适配 |
| Function Calling | src/tools/base.py | JSON Schema 参数定义、工具注册、Claude/OpenAI 工具格式 |
| 工具安全 | src/tools/python_tool.py、src/path_utils.py | 子进程沙箱、路径边界、防注入校验 |
| RAG 流水线 | src/rag/ | 切片、Embedding、混合检索、BM25、索引生命周期 |
| MCP 协议 | src/mcp/ + mcp_servers/ | JSON-RPC、Server/Client、外部能力接入 |
| Skill 编排 | src/skills/ | Tool 组合、专用 Prompt、语义/关键词路由 |
| 记忆系统 | src/memory/ | 短期/长期/情景/工作记忆、上下文压缩 |
| 多 Agent | src/multi_agent/ | 任务分解、编排、聚合 |
| 可观测性 | src/observability.py、src/agent/core.py | Trace、耗时、Token、工具调用审计 |
| 评估 | src/eval/benchmark.py、data/test_cases.yaml | dry-run/live Benchmark、报告生成 |
| 微调 | src/finetune/ | LoRA、数据准备、推理封装 |
| 环境检查 | src/doctor.py | 配置、数据库、知识库、依赖健康检查 |
| 质量门禁 | Makefile、scripts/、.github/workflows/ci.yml | 本地一键验证、CI 自动化、开发依赖隔离 |
| 架构文档 | docs/agent_architecture.md | 标准 Agent 项目模块拆解与学习路径 |

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
6. DeepSeek 端到端验证通过：
   - SQL 查询（rag_search + sql_query + create_chart 联动）
   - 数学计算（calculator 工具调用）
   - RAG 检索（rag_search + read_file，准确返回业务规则）
   - 修复 OpenAIAdapter 缺失 _normalize 方法

### Day 5 — 数据导入 + 多项目管理

1. python_tool 安全检查修复 — import/builtin 检测从字符串包含改为正则匹配（\b 词边界），防止空格绕过
2. CSV 导入工具（src/tools/csv_import_tool.py）：
   - pandas 读取 CSV 写入 SQLite
   - 表名正则校验 + 文件路径遍历防护
   - 支持 replace/append 模式
   - 返回导入摘要（行数、列名、数据类型、预览）
3. sql_tool 动态表结构感知：
   - 新增 _get_table_info() 读取 sqlite_master + PRAGMA table_info
   - description 从硬编码改为动态生成，覆写 to_claude_tool()
   - 导入新表后 Agent 自动感知
4. 命令行批量导入脚本（import_csv.py）：
   - 支持单文件和文件夹批量导入
   - --project 参数指定目标项目数据库
   - --list 列出所有项目
5. 多项目数据库管理：
   - 每个项目独立 SQLite 文件（data/databases/*.db）
   - config.py 新增 set() 函数，运行时动态切换数据库
   - settings.yaml 默认路径改为 data/databases/default.db
6. Streamlit 前端升级：
   - 项目切换下拉框 + 新建/删除项目
   - CSV 多文件上传批量导入
   - 数据库表列表动态展示（实时读取当前项目）
   - 示例问题改为两列网格布局 + 图标

### Day 6 — 标准 Agent 工程化补齐

1. 数据库默认路径统一为 data/databases/default.db，避免脚本、工具和配置各自指向不同数据库
2. 新增 src/path_utils.py，集中管理路径边界校验、SQL 标识符校验、文件名到表名转换、项目名规范化
3. RAG 索引生命周期补强：新增 data/vector_store_manifest.json 变更检测，知识库文件变化后自动重建索引
4. Retriever 支持从持久化向量库恢复 BM25 索引，解决重启后关键词检索状态丢失问题
5. Embedding 测试默认 mock / fake 化，完整测试集不再依赖真实模型下载；真实 Embedding 测试改为 RUN_EMBEDDING_TESTS=1 单独启用
6. 新增 pytest.ini，标记 embedding 测试，统一 pytest 行为
7. 新增 requirements-dev.txt，将 pytest、ruff 等开发依赖从运行依赖中拆出
8. 新增 Makefile、scripts/test.sh、scripts/lint.sh 和 .github/workflows/ci.yml，形成 make check 本地/CI 统一质量门禁
9. python_tool 从同进程 exec 改为隔离子进程执行，增加 -I isolated mode、3 秒超时、输出截断和代码长度限制
10. Agent 测试补充 fake LLM ReAct 循环覆盖，保证工具调用链路可以离线稳定验证
11. 新增 src/observability.py TraceRecorder，Agent 返回 trace，记录 LLM/Tool 耗时、Token Usage、输入输出摘要和错误事件
12. Streamlit 前端新增 “Trace / 性能” 面板，能直接观察每轮 Agent 的工具调用和性能信息
13. 新增 src/doctor.py，支持 python3 -m src.doctor / make doctor 检查 .env、LLM 凭据、数据库、知识库和关键依赖
14. src/eval/benchmark.py 标准化为 CLI，默认 dry-run 校验测试用例结构，--live 才调用真实 Agent/LLM
15. 新增 scripts/run_app.sh、scripts/init_db.sh，并通过 make run-app / make init-db 暴露标准入口命令
16. 新增 docs/agent_architecture.md，把本项目沉淀为标准 Agent 工程骨架学习文档
17. 最新验证：make doctor 通过（11 passed, 0 failed）；make check 通过（35 passed, 1 skipped）

### Day 7 — 开发与贡献文档补齐

1. 新增 CONTRIBUTING.md，明确贡献目标、本地开发流程、代码规范、安全边界、测试要求和 PR 检查清单
2. 新增 docs/development.md，沉淀标准 Agent 项目的开发心智模型、模块扩展流程、测试策略、可观测性规范和排查路径
3. README 增加开发与贡献文档入口，形成 README → 架构文档 → 开发手册 → 贡献指南的学习路径

### Day 8 — 个人学习资料包整理

1. 新建 my_own_learning/ 文件夹，集中保存面向个人学习和面试准备的补充资料
2. 新增 my_own_learning/learning_path.md，按 Agent Core、Tool、RAG、Skill、Memory、MCP、Eval、Trace 组织学习路径
3. 新增 my_own_learning/interview_guide.md，整理项目介绍、亮点讲法、Demo 路线和常见面试问答
4. 新增 my_own_learning/framework_comparison.md，对比 LangChain、LangGraph、LlamaIndex、CrewAI、AutoGen 等框架与本项目的关系
5. 新增 my_own_learning/demo_scenarios.md，沉淀 RAG、SQL、图表、CSV、Python 沙箱、Trace、Benchmark 等演示脚本
6. README 增加 my_own_learning/README.md 入口，把正式工程文档和个人学习资料区分开

### Day 9 — Agent Harness 标准运行外壳

1. 调研 OpenAI Agents SDK tracing/evals、Anthropic Agent Skills、LangSmith trajectory eval、LlamaIndex retrieval eval 等一手资料，确定项目内 harness 的职责边界
2. 新增 src/harness/，包含结构化模型、runner、validators 和 CLI，用于统一运行 Agent 场景并收集回答、工具轨迹、skill、trace、耗时和校验结果
3. 新增 data/harness_cases.yaml，提供 calculator、RAG、SQL+Chart 三类 dry-run 场景，使用脚本化 LLM 稳定触发工具调用
4. 新增 tests/test_harness.py，覆盖 harness case 校验和脚本化 tool-call loop
5. Makefile 增加 make harness / make harness-live，区分离线可回归场景和真实 Agent/LLM 端到端场景
6. README、docs/development.md、docs/agent_architecture.md 和 my_own_learning/ 学习资料补充 Harness、Eval、Tests 的职责边界
7. 新增 my_own_learning/standards_review.md，对照 OpenAI Agents SDK、Agent Skills、LangSmith、LlamaIndex 等资料说明当前项目规范性和后续补强路线
8. 安装 security-best-practices、security-threat-model 两个 Codex skills，后续重启 Codex 后可用于继续审查 Agent 工具权限和威胁模型

### Day 10 — RAG Eval 检索评估补齐

1. 新增 data/rag_eval_cases.yaml，定义 GMV、复购率、订单表结构、部门职责等检索评估用例
2. 新增 src/eval/rag_eval.py，离线构建 retriever 并输出 Source Hit@K、Keyword Hit Rate、MRR 和明细报告
3. 新增 tests/test_rag_eval.py，验证 RAG eval 用例加载和离线 retriever 可运行
4. Makefile 增加 make rag-eval，生成 data/rag_eval_report.md；默认只报告指标，不阻塞质量门禁
5. README、docs/development.md 和 my_own_learning/ 文档补充 RAG eval 的定位、指标和使用方式

### Day 11 — RAG 检索质量基础优化

1. RAG 索引从 recursive chunk 调整为 semantic chunk，优先保留标题、表结构和业务指标定义边界
2. Retriever.search_bm25 返回 metadata，修复 BM25 命中后来源信息丢失的问题
3. Hybrid 检索加入轻量 lexical score，提升表名、字段名、指标名等精确匹配查询的稳定性
4. RAG eval 当前用例达到 Source Hit@K 100%、Keyword Hit Rate 100%、MRR 1.0
5. tests/test_rag.py 和 tests/test_rag_eval.py 增加 BM25 metadata、hybrid metadata 和当前 RAG eval 用例回归测试

### Day 12 — 标准 Agent Skills 文件系统

1. 新增 skills/README.md，说明文件系统 Skills 和 src/skills/ 运行时 SkillRegistry 的关系
2. 新增 skills/data-analysis/SKILL.md、skills/sql-expert/SKILL.md、skills/doc-qa/SKILL.md、skills/report-generation/SKILL.md
3. 每个 SKILL.md 包含 name、description、version、tools、runtime_mapping、适用场景、工作流、工具规范、输出要求和示例问题
4. 新增 tests/test_skill_files.py，校验 SKILL.md frontmatter 和运行时代码映射
5. README、docs/agent_architecture.md、docs/development.md 和 my_own_learning/ 文档补充标准 Skills 文件系统说明
