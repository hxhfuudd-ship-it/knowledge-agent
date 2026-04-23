"""网络搜索工具：模拟搜索接口（学习 API 集成模式）"""
import logging
from .base import Tool

logger = logging.getLogger(__name__)


class SearchTool(Tool):
    name = "web_search"
    description = "搜索网络信息。输入关键词，返回搜索结果摘要。当知识库中找不到答案时可以尝试搜索。"
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索关键词",
            },
            "max_results": {
                "type": "integer",
                "description": "最大返回结果数（默认 3）",
            },
        },
        "required": ["query"],
    }

    def execute(self, query: str, max_results: int = 3) -> str:
        logger.info("搜索: %s", query)
        return (
            "搜索功能为演示模式。\n"
            "实际项目中可接入以下 API：\n"
            "- Tavily Search API（推荐，专为 AI Agent 设计）\n"
            "- SerpAPI（Google 搜索代理）\n"
            "- Bing Search API\n\n"
            "查询: %s\n"
            "提示: 请先尝试用 rag_search 在本地知识库中检索。" % query
        )
