"""网络搜索工具：支持 Tavily API，回退到演示模式"""
import os
import logging
from .base import Tool, ToolPolicy

logger = logging.getLogger(__name__)


class SearchTool(Tool):
    name = "web_search"
    description = "搜索网络信息。输入关键词，返回搜索结果摘要。当知识库中找不到答案时可以尝试搜索。"
    policy = ToolPolicy(
        risk_level="medium",
        read_only=True,
        idempotent=True,
        external_access=True,
        allowed_scopes=("web", "tavily"),
        description="可能访问外部网络搜索服务；结果需防 prompt injection。",
    )
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

    def __init__(self):
        self._client = None
        self._mode = None

    def _ensure_init(self):
        if self._mode is not None:
            return
        api_key = os.environ.get("TAVILY_API_KEY", "")
        if api_key:
            try:
                from tavily import TavilyClient
                self._client = TavilyClient(api_key=api_key)
                self._mode = "tavily"
                logger.info("搜索工具使用 Tavily API")
                return
            except ImportError:
                logger.warning("tavily 未安装，pip install tavily-python")
            except Exception as e:
                logger.warning("Tavily 初始化失败: %s", e)
        self._mode = "demo"
        logger.info("搜索工具使用演示模式（设置 TAVILY_API_KEY 启用真实搜索）")

    def execute(self, query: str, max_results: int = 3) -> str:
        self._ensure_init()
        logger.info("搜索: %s (mode=%s)", query, self._mode)

        if self._mode == "tavily":
            return self._search_tavily(query, max_results)
        return self._search_demo(query)

    def _search_tavily(self, query: str, max_results: int) -> str:
        try:
            response = self._client.search(
                query=query,
                max_results=max_results,
                search_depth="basic",
            )

            results = response.get("results", [])
            if not results:
                return "未找到相关搜索结果: %s" % query

            output = []
            for i, r in enumerate(results, 1):
                title = r.get("title", "")
                url = r.get("url", "")
                content = r.get("content", "")[:300]
                output.append("[%d] %s\n    %s\n    %s" % (i, title, url, content))

            answer = response.get("answer", "")
            if answer:
                output.insert(0, "摘要: %s\n" % answer)

            return "\n\n".join(output)
        except Exception as e:
            logger.error("Tavily 搜索失败: %s", e)
            return "搜索失败: %s\n回退提示: 请尝试用 rag_search 在本地知识库中检索。" % e

    @staticmethod
    def _search_demo(query: str) -> str:
        return (
            "搜索功能为演示模式（未配置 TAVILY_API_KEY）。\n"
            "获取免费 API Key: https://tavily.com\n"
            "然后在 .env 中设置 TAVILY_API_KEY=tvly-xxxxx\n\n"
            "查询: %s\n"
            "提示: 请先尝试用 rag_search 在本地知识库中检索。" % query
        )
