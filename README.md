# 个人知识库数据 Agent

通过构建一个完整的数据 Agent，系统学习 Agent 开发核心技术栈。

## 技术栈

- LLM：Claude API（Anthropic）
- Embedding：sentence-transformers（本地模型）
- 向量存储：纯 Python 实现（JSON 持久化 + 余弦相似度）
- 数据库：SQLite
- 前端：Streamlit
- MCP：Python MCP SDK（stdio 通信）

## 快速开始

```bash
# 1. 安装运行依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 ANTHROPIC_API_KEY

# 3. 初始化数据库
make init-db

# 4. 检查本地环境
make doctor

# 5. 启动界面
make run-app
```

开发和运行测试时安装额外依赖：

```bash
pip install -r requirements-dev.txt
```

## 项目结构

```
knowledge-agent/
├── config/settings.yaml       # 全局配置（模型、RAG 参数、记忆等）
├── src/
│   ├── agent/core.py          # Agent 核心 ReAct 循环
│   ├── tools/                 # 工具层（6 个工具）
│   │   ├── sql_tool.py        # SQL 查询（Text-to-SQL）
│   │   ├── calculator_tool.py # 安全数学计算（AST 求值）
│   │   ├── file_tool.py       # 文件读取（路径遍历防护）
│   │   ├── python_tool.py     # Python 沙箱执行
│   │   ├── search_tool.py     # 网络搜索（演示模式）
│   │   └── chart_tool.py      # 数据可视化（matplotlib）
│   ├── skills/                # 技能层（4 个 Skill）
│   │   ├── data_analysis.py   # 数据分析
│   │   ├── sql_expert.py      # SQL 专家
│   │   ├── report_gen.py      # 报告生成
│   │   └── doc_qa.py          # 文档问答
│   ├── rag/                   # RAG 检索增强
│   │   ├── loader.py          # 文档加载（PDF/MD/TXT）
│   │   ├── chunker.py         # 文本切片（固定/递归/语义）
│   │   ├── embedder.py        # Embedding（本地模型/Voyage/哈希回退）
│   │   ├── retriever.py       # 混合检索（向量 + BM25）
│   │   ├── reranker.py        # 重排序
│   │   └── vector_store.py    # 纯 Python 向量存储
│   ├── memory/                # 记忆系统（4 种类型）
│   │   ├── short_term.py      # 短期记忆（滑动窗口）
│   │   ├── long_term.py       # 长期记忆（向量持久化）
│   │   ├── episodic.py        # 情景记忆（交互摘要）
│   │   └── working.py         # 工作记忆（任务状态）
│   ├── multi_agent/           # 多 Agent 协作
│   │   └── orchestrator.py    # 编排器（任务分解 → 子 Agent → 聚合）
│   ├── mcp/client.py          # MCP 客户端
│   ├── eval/                  # 评估体系
│   │   ├── metrics.py         # 评估指标
│   │   ├── benchmark.py       # 基准测试
│   │   └── test_cases.yaml    # 测试用例
│   ├── finetune/              # 微调模块
│   │   ├── data_prep.py       # 数据准备
│   │   ├── train.py           # LoRA 训练
│   │   └── inference.py       # 推理
│   └── config.py              # 配置加载器
├── mcp_servers/               # MCP Server 进程
│   ├── sqlite_server.py       # SQLite MCP Server
│   └── knowledge_server.py    # 知识库 MCP Server
├── skills/                    # 标准 Agent Skills 文件系统（SKILL.md）
├── data/
│   ├── databases/default.db   # SQLite 模拟数据（6 张表）
│   └── documents/             # 知识库文档
├── tests/                     # 测试文件
├── app.py                     # Streamlit 主界面
└── requirements.txt
```

## 核心模块说明

更完整的标准 Agent 架构说明见：`docs/agent_architecture.md`。

### Agent 核心（ReAct 循环）
感知 → 思考 → 行动 → 观察，循环直到任务完成。支持 Tool Use 和 Skill 路由。

### Tool vs Skill
- Tool 是原子操作（查 SQL、读文件、算数学）
- Skill 是组合能力（数据分析 = 查数据 + 处理 + 可视化 + 结论）
- `src/skills/` 是运行时 SkillRegistry，`skills/*/SKILL.md` 是标准文件系统说明层

### RAG 流程
文档加载 → 切片 → Embedding → 向量存储 → 混合检索（向量 + BM25）→ 重排序 → 上下文注入

### 记忆系统
短期（对话窗口）+ 长期（向量持久化）+ 情景（历史摘要）+ 工作（任务状态）

### MCP 协议
通过 JSON-RPC stdio 通信，将数据源封装为标准化服务。

