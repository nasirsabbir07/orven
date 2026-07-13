import typer

from orven.config import ConfigLoadError, load_config
from orven.providers import ProviderError, create_provider

app = typer.Typer(help="Inspect and manage model providers.")


@app.command("list")
def list_providers() -> None:
    """List configured model providers."""
    try:
        loaded_config = load_config()
    except ConfigLoadError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error

    provider = loaded_config.settings.provider
    typer.echo(f"Configured provider: {provider.name}")
    typer.echo(f"Base URL: {provider.base_url}")
    typer.echo(f"Model: {provider.model or '(not set)'}")

    try:
        runtime_provider = create_provider(provider)
        models = runtime_provider.list_models()
    except ProviderError as error:
        typer.echo(f"Available models: unavailable ({error})")
        return

    if not models:
        typer.echo("Available models: none")
        return

    typer.echo("Available models:")
    for model in models:
        marker = " (selected)" if model.name == provider.model else ""
        typer.echo(f"- {model.name}{marker}")
