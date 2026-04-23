"""文档问答 Skill：检索文档 → 提取信息 → 综合回答 → 标注来源"""
from typing import Dict, Any, List
from .base import Skill


class DocQASkill(Skill):
    name = "doc_qa"
    description = "文档问答：从知识库中检索相关文档，综合回答用户问题，标注信息来源"
    keywords = ["文档", "知识", "规则", "定义", "什么是", "怎么算", "如何"]

    @property
    def system_prompt(self) -> str:
        return """你是一个知识库问答助手。你的工作流程：

1. 用 rag_search 检索与问题相关的文档
2. 如果需要补充信息，用 read_file 查看完整文档
3. 综合检索到的信息回答问题
4. 标注信息来源

回答原则：
- 基于文档内容回答，不要编造
- 如果文档中没有相关信息，明确告知用户
- 引用具体的文档来源
- 回答要准确、简洁"""

    @property
    def required_tools(self) -> List[str]:
        return ["rag_search", "read_file", "list_files"]

    def build_prompt(self, user_input: str, context: Dict[str, Any] = None) -> str:
        prompt = f"用户问题：{user_input}\n\n"
        prompt += "请从知识库中检索相关信息并回答。务必标注信息来源。"
        return prompt
