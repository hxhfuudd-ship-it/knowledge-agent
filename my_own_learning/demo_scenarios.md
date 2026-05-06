# Agent Demo 场景脚本

这份文档用于准备面试或自测时的演示路线。每个 demo 都尽量体现一个标准 Agent 模块。

## Demo 前准备

```bash
pip install -r requirements-dev.txt
make init-db
make doctor
make check
make harness
make run-app
```

如果没有真实 LLM Key，也可以先讲 dry-run、测试和架构；如果要现场演示真实对话，需要配置 `.env`。

## Demo 1：RAG 业务规则问答

目标：展示 Agent 会先查知识库，而不是直接编答案。

用户问题：

> GMV 是怎么计算的？订单金额和退款要怎么处理？

期望链路：

1. Agent 判断问题涉及业务规则。
2. 调用 `rag_search`。
3. 检索业务规则文档。
4. 总结 GMV 计算方式。
5. Trace 中能看到 RAG 工具调用。

讲解重点：

- RAG 用于动态知识，不需要把所有知识写进 prompt。
- 检索结果应当有来源。
- RAG 可以降低幻觉，但不等于完全消除幻觉。

## Demo 2：SQL 数据分析

目标：展示 Tool Calling 和数据库分析能力。

用户问题：

> 查询各部门员工数量，并给出简单分析。

期望链路：

1. Agent 识别需要查数据库。
2. 必要时先查数据字典。
3. 调用 `sql_query`。
4. 返回表格结果和分析结论。
5. Trace 中能看到 SQL 工具输入和输出摘要。

讲解重点：

- LLM 不直接访问数据库，而是通过 SQL Tool。
- SQL Tool 限制只允许 SELECT。
- Tool 层负责安全校验。

## Demo 3：业务指标分析 + 图表

目标：展示多工具组合能力。

用户问题：

> 帮我分析各产品销售额，并生成一个柱状图。

期望链路：

1. Agent 使用 SQL 查询产品销售额。
2. 使用 `create_chart` 生成图表。
3. 返回图表路径和分析结论。
4. Trace 展示 SQL + Chart 两个工具。

讲解重点：

- Agent 能把多个工具串起来。
- Tool Calling 让 LLM 从“生成文本”变成“调用能力”。
- Trace 能解释 Agent 为什么得出这个结果。

## Demo 4：CSV 导入后分析

目标：展示项目管理和数据接入能力。

准备一个 CSV，例如：

```csv
date,channel,revenue
2026-04-01,search,1000
2026-04-01,social,800
2026-04-02,search,1200
```

用户问题：

> 请把这个 CSV 导入数据库，然后分析不同渠道的收入。

期望链路：

1. 上传 CSV。
2. 使用 `csv_import` 导入为表。
3. SQL Tool 动态感知新表。
4. 查询并分析不同渠道收入。

讲解重点：

- Agent 不只处理固定示例数据，也能接入用户数据。
- CSV 导入需要文件名、路径和表名校验。
- 动态 schema 对数据 Agent 很重要。

## Demo 5：Python 工具沙箱

目标：展示安全执行代码能力。

用户问题：

> 用 Python 计算 1 到 100 的平方和。

期望链路：

1. Agent 调用 `python_exec`。
2. Python 子进程执行简单代码。
3. 返回结果。

可以继续测试危险输入：

> 用 Python 读取系统环境变量。

期望结果：

- 工具应拒绝危险 import / builtin / 文件系统行为。

讲解重点：

- Python 工具是高风险工具。
- 不能在主进程直接 exec 用户代码。
- 必须有隔离、超时、输出截断和白名单限制。

## Demo 6：Trace 排查 Agent 行为

目标：展示可观测性。

操作：

1. 在 UI 提问一个需要工具的问题。
2. 展开 Trace / 性能面板。
3. 指出 LLM 调用了几次、工具调用了几次、耗时多少、是否有 token usage。

讲解重点：

- Agent 的执行不是黑盒。
- Trace 用于调试慢请求、错误工具调用和成本问题。
- 生产级 Agent 必须有可观测性。

## Demo 7：Benchmark 与 CI

目标：展示工程化能力。

命令：

```bash
make harness
make benchmark
make check
```

期望结果：

- `make harness` dry-run 通过，展示工具轨迹、trace 和校验结果。
- `make benchmark` dry-run 通过，不调用真实 LLM。
- `make check` 通过 lint 和默认测试。

讲解重点：

- Harness 负责标准化运行和收集过程。
- Agent 不能只靠手工体验验证。
- 默认测试不依赖真实 embedding 或外部网络。
- live benchmark 和默认 CI 要分开。

## 面试推荐演示顺序

如果只有 5 分钟：

1. 讲项目定位。
2. 演示 Demo 3：SQL + Chart。
3. 打开 Trace。
4. 补一句 RAG / Memory / CI 都已经实现。

如果有 10 分钟：

1. 讲架构图。
2. 演示 Demo 1：RAG。
3. 演示 Demo 3：SQL + Chart。
4. 打开 Trace。
5. 运行 `make check` 或展示 CI。

如果不能现场联网或没有 API Key：

1. 展示源码结构。
2. 运行 `make check`。
3. 运行 `make benchmark`。
4. 讲 fake LLM / fake embedding 为什么重要。

## Demo 成功标准

一次好的 Agent demo 应该展示：

- 模型不是直接回答，而是会选择工具。
- 工具调用有输入输出。
- 回答基于工具结果。
- 有 trace 可以解释过程。
- 有测试和 benchmark 保证行为可回归。
- 有安全边界说明。
