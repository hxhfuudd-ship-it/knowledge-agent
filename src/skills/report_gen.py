"""报告生成 Skill：收集数据 → 分析趋势 → 生成结构化报告"""
from typing import Dict, Any, List
from .base import Skill


class ReportGenSkill(Skill):
    name = "report_gen"
    description = "生成数据报告：自动收集数据、分析趋势、生成结构化的 Markdown 报告"
    keywords = ["报告", "报表", "汇报", "总结", "周报", "月报"]

    @property
    def system_prompt(self) -> str:
        return """你是一个报告撰写专家。你的工作流程：

1. 确定报告范围和时间段
2. 用 sql_query 收集所需数据
3. 用 calculator 计算关键指标
4. 用 rag_search 查找业务规则确保指标计算正确
5. 生成结构化报告

报告原则：
- 先总后分，层次清晰
- 数据准确，标注数据来源
- 同比/环比对比，突出变化
- 结尾给出总结和建议"""

    @property
    def required_tools(self) -> List[str]:
        return ["sql_query", "calculator", "rag_search"]

    @property
    def output_format(self) -> str:
        return """
# {报告标题}

> 报告周期：{时间范围}

## 一、核心指标

| 指标 | 本期 | 上期 | 变化 |
|------|------|------|------|
| ... | ... | ... | ... |

## 二、详细分析

### 2.1 {分析维度1}
（数据 + 解读）

### 2.2 {分析维度2}
（数据 + 解读）

## 三、总结与建议

- 总结1
- 总结2
- 建议
"""

    def build_prompt(self, user_input: str, context: Dict[str, Any] = None) -> str:
        prompt = f"请生成以下报告：\n\n{user_input}\n"
        prompt += f"\n请按以下格式输出：{self.output_format}"
        return prompt
