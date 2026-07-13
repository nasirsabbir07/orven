from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any

from platformdirs import user_config_path
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

APP_NAME = "orven"
CONFIG_FILE_NAME = "config.toml"
ENV_PREFIX = "ORVEN_"


class ConfigLoadError(Exception):
    """Raised when the local configuration cannot be loaded."""


class ProviderSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = "ollama"
    base_url: str = "http://localhost:11434"
    model: str | None = None


class OrvenSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix=ENV_PREFIX,
        env_nested_delimiter="__",
        extra="forbid",
    )

    provider: ProviderSettings = Field(default_factory=ProviderSettings)
    skills_dir: Path | None = None
    workflows_dir: Path | None = None


class LoadedConfig(BaseModel):
    path: Path
    exists: bool
    settings: OrvenSettings


def default_config_path() -> Path:
    return user_config_path(APP_NAME, appauthor=False) / CONFIG_FILE_NAME


def load_config(config_path: Path | None = None) -> LoadedConfig:
    path = config_path or default_config_path()
    raw_config = _read_config_file(path)
    merged_config = _with_env_overrides(raw_config)

    try:
        settings = OrvenSettings.model_validate(merged_config)
    except ValidationError as error:
        raise ConfigLoadError(_format_validation_error(path, error)) from error

    return LoadedConfig(path=path, exists=path.exists(), settings=settings)


def set_provider_model(model: str, config_path: Path | None = None) -> LoadedConfig:
    path = config_path or default_config_path()
    raw_config = _read_config_file(path)
    provider_config = raw_config.setdefault("provider", {})
    if not isinstance(provider_config, dict):
        raise ConfigLoadError(f"Invalid Orven config at {path}: provider must be a TOML table.")

    provider_config["model"] = model
    _write_config_file(path, raw_config)
    return load_config(path)


def set_provider_name(name: str, config_path: Path | None = None) -> LoadedConfig:
    path = config_path or default_config_path()
    raw_config = _read_config_file(path)
    provider_config = raw_config.setdefault("provider", {})
    if not isinstance(provider_config, dict):
        raise ConfigLoadError(f"Invalid Orven config at {path}: provider must be a TOML table.")

    provider_config["name"] = name
    _write_config_file(path, raw_config)
    return load_config(path)


def _read_config_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    try:
        with path.open("rb") as config_file:
            data = tomllib.load(config_file)
    except tomllib.TOMLDecodeError as error:
        raise ConfigLoadError(f"Invalid Orven config at {path}: {error}") from error

    if not isinstance(data, dict):
        raise ConfigLoadError(f"Invalid Orven config at {path}: expected a TOML table.")

    return data


def _write_config_file(path: Path, config: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_to_toml(config), encoding="utf-8")


def _to_toml(config: dict[str, Any]) -> str:
    lines: list[str] = []
    scalar_items = {key: value for key, value in config.items() if not isinstance(value, dict)}
    table_items = {key: value for key, value in config.items() if isinstance(value, dict)}

    for key, value in scalar_items.items():
        lines.append(f"{key} = {_format_toml_value(value)}")

    for table_name, table in table_items.items():
        if lines:
            lines.append("")
        lines.append(f"[{table_name}]")
        for key, value in table.items():
            lines.append(f"{key} = {_format_toml_value(value)}")

    return "\n".join(lines) + "\n"


def _format_toml_value(value: Any) -> str:
    if isinstance(value, str):
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if isinstance(value, Path):
        return _format_toml_value(str(value))
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return '""'
    return str(value)


def _with_env_overrides(config: dict[str, Any]) -> dict[str, Any]:
    merged = dict(config)

    _set_path_value(merged, ("provider", "name"), os.getenv(f"{ENV_PREFIX}PROVIDER__NAME"))
    _set_path_value(
        merged,
        ("provider", "base_url"),
        os.getenv(f"{ENV_PREFIX}PROVIDER__BASE_URL"),
    )
    _set_path_value(merged, ("provider", "model"), os.getenv(f"{ENV_PREFIX}PROVIDER__MODEL"))
    _set_path_value(merged, ("skills_dir",), os.getenv(f"{ENV_PREFIX}SKILLS_DIR"))
    _set_path_value(merged, ("workflows_dir",), os.getenv(f"{ENV_PREFIX}WORKFLOWS_DIR"))

    return merged


def _set_path_value(config: dict[str, Any], keys: tuple[str, ...], value: str | None) -> None:
    if value is None:
        return

    current = config
    for key in keys[:-1]:
        nested = current.setdefault(key, {})
        if not isinstance(nested, dict):
            nested = {}
            current[key] = nested
        current = nested

    current[keys[-1]] = value


def _format_validation_error(path: Path, error: ValidationError) -> str:
    messages = []
    for issue in error.errors():
        location = ".".join(str(part) for part in issue["loc"])
        messages.append(f"{location}: {issue['msg']}")

    return f"Invalid Orven config at {path}: " + "; ".join(messages)
