"""Path and identifier safety helpers."""
import re
from pathlib import Path


SQL_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
PROJECT_NAME_RE = re.compile(r"^[A-Za-z0-9_\u4e00-\u9fff]{1,64}$")


def resolve_under(base: Path, *parts) -> Path:
    base_path = base.resolve()
    candidate = base_path.joinpath(*[str(p) for p in parts]).resolve()
    try:
        candidate.relative_to(base_path)
    except ValueError as exc:
        raise ValueError("路径不合法") from exc
    return candidate


def is_sql_identifier(value: str) -> bool:
    return bool(SQL_IDENTIFIER_RE.fullmatch(value or ""))


def table_name_from_filename(filename: str) -> str:
    stem = Path(filename).stem
    name = re.sub(r"[^A-Za-z0-9_]", "_", stem)
    name = re.sub(r"_+", "_", name).strip("_")
    if not name:
        name = "csv"
    if name[0].isdigit():
        name = "table_%s" % name
    return name[:64]


def normalize_project_name(value: str) -> str:
    name = re.sub(r"[^A-Za-z0-9_\u4e00-\u9fff]", "_", (value or "").strip())
    name = re.sub(r"_+", "_", name).strip("_")[:64]
    if not name or not PROJECT_NAME_RE.fullmatch(name):
        raise ValueError("项目名只允许字母、数字、中文和下划线")
    return name
