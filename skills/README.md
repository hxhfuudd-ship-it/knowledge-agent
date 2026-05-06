# Agent Skills 文件系统

这个目录把代码里的 Python Skill 映射成标准 `SKILL.md` 文件，方便学习、面试讲解和后续向可移植 Agent Skills 规范演进。

## 为什么要有这个目录

项目中已经有 `src/skills/`：

- 负责运行时 Skill 路由。
- 用 Python 类定义 `name`、`description`、`system_prompt`、`required_tools`。
- Agent 在对话时根据用户问题选择合适 Skill。

这个 `skills/` 目录负责：

- 用文件系统方式表达 Skill。
- 让每个 Skill 的用途、触发条件、推荐工具和流程更清晰。
- 对齐常见 Agent Skills 的组织方式：每个 Skill 一个目录，每个目录至少有一个 `SKILL.md`。

## 当前 Skills

| Skill | 运行时代码 | 文件系统说明 |
|---|---|---|
| data-analysis | `src/skills/data_analysis.py` | `skills/data-analysis/SKILL.md` |
| sql-expert | `src/skills/sql_expert.py` | `skills/sql-expert/SKILL.md` |
| doc-qa | `src/skills/doc-qa.py` | `skills/doc-qa/SKILL.md` |
| report-generation | `src/skills/report_gen.py` | `skills/report-generation/SKILL.md` |

## 标准结构

```text
skills/
├── README.md
├── data-analysis/
│   └── SKILL.md
├── sql-expert/
│   └── SKILL.md
├── doc-qa/
│   └── SKILL.md
└── report-generation/
    └── SKILL.md
```

## `SKILL.md` 约定

每个 `SKILL.md` 都包含：

- YAML frontmatter：`name`、`description`、`version`、`tools`
- 适用场景
- 不适用场景
- 推荐工作流
- 工具使用规范
- 输出要求
- 示例问题
- 对应源码

## 和 `src/skills/` 的关系

目前这个目录是“标准说明层”，`src/skills/` 是“运行时执行层”。

后续可以继续增强：

1. 让 `SkillRegistry` 自动读取这些 `SKILL.md` 元数据。
2. 把 `description` 和 `tools` 用于运行时路由。
3. 把每个 Skill 的 workflow 注入 Agent prompt。

