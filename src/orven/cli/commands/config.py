import typer

from orven.config import ConfigLoadError, LoadedConfig, load_config


def show_config() -> None:
    """Show resolved local configuration."""
    try:
        loaded_config = load_config()
    except ConfigLoadError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error

    for line in format_config(loaded_config):
        typer.echo(line)


def format_config(loaded_config: LoadedConfig) -> list[str]:
    """Return user-facing resolved configuration lines."""
    settings = loaded_config.settings
    return [
        f"Config path: {loaded_config.path}",
        f"Config exists: {loaded_config.exists}",
        f"Provider: {settings.provider.name}",
        f"Provider base URL: {settings.provider.base_url}",
        f"Provider model: {settings.provider.model or '(not set)'}",
        f"Skills dir: {settings.skills_dir or '(not set)'}",
        f"Workflows dir: {settings.workflows_dir or '(not set)'}",
    ]
