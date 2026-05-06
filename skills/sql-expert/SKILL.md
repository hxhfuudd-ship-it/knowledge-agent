---
name: sql-expert
description: Use this skill when the user asks for database queries, table fields, SQL generation, schema understanding, joins, aggregations, or query result explanation.
version: 1.0.0
tools:
  - rag_search
  - sql_query
runtime_mapping: src/skills/sql_expert.py
---

# SQL Expert Skill

## 适用场景

当用户的问题核心是“查数据库”或“理解数据库结构”时，使用这个 Skill。

典型场景：

- 查询某张表的数据。
- 询问表结构、字段含义、字段类型。
- 把自然语言需求转换成 SQL。
- 聚合查询、分组查询、排序、TopN。
- 解释 SQL 查询结果。

## 不适用场景

不要在以下场景优先使用：

- 用户只是问业务规则定义，优先使用 `doc-qa`。
- 用户需要完整经营分析和建议，优先使用 `data-analysis`。
- 用户需要正式报告格式，优先使用 `report-generation`。

## 推荐工作流

1. 理解查询意图：要查什么、按什么维度、是否有时间范围。
2. 如果不确定 schema，先用 `rag_search` 查询数据字典。
3. 生成 SQLite 兼容 SQL。
4. 使用 `sql_query` 执行查询。
5. 解释结果，并指出查询逻辑。

## SQL 规范

- 只允许 `SELECT` 查询。
- 不生成 `INSERT`、`UPDATE`、`DELETE`、`DROP`、`ALTER`。
- 聚合查询必须正确使用 `GROUP BY`。
- 日期处理使用 SQLite 语法，例如 `strftime`。
- 查询结果可能很大时加 `LIMIT`。
- 不确定字段时先查数据字典，不要猜表结构。

## 输出要求

建议输出：

```markdown
### 查询逻辑
...

### SQL
```sql
SELECT ...
```

### 查询结果解读
...
```

要求：

- 说明用了哪些表。
- 说明关键过滤条件。
- 说明聚合口径。
- 查询失败时解释可能原因。

## 示例问题

- “orders 表有哪些字段？”
- “查询各部门平均薪资。”
- “卖得最好的前 5 个产品是什么？”
- “各城市 VIP 客户数量是多少？”

## 对应源码

- Runtime Skill：`src/skills/sql_expert.py`
- SQL Tool：`src/tools/sql_tool.py`
- 数据字典：`data/documents/data_dictionary.py`

