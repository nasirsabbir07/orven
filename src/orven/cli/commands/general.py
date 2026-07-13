import typer

from orven.cli.shell import run_shell
from orven.config import ConfigLoadError, load_config
from orven.providers import ProviderError, ProviderRequest, create_provider


def run() -> None:
    """Start an interactive Orven session."""
    run_shell()


def ask(prompt: str) -> None:
    """Send a prompt to the configured model provider."""
    try:
        loaded_config = load_config()
        provider = create_provider(loaded_config.settings.provider)
        response = provider.complete(ProviderRequest(prompt=prompt))
    except (ConfigLoadError, ProviderError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error

    typer.echo(response.text)


def hello() -> None:
    """Test command."""
    typer.echo("Hello from Orven!")


def exit() -> None:
    """Exit Orven."""
    typer.echo("Exiting Orven.")
