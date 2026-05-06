---
name: data-analysis
description: Use this skill when the user asks for business data analysis, trends, rankings, distributions, comparisons, metric interpretation, or insight generation from database/query results.
version: 1.0.0
tools:
  - rag_search
  - sql_query
  - calculator
  - python_exec
  - create_chart
runtime_mapping: src/skills/data_analysis.py
---

# Data Analysis Skill

## 适用场景

当用户的问题需要从业务数据中得到结论时，使用这个 Skill。

典型场景：

- 分析销售额、GMV、客单价、复购率、退单率等指标。
- 比较不同产品、部门、城市、客户等级的表现。
- 查看趋势、排名、分布、占比、异常变化。
- 根据查询结果生成业务洞察和建议。

## 不适用场景

不要在以下场景优先使用：

- 用户只问某个字段或表结构，优先使用 `sql-expert` 或 `doc-qa`。
- 用户只要求解释知识库规则，优先使用 `doc-qa`。
- 用户只要求生成正式报告，优先使用 `report-generation`。

## 推荐工作流

1. 明确分析目标：指标、维度、时间范围、筛选条件。
2. 如涉及业务指标，先用 `rag_search` 检索指标定义和业务规则。
3. 如不确定表结构，先检索数据字典。
4. 使用 `sql_query` 获取必要数据。
5. 使用 `calculator` 或 `python_exec` 做简单计算、汇总或格式转换。
6. 需要可视化时使用 `create_chart`。
7. 输出结论时区分“数据事实”和“分析推断”。

## 工具使用规范

- `rag_search`：用于确认 GMV、复购率、退单率等指标口径。
- `sql_query`：只执行安全查询，不修改数据。
- `calculator`：用于简单数学计算。
- `python_exec`：仅用于受限的数据处理或统计计算。
- `create_chart`：用于展示趋势、对比、排名、分布。

## 输出要求

建议输出结构：

```markdown
## 分析结果

### 数据概览
- ...

### 核心发现
1. ...
2. ...

### 建议
- ...
```

要求：

- 给出具体数字，不要只写模糊描述。
- 如果数据不足，要明确说明。
- 如果用了业务指标，要说明计算口径。
- 如果生成图表，要说明图表表达了什么。

## 示例问题

- “分析一下各产品类别的销售情况，哪个类别卖得最好？”
- “帮我看一下本月 GMV 和上月相比有什么变化。”
- “VIP 客户主要分布在哪些城市？”
- “画个柱状图展示各部门人数。”

## 对应源码

- Runtime Skill：`src/skills/data_analysis.py`
- 常用工具：`src/tools/sql_tool.py`、`src/tools/chart_tool.py`、`src/rag/rag_tool.py`
- 评估入口：`make harness`、`make benchmark`、`make rag-eval`

