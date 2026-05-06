---
name: report-generation
description: Use this skill when the user asks for a structured report, weekly/monthly summary, business review, executive briefing, or Markdown report based on business data and metrics.
version: 1.0.0
tools:
  - rag_search
  - sql_query
  - calculator
  - python_exec
  - create_chart
runtime_mapping: src/skills/report_gen.py
---

# Report Generation Skill

## 适用场景

当用户需要结构化报告，而不是只要一个查询结果或单个回答时，使用这个 Skill。

典型场景：

- 生成月报、周报、经营分析报告。
- 汇总多个指标并给出结论。
- 需要图表、表格、结论和建议。
- 面向汇报场景，需要结构清晰、先总后分。

## 不适用场景

不要在以下场景优先使用：

- 用户只要查一条数据，优先使用 `sql-expert`。
- 用户只问指标定义，优先使用 `doc-qa`。
- 用户只要求探索性分析，优先使用 `data-analysis`。

## 推荐工作流

1. 明确报告主题、周期、受众和范围。
2. 用 `rag_search` 确认关键指标口径。
3. 用 `sql_query` 获取核心数据。
4. 用 `calculator` 或 `python_exec` 计算同比、环比、占比等指标。
5. 需要图表时用 `create_chart`。
6. 按结构化 Markdown 输出报告。

## 报告结构

建议输出：

```markdown
# 报告标题

> 报告周期：...

## 一、核心结论
- ...

## 二、关键指标
| 指标 | 数值 | 说明 |
|---|---|---|

## 三、详细分析
### 3.1 ...

## 四、风险与建议
- ...
```

## 写作原则

- 先给结论，再给数据。
- 指标口径要准确。
- 结论必须能追溯到数据或知识库规则。
- 不要编造没有数据支持的业务判断。
- 建议要具体、可执行。

## 示例问题

- “生成一份本月销售分析报告。”
- “帮我写一份各产品类别销售情况月报。”
- “整理一份 VIP 客户经营分析汇报。”
- “输出一份包含图表和建议的经营总结。”

## 对应源码

- Runtime Skill：`src/skills/report_gen.py`
- 相关工具：`sql_query`、`rag_search`、`calculator`、`python_exec`、`create_chart`
- Demo 场景：`my_own_learning/demo_scenarios.md`

