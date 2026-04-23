"""数据分析 Skill：组合 SQL 查询 + 计算 + 可视化，完成端到端数据分析"""
from typing import Dict, Any, List
from .base import Skill


class DataAnalysisSkill(Skill):
    name = "data_analysis"
    description = "端到端数据分析：理解需求 → 查询数据 → 计算指标 → 生成洞察"
    keywords = ["分析", "趋势", "对比", "统计", "占比", "分布", "排名", "top"]

    @property
    def system_prompt(self) -> str:
        return """你是一个专业的数据分析师。你的工作流程：

1. 理解分析需求：明确用户想分析什么
2. 查询数据：用 sql_query 获取原始数据，必要时先用 rag_search 查看表结构
3. 计算指标：用 calculator 做必要的计算
4. 生成洞察：对数据进行解读，给出有价值的发现和建议

分析原则：
- 数据说话，不要臆测
- 给出具体数字，不要模糊描述
- 发现异常要指出可能的原因
- 如果数据不足以得出结论，要明确说明"""

    @property
    def required_tools(self) -> List[str]:
        return ["sql_query", "calculator", "rag_search"]

    @property
    def output_format(self) -> str:
        return """
## 分析结果

### 数据概览
（关键数据汇总）

### 核心发现
（2-3 个主要发现）

### 建议
（基于数据的可行建议）
"""

    def build_prompt(self, user_input: str, context: Dict[str, Any] = None) -> str:
        prompt = f"请对以下需求进行数据分析：\n\n{user_input}\n"
        if context and context.get("history"):
            prompt += f"\n参考之前的分析结果：\n{context['history']}\n"
        prompt += f"\n请按以下格式输出：{self.output_format}"
        return prompt
