<div align="center">

# Knowledge Agent

**个人知识库数据 Agent — 系统学习 Agent 开发核心技术栈**

**Personal Knowledge Base Agent — Learn core Agent development technologies by building.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776ab?logo=python&logoColor=white)](https://python.org)
[![Claude API](https://img.shields.io/badge/Claude_API-Anthropic-191919?logo=anthropic&logoColor=white)](https://anthropic.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-UI-ff4b4b?logo=streamlit&logoColor=white)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)

[中文](#功能特性) · [English](#features)

</div>

---

## 功能特性

| 模块 | 说明 |
|------|------|
| **ReAct Agent** | 感知 → 思考 → 行动 → 观察循环，支持 Tool Use 和 Skill 路由 |
| **6 个工具** | SQL 查询、数学计算、文件读取、Python 沙箱、网络搜索、数据可视化 |
| **4 个技能** | 数据分析、SQL 专家、报告生成、文档问答 |
| **RAG 检索增强** | 文档加载 → 切片 → Embedding → 混合检索（向量 + BM25）→ 重排序 |
| **4 层记忆系统** | 短期（滑动窗口）+ 长期（向量持久化）+ 情景（交互摘要）+ 工作（任务状态） |
| **多 Agent 协作** | 编排器实现任务分解 → 子 Agent → 结果聚合 |
| **MCP 协议** | 自研 Python MCP Client/Server（JSON-RPC stdio 通信） |
| **评估体系** | 基准测试 + RAG 检索评估 + 回答质量评估 |

---

## Features

| Module | Details |
|--------|---------|
| **ReAct Agent** | Perceive → Think → Act → Observe loop with Tool Use and Skill routing |
| **6 Tools** | SQL query, math calculator, file reader, Python sandbox, web search, chart generation |
| **4 Skills** | Data analysis, SQL expert, report generation, document QA |
| **RAG Pipeline** | Document loading → Chunking → Embedding → Hybrid retrieval (Vector + BM25) → Reranking |
| **4-Layer Memory** | Short-term (sliding window) + Long-term (vector) + Episodic (summaries) + Working (task state) |
| **Multi-Agent** | Orchestrator for task decomposition → sub-agents → aggregation |
| **MCP Protocol** | Custom Python MCP Client/Server (JSON-RPC stdio) |
| **Evaluation** | Benchmarks + RAG retrieval eval + response quality eval |

---

## 技术栈 / Tech Stack

| 层级 / Layer | 技术 / Technology |
|------|------|
| LLM | Claude API (Anthropic) |
| Embedding | sentence-transformers（本地模型） |
| 向量存储 / Vector Store | 纯 Python 实现（JSON 持久化 + 余弦相似度） |
| 数据库 / Database | SQLite |
| 前端 / Frontend | Streamlit |
| MCP | 自研 Python Client/Server |

---

## 快速开始 / Getting Started

### 环境要求 / Prerequisites

- Python >= 3.11
- pip

### 安装运行 / Install & Run

```bash
# 安装依赖 / Install dependencies
pip install -r requirements.txt

# 配置环境变量 / Configure environment
cp .env.example .env
# 编辑 .env，填入 ANTHROPIC_API_KEY

# 初始化数据库 / Initialize database
make init-db

# 检查环境 / Check environment
make doctor

# 启动界面 / Start UI
make run-app
```

### 开发与测试 / Development

```bash
pip install -r requirements-dev.txt
make test    # 运行测试
make check   # lint + test
```

---

## 项目结构 / Project Structure

```
knowledge-agent/
├── config/settings.yaml       # 全局配置 / Global config
├── src/
│   ├── agent/core.py          # ReAct 循环 / ReAct loop
│   ├── tools/                 # 工具层 / Tools (6)
│   ├── skills/                # 技能层 / Skills (4)
│   ├── rag/                   # RAG 检索增强 / RAG pipeline
│   ├── memory/                # 记忆系统 / Memory system (4 types)
│   ├── multi_agent/           # 多 Agent / Multi-agent orchestration
│   ├── mcp/                   # MCP 客户端 / MCP client
│   ├── eval/                  # 评估体系 / Evaluation
│   └── finetune/              # 微调模块 / Fine-tuning
├── mcp_servers/               # MCP Server 进程 / MCP servers
├── data/
│   ├── databases/default.db   # SQLite 模拟数据 / Sample data
│   └── documents/             # 知识库文档 / Knowledge base docs
├── tests/                     # 测试 / Tests
└── app.py                     # Streamlit 主界面 / Main UI
```

---

## 核心架构 / Architecture

### Tool vs Skill

- **Tool** — 原子操作（查 SQL、读文件、算数学）/ Atomic operations
- **Skill** — 组合能力（数据分析 = 查数据 + 处理 + 可视化 + 结论）/ Composite capabilities

### RAG 流程 / RAG Pipeline

```
文档加载 → 切片 → Embedding → 向量存储 → 混合检索 → 重排序 → 上下文注入
Load → Chunk → Embed → Store → Hybrid Retrieve → Rerank → Context Injection
```

### 记忆系统 / Memory System

| 类型 / Type | 说明 / Description |
|------|------|
| 短期 / Short-term | 对话滑动窗口 / Sliding window |
| 长期 / Long-term | 向量持久化，支持 namespace 隔离 / Vector persistence with namespace isolation |
| 情景 / Episodic | 历史交互摘要 / Interaction summaries |
| 工作 / Working | 当前任务状态 / Current task state |

---

## Embedding 模型 / Models

| 值 / Value | 模型 / Model | 维度 / Dims | 适用 / Use Case |
|---|---|---|---|
| chinese | text2vec-base-chinese | 768 | 中文（默认） |
| multilingual | paraphrase-multilingual-MiniLM-L12-v2 | 384 | 多语言 |
| english | all-MiniLM-L6-v2 | 384 | 英文 |

---

## 常用命令 / Commands

| 命令 / Command | 说明 / Description |
|---|---|
| `make init-db` | 初始化数据库 / Initialize database |
| `make run-app` | 启动 Web UI / Start Streamlit UI |
| `make doctor` | 环境检查 / Check environment |
| `make test` | 运行测试 / Run tests |
| `make check` | lint + test |
| `make benchmark` | 基准测试（dry-run）/ Benchmark (dry-run) |
| `make benchmark-live` | 基准测试（真实 LLM）/ Benchmark (live LLM) |
| `make rag-eval` | RAG 检索评估 / RAG retrieval evaluation |
| `make rag-response-eval` | RAG 回答评估 / RAG response evaluation |

---

## 规划中 / Roadmap

- [ ] Web UI 升级（React 前端）
- [ ] 更多文档格式支持（DOCX、PPT）
- [ ] 在线 Demo 部署
- [ ] 多模态支持（图片理解）

---

## 参与贡献 / Contributing

详见 `CONTRIBUTING.md`。欢迎提 Issue 和 PR。

See `CONTRIBUTING.md` for details. Issues and PRs are welcome.

---

## 许可证 / License

[MIT](./LICENSE)

---

<div align="center">
<sub>通过构建学习 Agent 核心技术：Tool Use / RAG / Skills / MCP / Memory / Multi-Agent</sub>
<br>
<sub>Learn Agent fundamentals by building: Tool Use / RAG / Skills / MCP / Memory / Multi-Agent</sub>
</div>
