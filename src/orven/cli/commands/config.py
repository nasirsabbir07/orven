import typer

from orven.config import ConfigLoadError, load_config


def show_config() -> None:
    """Show resolved local configuration."""
    try:
        loaded_config = load_config()
    except ConfigLoadError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error

    settings = loaded_config.settings
    typer.echo(f"Config path: {loaded_config.path}")
    typer.echo(f"Config exists: {loaded_config.exists}")
    typer.echo(f"Provider: {settings.provider.name}")
    typer.echo(f"Provider base URL: {settings.provider.base_url}")
    typer.echo(f"Provider model: {settings.provider.model or '(not set)'}")
    typer.echo(f"Skills dir: {settings.skills_dir or '(not set)'}")
    typer.echo(f"Workflows dir: {settings.workflows_dir or '(not set)'}")
