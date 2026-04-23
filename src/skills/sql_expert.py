"""SQL 专家 Skill：自然语言 → 优化 SQL → 解释 → 执行"""
from typing import Dict, Any, List
from .base import Skill


class SQLExpertSkill(Skill):
    name = "sql_expert"
    description = "SQL 专家：理解自然语言查询意图，生成优化的 SQL，解释查询逻辑"
    keywords = ["查询", "sql", "SQL", "数据库", "表"]

    @property
    def system_prompt(self) -> str:
        return """你是一个 SQL 专家。你的工作流程：

1. 理解用户的查询意图
2. 用 rag_search 查看相关表结构和业务规则
3. 生成准确的 SQL 查询
4. 用 sql_query 执行查询
5. 解释查询结果

SQL 原则：
- 只用 SELECT，禁止修改数据
- 优先使用 JOIN 而非子查询（可读性更好）
- 大数据量时注意加 LIMIT
- 日期处理用 strftime（SQLite 语法）
- 聚合查询要注意 GROUP BY 的正确性"""

    @property
    def required_tools(self) -> List[str]:
        return ["sql_query", "rag_search"]

    def build_prompt(self, user_input: str, context: Dict[str, Any] = None) -> str:
        prompt = f"用户查询需求：{user_input}\n\n"
        prompt += "请先查看相关表结构，然后生成并执行 SQL 查询，最后解释结果。"
        return prompt