## Embedding 模型

配置 `config/settings.yaml` 中的 `rag.embedding_model`：

| 值 | 模型 | 维度 | 适用 |
|---|---|---|---|
| chinese | text2vec-base-chinese | 768 | 中文（默认） |
| multilingual | paraphrase-multilingual-MiniLM-L12-v2 | 384 | 多语言 |
| english | all-MiniLM-L6-v2 | 384 | 英文 |

## 测试

默认测试使用假 Embedding / 哈希回退，不会下载或加载真实模型，适合本地开发和 CI：

```bash
pip install -r requirements-dev.txt
```

```bash
make test
```

运行完整质量门禁（lint + test）：

```bash
make check
```

检查本地运行环境（`.env`、API Key、数据库、依赖）：

```bash
make doctor
```

如需验证真实 Embedding 模型可用性，显式开启集成测试：

```bash
make test-embedding
```

## 常用入口命令

| 命令 | 说明 |
|---|---|
| `make init-db` | 初始化 SQLite 示例数据库 |
| `make run-app` | 启动 Streamlit Web UI |
| `make doctor` | 检查本地环境、密钥、数据库和依赖 |
| `make benchmark` | dry-run 基准测试，验证评估用例结构并生成报告 |
| `make benchmark-live` | 使用真实 Agent/LLM 跑基准测试并生成报告 |
| `make harness` | 使用脚本化 LLM 跑标准 Agent harness 场景，收集工具轨迹和 trace |
| `make harness-live` | 使用真实 Agent/LLM 跑 harness 场景 |
| `make rag-eval` | 离线评估 RAG 检索质量，输出 Source Hit@K、Keyword Hit Rate、MRR |
| `make check` | 运行 lint + 默认测试 |

## 学习、开发与贡献文档

- 个人学习路径、面试讲解、框架对比和 Demo 脚本见：`my_own_learning/README.md`
- 贡献流程、代码规范和 PR 检查清单见：`CONTRIBUTING.md`
- 开发者扩展手册、模块新增流程和排查指南见：`docs/development.md`
- 标准 Agent 架构拆解见：`docs/agent_architecture.md`

## 配置

所有配置集中在 `config/settings.yaml`，支持环境变量覆盖（如 `AGENT_LLM_MODEL`）。

## Agent Harness

Harness 是项目的标准运行外壳，用于验证 Agent 是否能在明确任务目标、成功标准和执行边界内，持续稳定、可复现地把事情做完。

- `src/harness/`：Harness runner、结构化模型和校验器
- `data/harness_cases.yaml`：标准 task case，包含目标、成功标准、执行限制、期望工具轨迹和 dry-run script
- `make harness`：默认脚本化 dry-run，不调用真实 LLM，适合 CI、教学和演示回归
- `make harness-live`：调用真实 Agent / LLM，适合人工验收
- 结果会记录 `run_id`、状态、最终回答、工具轨迹、artifact、trace、耗时、检查项和违规原因

它和 benchmark 的区别是：Harness 负责“如何标准化运行、约束并验证任务过程”，Benchmark/Eval 负责“如何评分和生成质量报告”。

## RAG Eval

RAG eval 用于单独评估检索阶段，不评价最终回答：

- `data/rag_eval_cases.yaml`：检索评估用例，包含 query、期望来源和关键词
- `src/eval/rag_eval.py`：离线构建 retriever，输出 Source Hit@K、Source Recall@K、Context Precision@K、Keyword Coverage、MRR
- 检索默认使用 semantic chunk，保留标题/表结构等语义单元，并为每个 chunk 生成稳定 `chunk_id`、`chunk_hash` 和 `citation`
- 索引 manifest 会记录 schema version、chunk 配置、embedding 模型和文档签名，避免代码或配置变化后复用旧索引
- `rag_search` 输出包含 source、chunk_id、section、score 和 citation，便于 Agent 基于来源回答
- `make rag-eval`：生成 `data/rag_eval_report.md`

默认 `make rag-eval` 只输出指标，不作为质量门禁失败；如果要把它作为严格回归检查，可使用 `python3 -m src.eval.rag_eval --fail-on-regression`。

## RAG Response Eval

RAG response eval 用于评估最终回答是否基于检索上下文：

- `data/rag_response_eval_cases.yaml`：包含 query、期望关键词和参考回答
- `src/eval/rag_response_eval.py`：离线评估 citation hit、faithfulness 和 coverage
- `make rag-response-eval`：生成 `data/rag_response_eval_report.md`

这一步和检索评估分开：前者看“找没找到”，后者看“答得是不是基于找到的内容”。
