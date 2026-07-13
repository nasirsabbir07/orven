from pathlib import Path

import pytest

from orven.config import (
    ConfigLoadError,
    default_config_path,
    load_config,
    set_provider_model,
    set_provider_name,
)


def test_missing_config_uses_defaults(tmp_path: Path) -> None:
    config_path = tmp_path / "missing.toml"

    loaded_config = load_config(config_path)

    assert loaded_config.path == config_path
    assert loaded_config.exists is False
    assert loaded_config.settings.provider.name == "ollama"
    assert loaded_config.settings.provider.base_url == "http://localhost:11434"


def test_config_file_loads_typed_values(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    skills_dir = tmp_path / "skills"
    config_path.write_text(
        "\n".join(
            [
                f'skills_dir = "{skills_dir.as_posix()}"',
                "[provider]",
                'name = "vllm"',
                'base_url = "http://localhost:8000"',
                'model = "qwen2.5-coder"',
            ]
        ),
        encoding="utf-8",
    )

    loaded_config = load_config(config_path)

    assert loaded_config.exists is True
    assert loaded_config.settings.provider.name == "vllm"
    assert loaded_config.settings.provider.base_url == "http://localhost:8000"
    assert loaded_config.settings.provider.model == "qwen2.5-coder"
    assert loaded_config.settings.skills_dir == skills_dir


def test_env_overrides_config_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        "\n".join(
            [
                "[provider]",
                'name = "ollama"',
                'base_url = "http://localhost:11434"',
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("ORVEN_PROVIDER__NAME", "vllm")
    monkeypatch.setenv("ORVEN_PROVIDER__BASE_URL", "http://localhost:8000")

    loaded_config = load_config(config_path)

    assert loaded_config.settings.provider.name == "vllm"
    assert loaded_config.settings.provider.base_url == "http://localhost:8000"


def test_invalid_config_returns_actionable_error(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text("[provider\n", encoding="utf-8")

    with pytest.raises(ConfigLoadError, match="Invalid Orven config"):
        load_config(config_path)


def test_default_config_path_uses_orven_config_file() -> None:
    assert default_config_path().name == "config.toml"
    assert "orven" in str(default_config_path()).lower()


def test_set_provider_model_writes_config(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"

    loaded_config = set_provider_model("llama3:8b", config_path)

    assert loaded_config.settings.provider.model == "llama3:8b"
    assert 'model = "llama3:8b"' in config_path.read_text(encoding="utf-8")


def test_set_provider_name_writes_config(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"

    loaded_config = set_provider_name("ollama", config_path)

    assert loaded_config.settings.provider.name == "ollama"
    assert 'name = "ollama"' in config_path.read_text(encoding="utf-8")
