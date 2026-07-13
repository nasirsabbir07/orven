import typer

from orven.config import ConfigLoadError, load_config
from orven.providers import ProviderError, create_provider


def doctor() -> None:
    """Check the local Orven environment."""
    try:
        loaded_config = load_config()
        provider = create_provider(loaded_config.settings.provider)
        provider.list_models()
    except (ConfigLoadError, ProviderError) as error:
        typer.echo("Orven doctor")
        typer.echo(f"Provider runtime: not ready ({error})")
        return

    typer.echo("Orven doctor")
    typer.echo("Provider runtime: configured")
