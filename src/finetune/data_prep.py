"""训练数据准备：从 Agent 使用日志中提取训练样本"""
import json
from typing import List, Dict
from pathlib import Path

TRAIN_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "finetune_data.jsonl"


class DataPrep:
    """将 Agent 交互日志转换为微调训练数据"""

    @staticmethod
    def from_agent_logs(logs: List[Dict]) -> List[Dict]:
        """从 Agent 日志提取 instruction-input-output 格式的训练数据"""
        samples = []
        for log in logs:
            query = log.get("query", "")
            tool_calls = log.get("tool_calls", [])
            response = log.get("response", "")

            if not query or not response:
                continue

            # 意图分类样本
            if tool_calls:
                primary_tool = tool_calls[0]["tool"]
                samples.append({
                    "instruction": "判断用户查询应该使用哪个工具",
                    "input": query,
                    "output": primary_tool,
                    "task": "intent_classification",
                })

            # SQL 生成样本
            for tc in tool_calls:
                if tc["tool"] == "sql_query":
                    samples.append({
                        "instruction": "根据用户的自然语言查询生成 SQL",
                        "input": query,
                        "output": tc["input"].get("sql", ""),
                        "task": "text_to_sql",
                    })

        return samples

    @staticmethod
    def generate_synthetic(n: int = 100) -> List[Dict]:
        """生成合成训练数据（用于冷启动）"""
        intent_samples = [
            ("各部门有多少人", "sql_query"),
            ("帮我算一下 100*200", "calculator"),
            ("复购率怎么算", "rag_search"),
            ("知识库里有什么文件", "list_files"),
            ("读一下数据字典", "read_file"),
            ("上个月销售额多少", "sql_query"),
            ("平均薪资是多少", "sql_query"),
            ("什么是GMV", "rag_search"),
            ("sqrt(144)等于多少", "calculator"),
            ("产品分类有哪些", "rag_search"),
            ("VIP客户有多少", "sql_query"),
            ("退单率怎么计算", "rag_search"),
            ("最贵的产品是什么", "sql_query"),
            ("3.14 * 10 * 10", "calculator"),
            ("订单表的字段有哪些", "rag_search"),
            ("用 Python 算一下列表的平均值", "python_exec"),
            ("帮我画个各部门人数的柱状图", "create_chart"),
            ("搜一下最新的行业报告", "web_search"),
            ("把这些数据转成 JSON 格式", "python_exec"),
            ("画个饼图看看各产品占比", "create_chart"),
        ]

        samples = []
        for query, tool in intent_samples:
            samples.append({
                "instruction": "判断用户查询应该使用哪个工具。可选工具：sql_query, calculator, rag_search, read_file, list_files, python_exec, create_chart, web_search",
                "input": query,
                "output": tool,
                "task": "intent_classification",
            })

        return samples

    @staticmethod
    def save_jsonl(samples: List[Dict], path: str = None):
        """保存为 JSONL 格式"""
        if path is None:
            path = str(TRAIN_DATA_PATH)
        with open(path, "w", encoding="utf-8") as f:
            for sample in samples:
                f.write(json.dumps(sample, ensure_ascii=False) + "\n")

    @staticmethod
    def load_jsonl(path: str = None) -> List[Dict]:
        """加载 JSONL 数据"""
        if path is None:
            path = str(TRAIN_DATA_PATH)
        samples = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    samples.append(json.loads(line))
        return samples
