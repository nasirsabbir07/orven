import typer

from orven.config import ConfigLoadError, load_config, set_provider_model
from orven.providers import ProviderError, create_provider

app = typer.Typer(help="Inspect and select local models.")


@app.command("list")
def list_models() -> None:
    """List models available from the configured provider."""
    try:
        loaded_config = load_config()
        provider = create_provider(loaded_config.settings.provider)
        models = provider.list_models()
    except (ConfigLoadError, ProviderError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error

    selected_model = loaded_config.settings.provider.model
    if not models:
        typer.echo("No models found.")
        return

    for model in models:
        marker = " (selected)" if model.name == selected_model else ""
        typer.echo(f"{model.name}{marker}")


@app.command("current")
def current_model() -> None:
    """Show the currently selected model."""
    try:
        loaded_config = load_config()
        provider = create_provider(loaded_config.settings.provider)
        selected_model = loaded_config.settings.provider.model
        if selected_model is None:
            models = provider.list_models()
            selected_model = models[0].name if models else None
    except (ConfigLoadError, ProviderError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error

    typer.echo(f"Current model: {selected_model or '(not set)'}")


@app.command("set")
def set_model(model: str) -> None:
    """Select the model Orven should use."""
    try:
        loaded_config = load_config()
        provider = create_provider(loaded_config.settings.provider)
        available_models = {model_info.name for model_info in provider.list_models()}
        if model not in available_models:
            typer.echo(f"Model '{model}' is not available locally.", err=True)
            raise typer.Exit(code=1)

        updated_config = set_provider_model(model, loaded_config.path)
    except (ConfigLoadError, ProviderError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error

    typer.echo(f"Selected model: {updated_config.settings.provider.model}")
    typer.echo(f"Config path: {updated_config.path}")
