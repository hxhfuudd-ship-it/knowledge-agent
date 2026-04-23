"""基准测试：自动化运行测试用例并生成评估报告"""
import json
import time
import yaml
from typing import List, Dict
from pathlib import Path
from .metrics import Metrics

EVAL_DIR = Path(__file__).parent


class Benchmark:
    """Agent 基准测试框架"""

    def __init__(self, agent=None):
        self.agent = agent
        self.results: List[Dict] = []

    def load_test_cases(self, path: str = None) -> List[Dict]:
        """加载测试用例"""
        if path is None:
            path = str(EVAL_DIR / "test_cases.yaml")

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data.get("test_cases", [])

    def run(self, test_cases: List[Dict] = None) -> Dict:
        """运行基准测试"""
        if test_cases is None:
            test_cases = self.load_test_cases()

        self.results = []
        passed = 0
        failed = 0

        for i, case in enumerate(test_cases):
            print(f"  [{i+1}/{len(test_cases)}] {case.get('name', 'unnamed')}...", end=" ")
            result = self._run_single(case)
            self.results.append(result)

            if result["passed"]:
                passed += 1
                print("PASS")
            else:
                failed += 1
                print(f"FAIL - {result.get('error', '')}")

        report = {
            "total": len(test_cases),
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / len(test_cases) if test_cases else 0,
            "details": self.results,
        }

        return report

    def _run_single(self, case: Dict) -> Dict:
        """运行单个测试用例"""
        query = case.get("query", "")
        expected_tools = case.get("expected_tools", [])
        expected_keywords = case.get("expected_keywords", [])
        category = case.get("category", "general")

        start = time.time()
        try:
            if self.agent:
                result = self.agent.chat(query)
                response = result["response"]
                actual_tools = [tc["tool"] for tc in result.get("tool_calls", [])]
                self.agent.reset()
            else:
                response = ""
                actual_tools = []

            latency = (time.time() - start) * 1000

            # 检查工具调用
            tool_match = all(t in actual_tools for t in expected_tools) if expected_tools else True

            # 检查关键词
            keyword_match = all(kw in response for kw in expected_keywords) if expected_keywords else True

            passed = tool_match and keyword_match

            return {
                "name": case.get("name", ""),
                "category": category,
                "query": query,
                "passed": passed,
                "tool_match": tool_match,
                "keyword_match": keyword_match,
                "actual_tools": actual_tools,
                "latency_ms": round(latency, 1),
                "response_preview": response[:200],
            }
        except Exception as e:
            return {
                "name": case.get("name", ""),
                "category": category,
                "query": query,
                "passed": False,
                "error": str(e),
                "latency_ms": (time.time() - start) * 1000,
            }

    def generate_report(self, results: Dict = None) -> str:
        """生成 Markdown 格式的评估报告"""
        if results is None:
            results = self.run()

        report = f"""# Agent 基准测试报告

## 总体结果

| 指标 | 值 |
|------|-----|
| 总用例数 | {results['total']} |
| 通过 | {results['passed']} |
| 失败 | {results['failed']} |
| 通过率 | {results['pass_rate']:.1%} |

## 详细结果

"""
        for r in results.get("details", []):
            status = "PASS" if r.get("passed") else "FAIL"
            report += f"### [{status}] {r.get('name', 'unnamed')}\n"
            report += f"- 查询: {r.get('query', '')}\n"
            report += f"- 耗时: {r.get('latency_ms', 0):.0f}ms\n"
            if r.get("actual_tools"):
                report += f"- 调用工具: {', '.join(r['actual_tools'])}\n"
            if r.get("error"):
                report += f"- 错误: {r['error']}\n"
            report += "\n"

        return report
