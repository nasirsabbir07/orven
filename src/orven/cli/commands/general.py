from pathlib import Path
import sys

import typer

from orven.cli.shell import run_shell
from orven.config import ConfigLoadError, load_config
from orven.core import Agent
from orven.core.tools import ConfirmFunc, ToolRegistry, default_tools
from orven.providers import ProviderError, create_provider


def run() -> None:
    """Start an interactive Orven session."""
    run_shell()


def chat() -> None:
    """Start an interactive chat session."""
    run_shell()


def ask(
    prompt: str,
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Automatically approve tool actions that require confirmation (e.g. writing files).",
    ),
) -> None:
    """Send a prompt to the configured model provider."""
    try:
        loaded_config = load_config()
        provider = create_provider(loaded_config.settings.provider)
        agent = Agent(
            provider,
            tools=ToolRegistry(default_tools()),
            confirm=_make_ask_confirm(auto_yes=yes),
            root_dir=Path.cwd(),
        )
        agent.respond(prompt, on_token=lambda token: typer.echo(token, nl=False))
    except (ConfigLoadError, ProviderError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error
    except KeyboardInterrupt:
        typer.echo()
        typer.echo("Cancelled.", err=True)
        raise typer.Exit(code=130) from None

    typer.echo()


def _make_ask_confirm(*, auto_yes: bool) -> ConfirmFunc:
    def _confirm(message: str) -> bool:
        if auto_yes:
            return True
        if not sys.stdin.isatty():
            typer.echo(f"Refused ({message}) without --yes in non-interactive mode.", err=True)
            return False
        try:
            return typer.confirm(message, default=False)
        except (typer.Abort, EOFError, KeyboardInterrupt):
            return False

    return _confirm


def hello() -> None:
    """Test command."""
    typer.echo("Hello from Orven!")


def exit() -> None:
    """Exit Orven."""
    typer.echo("Exiting Orven.")
