<div align="center">

# Knowledge Agent

**个人知识库数据 Agent — 系统学习 Agent 开发核心技术栈**

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
| **ReAct Agent** | 感知 → 思考 → 行动 → 观察循环，支持工具调用和技能路由 |
| **6 个工具** | SQL 查询、数学计算、文件读取、Python 沙箱、网络搜索、数据可视化 |
| **4 个技能** | 数据分析、SQL 专家、报告生成、文档问答 |
| **RAG 检索增强** | 文档加载 → 切片 → 向量化 → 混合检索（向量 + BM25）→ 重排序 |
| **4 层记忆系统** | 短期（滑动窗口）+ 长期（向量持久化）+ 情景（交互摘要）+ 工作（任务状态） |
| **多 Agent 协作** | 编排器实现任务分解 → 子 Agent → 结果聚合 |
| **MCP 协议** | 自研 Python MCP 客户端/服务端（JSON-RPC stdio 通信） |
| **评估体系** | 基准测试 + RAG 检索评估 + 回答质量评估 |

## 技术栈

| 层级 | 技术 |
|------|------|
| 大语言模型 | Claude API（Anthropic） |
| 向量化 | sentence-transformers（本地模型） |
| 向量存储 | 纯 Python 实现（JSON 持久化 + 余弦相似度） |
| 数据库 | SQLite |
| 前端 | Streamlit |
| MCP | 自研 Python 客户端/服务端 |

## 快速开始

### 环境要求

- Python >= 3.11
- pip

### 安装运行

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入 ANTHROPIC_API_KEY

# 初始化数据库
make init-db

# 检查环境
make doctor

# 启动界面
make run-app
```

### 开发与测试

```bash
pip install -r requirements-dev.txt
make test    # 运行测试
make check   # 代码检查 + 测试
```

## 核心架构

### 工具与技能

- **工具** — 原子操作（查 SQL、读文件、算数学）
- **技能** — 组合能力（数据分析 = 查数据 + 处理 + 可视化 + 结论）

### RAG 流程

```
文档加载 → 切片 → 向量化 → 向量存储 → 混合检索 → 重排序 → 上下文注入
```

### 记忆系统

| 类型 | 说明 |
|------|------|
| 短期 | 对话滑动窗口 |
| 长期 | 向量持久化，支持命名空间隔离 |
| 情景 | 历史交互摘要 |
| 工作 | 当前任务状态 |

## 向量化模型

| 配置值 | 模型 | 维度 | 适用场景 |
|---|---|---|---|
| chinese | text2vec-base-chinese | 768 | 中文（默认） |
| multilingual | paraphrase-multilingual-MiniLM-L12-v2 | 384 | 多语言 |
| english | all-MiniLM-L6-v2 | 384 | 英文 |

## 常用命令

| 命令 | 说明 |
|---|---|
| `make init-db` | 初始化数据库 |
| `make run-app` | 启动界面 |
| `make doctor` | 环境检查 |
| `make test` | 运行测试 |
| `make check` | 代码检查 + 测试 |
| `make benchmark` | 基准测试（模拟运行） |
| `make benchmark-live` | 基准测试（真实调用） |
| `make rag-eval` | RAG 检索评估 |
| `make rag-response-eval` | RAG 回答评估 |

## 项目结构

```
knowledge-agent/
├── config/settings.yaml       # 全局配置
├── src/
│   ├── agent/core.py          # ReAct 循环
│   ├── tools/                 # 工具层（6 个）
│   ├── skills/                # 技能层（4 个）
│   ├── rag/                   # RAG 检索增强
│   ├── memory/                # 记忆系统（4 种）
│   ├── multi_agent/           # 多 Agent 协作
│   ├── mcp/                   # MCP 客户端
│   ├── eval/                  # 评估体系
│   └── finetune/              # 微调模块
├── mcp_servers/               # MCP 服务端进程
├── data/
│   ├── databases/default.db   # SQLite 模拟数据
│   └── documents/             # 知识库文档
├── tests/                     # 测试文件
└── app.py                     # Streamlit 主界面
```

## 规划中

- [ ] Web UI 升级（React 前端）
- [ ] 更多文档格式支持（DOCX、PPT）
- [ ] 在线演示部署
- [ ] 多模态支持（图片理解）

## 参与贡献

详见 `CONTRIBUTING.md`。欢迎提 Issue 和 PR。

---

## Features

| Module | Details |
|--------|---------|
| **ReAct Agent** | Perceive → Think → Act → Observe loop with tool use and skill routing |
| **6 Tools** | SQL query, math calculator, file reader, Python sandbox, web search, chart generation |
| **4 Skills** | Data analysis, SQL expert, report generation, document QA |
| **RAG Pipeline** | Document loading → Chunking → Embedding → Hybrid retrieval (Vector + BM25) → Reranking |
| **4-Layer Memory** | Short-term (sliding window) + Long-term (vector) + Episodic (summaries) + Working (task state) |
| **Multi-Agent** | Orchestrator for task decomposition → sub-agents → aggregation |
| **MCP Protocol** | Custom Python MCP Client/Server (JSON-RPC stdio) |
| **Evaluation** | Benchmarks + RAG retrieval eval + response quality eval |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM | Claude API (Anthropic) |
| Embedding | sentence-transformers (local models) |
| Vector Store | Pure Python (JSON persistence + cosine similarity) |
| Database | SQLite |
| Frontend | Streamlit |
| MCP | Custom Python Client/Server |

## Getting Started

### Prerequisites

- Python >= 3.11
- pip

### Install & Run

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env, add your ANTHROPIC_API_KEY

# Initialize database
make init-db

# Check environment
make doctor

# Start UI
make run-app
```

