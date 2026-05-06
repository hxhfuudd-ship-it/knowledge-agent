"""Command line entry for the Agent harness."""
import argparse
import json
from pathlib import Path

from .runner import HarnessRunner, load_cases


def _to_markdown(results) -> str:
    lines = [
        "# Agent Harness Report",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---|",
        "| Total | %d |" % results["total"],
        "| Passed | %d |" % results["passed"],
        "| Failed | %d |" % results["failed"],
        "| Pass Rate | %.1f%% |" % (results["pass_rate"] * 100),
        "",
        "## Details",
        "",
    ]

    for item in results.get("details", []):
        status = "PASS" if item.get("passed") else "FAIL"
        lines.append("### [%s] %s" % (status, item.get("name", "unnamed")))
        lines.append("- Category: `%s`" % item.get("category", "general"))
        lines.append("- Mode: `%s`" % item.get("mode", "dry"))
        lines.append("- Query: %s" % item.get("query", ""))
        if item.get("tools_used"):
            lines.append("- Tools: %s" % ", ".join(item["tools_used"]))
        if item.get("checks"):
            checks = ", ".join("%s=%s" % (key, value) for key, value in item["checks"].items())
            lines.append("- Checks: %s" % checks)
        if item.get("latency_ms") is not None:
            lines.append("- Latency: %.1fms" % item.get("latency_ms", 0))
        if item.get("error"):
            lines.append("- Error: %s" % item["error"])
        if item.get("response"):
            lines.append("- Response Preview: %s" % item["response"][:200])
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run standardized Agent harness cases")
    parser.add_argument("--cases", help="Path to harness_cases.yaml")
    parser.add_argument("--output", help="Write report to this path")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--validate-only", action="store_true", help="Only validate case structure")
    parser.add_argument("--live", action="store_true", help="Run real Agent/LLM instead of scripted dry-run")
    args = parser.parse_args()

    raw_cases = load_cases(args.cases)
    runner = HarnessRunner()
    results = runner.validate_cases(raw_cases) if args.validate_only else runner.run_cases(raw_cases, live=args.live)

    content = json.dumps(results, ensure_ascii=False, indent=2) if args.format == "json" else _to_markdown(results)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        print("Harness report written to: %s" % output_path)
    else:
        print(content)

    return 0 if results.get("failed", 0) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

