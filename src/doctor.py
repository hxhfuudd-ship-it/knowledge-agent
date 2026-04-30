"""Environment and configuration checks for local development."""
import importlib.util
import os
import sqlite3
from pathlib import Path
from typing import List, Tuple

from dotenv import load_dotenv

from . import config

PROJECT_ROOT = Path(__file__).parent.parent
ENV_PATH = PROJECT_ROOT / ".env"

REQUIRED_PACKAGES = {
    "anthropic": "anthropic",
    "openai": "openai",
    "yaml": "pyyaml",
    "streamlit": "streamlit",
    "pandas": "pandas",
    "matplotlib": "matplotlib",
    "rank_bm25": "rank-bm25",
}


CheckResult = Tuple[str, bool, str]


def _has_module(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def check_env_file() -> CheckResult:
    if ENV_PATH.exists():
        return ("env_file", True, ".env 已存在")
    return ("env_file", False, "缺少 .env；可执行 cp .env.example .env 后填写 API Key")


def check_llm_credentials() -> CheckResult:
    load_dotenv(ENV_PATH)
    provider = config.get("llm.provider", "anthropic")
    if provider == "anthropic":
        if os.environ.get("ANTHROPIC_API_KEY"):
            return ("llm_credentials", True, "已配置 ANTHROPIC_API_KEY")
        return ("llm_credentials", False, "当前 provider=anthropic，但缺少 ANTHROPIC_API_KEY")

    if provider == "openai":
        api_key_env = config.get("llm.api_key_env", "") or "OPENAI_API_KEY"
        if os.environ.get(api_key_env):
            return ("llm_credentials", True, "已配置 %s" % api_key_env)
        return ("llm_credentials", False, "当前 provider=openai，但缺少 %s" % api_key_env)

    return ("llm_credentials", False, "未知 llm.provider: %s" % provider)


def check_database() -> CheckResult:
    db_path = PROJECT_ROOT / config.get("database.path", "data/databases/default.db")
    if not db_path.exists():
        return ("database", False, "数据库不存在: %s；可执行 python3 data/init_db.py" % db_path)

    try:
        with sqlite3.connect(str(db_path)) as conn:
            count = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
        if count == 0:
            return ("database", False, "数据库存在但没有表: %s" % db_path)
        return ("database", True, "数据库可用，包含 %d 张表" % count)
    except sqlite3.Error as e:
        return ("database", False, "数据库无法读取: %s" % e)


def check_documents() -> CheckResult:
    docs_dir = PROJECT_ROOT / "data" / "documents"
    if not docs_dir.exists():
        return ("documents", False, "知识库目录不存在: %s" % docs_dir)
    files = [f for f in docs_dir.iterdir() if f.is_file()]
    if not files:
        return ("documents", False, "知识库目录为空: %s" % docs_dir)
    return ("documents", True, "知识库文档 %d 个" % len(files))


def check_packages() -> List[CheckResult]:
    results = []
    for module_name, package_name in REQUIRED_PACKAGES.items():
        ok = _has_module(module_name)
        message = "已安装 %s" % package_name if ok else "缺少依赖 %s；执行 pip install -r requirements.txt" % package_name
        results.append(("package:%s" % package_name, ok, message))
    return results


def run_checks(include_packages: bool = True) -> List[CheckResult]:
    checks = [check_env_file(), check_llm_credentials(), check_database(), check_documents()]
    if include_packages:
        checks.extend(check_packages())
    return checks


def format_report(results: List[CheckResult]) -> str:
    lines = ["# Environment check"]
    for name, ok, message in results:
        status = "OK" if ok else "FAIL"
        lines.append("[%s] %s - %s" % (status, name, message))
    failed = sum(1 for _, ok, _ in results if not ok)
    lines.append("\nSummary: %d passed, %d failed" % (len(results) - failed, failed))
    return "\n".join(lines)


def main() -> int:
    results = run_checks(include_packages=True)
    print(format_report(results))
    return 1 if any(not ok for _, ok, _ in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