### Development

```bash
pip install -r requirements-dev.txt
make test    # Run tests
make check   # Lint + tests
```

## Architecture

### Tools vs Skills

- **Tool** — Atomic operations (SQL query, file read, math)
- **Skill** — Composite capabilities (data analysis = query + process + visualize + conclude)

### RAG Pipeline

```
Load → Chunk → Embed → Store → Hybrid Retrieve → Rerank → Context Injection
```

### Memory System

| Type | Description |
|------|-------------|
| Short-term | Sliding conversation window |
| Long-term | Vector persistence with namespace isolation |
| Episodic | Interaction summaries |
| Working | Current task state |

## Embedding Models

| Value | Model | Dims | Use Case |
|---|---|---|---|
| chinese | text2vec-base-chinese | 768 | Chinese (default) |
| multilingual | paraphrase-multilingual-MiniLM-L12-v2 | 384 | Multilingual |
| english | all-MiniLM-L6-v2 | 384 | English |

## Commands

| Command | Description |
|---|---|
| `make init-db` | Initialize database |
| `make run-app` | Start Streamlit UI |
| `make doctor` | Check environment |
| `make test` | Run tests |
| `make check` | Lint + tests |
| `make benchmark` | Benchmark (dry-run) |
| `make benchmark-live` | Benchmark (live LLM) |
| `make rag-eval` | RAG retrieval evaluation |
| `make rag-response-eval` | RAG response evaluation |

## Project Structure

```
knowledge-agent/
├── config/settings.yaml       # Global config
├── src/
│   ├── agent/core.py          # ReAct loop
│   ├── tools/                 # Tools (6)
│   ├── skills/                # Skills (4)
│   ├── rag/                   # RAG pipeline
│   ├── memory/                # Memory system (4 types)
│   ├── multi_agent/           # Multi-agent orchestration
│   ├── mcp/                   # MCP client
│   ├── eval/                  # Evaluation
│   └── finetune/              # Fine-tuning
├── mcp_servers/               # MCP server processes
├── data/
│   ├── databases/default.db   # SQLite sample data
│   └── documents/             # Knowledge base documents
├── tests/                     # Test files
└── app.py                     # Streamlit main UI
```

## Roadmap

- [ ] Web UI upgrade (React frontend)
- [ ] More document formats (DOCX, PPT)
- [ ] Online demo deployment
- [ ] Multimodal support (image understanding)

## Contributing

See `CONTRIBUTING.md` for details. Issues and PRs are welcome.

---

## License

[MIT](./LICENSE)

---

<div align="center">
<sub>通过构建学习 Agent 核心技术：Tool Use / RAG / Skills / MCP / Memory / Multi-Agent</sub>
<br>
<sub>Learn Agent fundamentals by building: Tool Use / RAG / Skills / MCP / Memory / Multi-Agent</sub>
</div>
