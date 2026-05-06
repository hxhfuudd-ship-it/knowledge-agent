"""Filesystem Agent Skills tests."""
from pathlib import Path

import yaml


SKILLS_DIR = Path(__file__).parent.parent / "skills"


def _skill_files():
    return sorted(SKILLS_DIR.glob("*/SKILL.md"))


def _frontmatter(path: Path):
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    _, raw, body = text.split("---", 2)
    return yaml.safe_load(raw), body


def test_skill_files_have_required_frontmatter():
    files = _skill_files()
    assert len(files) >= 4
    for path in files:
        meta, body = _frontmatter(path)
        assert meta.get("name")
        assert meta.get("description")
        assert meta.get("version")
        assert isinstance(meta.get("tools"), list)
        assert body.strip().startswith("# ")
    print("  OK  skill files have required frontmatter")


def test_skill_files_map_to_runtime_skills():
    runtime_paths = []
    for path in _skill_files():
        meta, _body = _frontmatter(path)
        runtime_paths.append(meta.get("runtime_mapping"))
    assert "src/skills/data_analysis.py" in runtime_paths
    assert "src/skills/sql_expert.py" in runtime_paths
    assert "src/skills/doc_qa.py" in runtime_paths
    assert "src/skills/report_gen.py" in runtime_paths
    print("  OK  skill files map to runtime skills")

