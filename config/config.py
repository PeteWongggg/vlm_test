from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

import yaml

CONFIG_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = CONFIG_DIR / "config.yaml"


@dataclass(frozen=True)
class ModelConfig:
    name: str
    base_url: str
    api_key: str
    default_prompt: str
    allowed_mime_types: List[str]
    sampling_args: Dict[str, Any]
    extra_args: Dict[str, Any]


@dataclass(frozen=True)
class AppMeta:
    title: str
    version: str


@dataclass(frozen=True)
class AppConfig:
    model: ModelConfig
    app: AppMeta


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"配置文件不存在: {path}")
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _build_config(data: Dict[str, Any]) -> AppConfig:
    model_section = data.get("model") or {}
    app_section = data.get("app") or {}
    return AppConfig(
        model=ModelConfig(
            name=model_section.get("name", "Qwen3-VL-8B-Instruct"),
            base_url=model_section.get("base_url", "http://localhost:8500/v1"),
            api_key=model_section.get("api_key", ""),
            default_prompt=model_section.get(
                "default_prompt",
                "请根据提供的网页设计图，编写对应的HTML代码，将结果写在一个 markdown HTML 代码块中",
            ),
            allowed_mime_types=model_section.get(
                "allowed_mime_types",
                ["image/png", "image/jpeg", "image/svg+xml"],
            ),
            sampling_args=model_section.get("sampling_args", {}),
            extra_args=model_section.get("extra_args", {}),
        ),
        app=AppMeta(
            title=app_section.get("title", "Image-to-Text Demo"),
            version=app_section.get("version", "0.1.0"),
        ),
    )


@lru_cache(maxsize=1)
def load_config(path: Path | None = None) -> AppConfig:
    """Load and cache configuration from YAML file."""
    config_path = path or DEFAULT_CONFIG_PATH
    data = _load_yaml(config_path)
    return _build_config(data)

