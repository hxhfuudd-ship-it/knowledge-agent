"""全局配置加载器：从 settings.yaml 读取配置，支持环境变量覆盖"""
import os
import yaml
from pathlib import Path
from typing import Any

CONFIG_PATH = Path(__file__).parent.parent / "config" / "settings.yaml"

_config = None


def load_config(path: str = None) -> dict:
    """加载 YAML 配置文件"""
    global _config
    if _config is not None and path is None:
        return _config

    config_path = Path(path) if path else CONFIG_PATH
    if not config_path.exists():
        _config = _default_config()
        return _config

    with open(config_path, "r", encoding="utf-8") as f:
        _config = yaml.safe_load(f) or {}

    _apply_env_overrides(_config)
    return _config


def get(key: str, default: Any = None) -> Any:
    """点号分隔的 key 访问，如 get('llm.model')"""
    config = load_config()
    keys = key.split(".")
    val = config
    for k in keys:
        if isinstance(val, dict):
            val = val.get(k)
        else:
            return default
        if val is None:
            return default
    return val


def set(key: str, value: Any):
    """运行时修改配置（仅内存，不写文件）"""
    config = load_config()
    keys = key.split(".")
    target = config
    for k in keys[:-1]:
        target = target.setdefault(k, {})
    target[keys[-1]] = value


def _apply_env_overrides(config: dict):
    """环境变量覆盖：AGENT_LLM_MODEL -> config['llm']['model']"""
    env_map = {
        "AGENT_LLM_PROVIDER": ("llm", "provider"),
        "AGENT_LLM_MODEL": ("llm", "model"),
        "AGENT_LLM_MAX_TOKENS": ("llm", "max_tokens"),
        "AGENT_LLM_BASE_URL": ("llm", "base_url"),
        "AGENT_LLM_API_KEY_ENV": ("llm", "api_key_env"),
        "AGENT_DB_PATH": ("database", "path"),
        "AGENT_RAG_CHUNK_SIZE": ("rag", "chunk_size"),
        "AGENT_RAG_TOP_K": ("rag", "top_k"),
        "AGENT_MAX_ITERATIONS": ("agent", "max_iterations"),
    }
    for env_key, path in env_map.items():
        val = os.environ.get(env_key)
        if val is not None:
            section = config.setdefault(path[0], {})
            try:
                section[path[1]] = int(val)
            except ValueError:
                section[path[1]] = val


def _default_config() -> dict:
    return {
        "llm": {"model": "claude-sonnet-4-20250514", "max_tokens": 4096, "temperature": 0},
        "database": {"path": "data/databases/default.db"},
        "rag": {"chunk_size": 512, "chunk_overlap": 50, "collection_name": "knowledge_base", "top_k": 5},
        "memory": {"short_term_max_messages": 20, "long_term_collection": "long_term_memory"},
        "agent": {"max_iterations": 10, "strategy": "react"},
    }


def reload():
    """强制重新加载配置"""
    global _config
    _config = None
    return load_config()
