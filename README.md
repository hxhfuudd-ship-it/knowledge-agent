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
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 ANTHROPIC_API_KEY

# 3. 初始化数据库
python3 data/init_db.py

# 4. 启动界面
streamlit run app.py
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
├── data/
│   ├── sample.db              # SQLite 模拟数据（6 张表）
│   └── documents/             # 知识库文档
├── tests/                     # 测试文件
├── app.py                     # Streamlit 主界面
└── requirements.txt
```

## 核心模块说明

### Agent 核心（ReAct 循环）
感知 → 思考 → 行动 → 观察，循环直到任务完成。支持 Tool Use 和 Skill 路由。

### Tool vs Skill
- Tool 是原子操作（查 SQL、读文件、算数学）
- Skill 是组合能力（数据分析 = 查数据 + 处理 + 可视化 + 结论）

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

## 配置

所有配置集中在 `config/settings.yaml`，支持环境变量覆盖（如 `AGENT_LLM_MODEL`）。
