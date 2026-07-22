from collections.abc import Callable
from pathlib import Path
import sys

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
import typer

from orven.cli.commands.config import format_config
from orven.cli.tracing import print_turn_receipt
from orven.config import ConfigLoadError, load_config, set_provider_model, set_provider_name
from orven.core import Agent, Conversation
from orven.core.skills import (
    Skill,
    discover_skills,
    project_agents_skills_dir,
    project_local_skills_dir,
)
from orven.core.tools import ToolRegistry, default_tools
from orven.providers import ModelInfo, ProviderError, create_provider

HELP_TEXT = """Commands:
  /help      Show this help
  /clear     Clear the current session view
  /config    Show resolved configuration
  /current   Show the selected model
  /provider  Select provider
  /providers List supported providers
  /models    List local models
  /model     Select a local model
  /skills    List local skills
  /skill     Show a local skill's instructions
  /exit      Exit Orven

Type a task or question and press Enter to submit it."""

SUPPORTED_PROVIDERS = ["ollama"]
SLASH_COMMANDS = [
    "/help",
    "/clear",
    "/config",
    "/current",
    "/providers",
    "/provider",
    "/models",
    "/model",
    "/skills",
    "/skill",
    "/exit",
    "/quit",
]

InputFunc = Callable[[str], str]


def run_shell(input_func: InputFunc | None = None, *, verbose: bool = False) -> None:
    """Run the interactive Orven shell."""
    typer.echo("Orven")
    typer.echo("Type a task, or /help for commands. Use /model to select a local model.")
    prompt = input_func or _default_prompt
    conversation = Conversation()
    agent: Agent | None = None

    while True:
        try:
            user_input = prompt("orven").strip()
        except (EOFError, KeyboardInterrupt):
            typer.echo()
            typer.echo("Exiting Orven.")
            return

        if user_input == "":
            continue

        command = user_input.lower()

        if command in {"/exit", "exit", "/quit", "quit"}:
            typer.echo("Exiting Orven.")
            return
        if command in {"/help", "help"}:
            typer.echo(HELP_TEXT)
            continue
        if command == "/clear":
            typer.echo("\x1b[2J\x1b[H", nl=False)
            continue
        if command == "/config":
            _show_config()
            continue
        if command == "/current":
            _show_current_model()
            continue
        if command == "/providers":
            _show_providers()
            continue
        if command == "/provider":
            _select_provider(prompt)
            agent = None
            continue
        if command == "/models":
            _show_models()
            continue
        if command == "/model":
            _select_model(prompt)
            agent = None
            continue
        if command == "/skills":
            _show_skills()
            continue
        if command == "/skill":
            _show_skill(prompt)
            continue
        if command == "hello":
            typer.echo("Hello from Orven!")
            continue

        if agent is None:
            try:
                agent = _build_agent(conversation, verbose=verbose)
            except (ConfigLoadError, ProviderError) as error:
                typer.echo(str(error))
                continue

        _send_prompt(agent, user_input)


def _default_prompt(message: str) -> str:
    if sys.stdin.isatty():
        session: PromptSession[str] = PromptSession(
            completer=WordCompleter(SLASH_COMMANDS, ignore_case=True)
        )
        return session.prompt(f"{message}> ")

    return typer.prompt(message)


def _build_agent(conversation: Conversation, *, verbose: bool = False) -> Agent:
    loaded_config = load_config()
    provider = create_provider(loaded_config.settings.provider)
    skills = _discover_shell_skills(loaded_config.settings.skills_dir)
    return Agent(
        provider,
        conversation,
        tools=ToolRegistry(default_tools()),
        confirm=_shell_confirm,
        root_dir=Path.cwd(),
        skills=skills,
        on_turn=print_turn_receipt if verbose else None,
    )


def _shell_confirm(message: str) -> bool:
    try:
        return typer.confirm(message, default=False)
    except (typer.Abort, EOFError, KeyboardInterrupt):
        return False


def _send_prompt(agent: Agent, prompt: str) -> None:
    try:
        response = agent.respond(prompt, on_token=lambda token: typer.echo(token, nl=False))
    except KeyboardInterrupt:
        typer.echo()
        typer.echo("Cancelled.")
        return
    except ProviderError as error:
        typer.echo()
        typer.echo(str(error))
        return

    if not response.strip():
        typer.echo("(model returned an empty response)")
    typer.echo()


def _show_config() -> None:
    try:
        loaded_config = load_config()
    except ConfigLoadError as error:
        typer.echo(str(error))
        return

    for line in format_config(loaded_config):
        typer.echo(line)


def _show_current_model() -> None:
    try:
        loaded_config = load_config()
        selected_model = loaded_config.settings.provider.model
        if selected_model is None:
            models = _available_models()
            selected_model = models[0].name if models else None
    except (ConfigLoadError, ProviderError) as error:
        typer.echo(str(error))
        return

    typer.echo(f"Current model: {selected_model or '(not set)'}")


def _show_models() -> None:
    try:
        loaded_config = load_config()
        models = _available_models()
    except (ConfigLoadError, ProviderError) as error:
        typer.echo(str(error))
        return

    if not models:
        typer.echo("No models found.")
        return

    selected_model = loaded_config.settings.provider.model
    for index, model in enumerate(models, start=1):
        marker = " *" if model.name == selected_model else ""
        typer.echo(f"{index}. {model.name}{marker}")


def _show_providers() -> None:
    try:
        loaded_config = load_config()
    except ConfigLoadError as error:
        typer.echo(str(error))
        return

    selected_provider = loaded_config.settings.provider.name
    for index, provider in enumerate(SUPPORTED_PROVIDERS, start=1):
        marker = " *" if provider == selected_provider else ""
        typer.echo(f"{index}. {provider}{marker}")


def _select_provider(prompt: InputFunc) -> None:
    try:
        loaded_config = load_config()
    except ConfigLoadError as error:
        typer.echo(str(error))
        return

    selected_provider = loaded_config.settings.provider.name
    for index, provider in enumerate(SUPPORTED_PROVIDERS, start=1):
        marker = " *" if provider == selected_provider else ""
        typer.echo(f"{index}. {provider}{marker}")

    choice = prompt("select provider").strip()
    try:
        provider_index = int(choice)
    except ValueError:
        typer.echo("Selection must be a number.")
        return

    if provider_index < 1 or provider_index > len(SUPPORTED_PROVIDERS):
        typer.echo("Selection is out of range.")
        return

    selected = SUPPORTED_PROVIDERS[provider_index - 1]
    try:
        updated_config = set_provider_name(selected, loaded_config.path)
    except ConfigLoadError as error:
        typer.echo(str(error))
        return

    typer.echo(f"Selected provider: {updated_config.settings.provider.name}")


def _select_model(prompt: InputFunc) -> None:
    try:
        loaded_config = load_config()
        models = _available_models()
    except (ConfigLoadError, ProviderError) as error:
        typer.echo(str(error))
        return

    if not models:
        typer.echo("No models found.")
        return

    selected_model = loaded_config.settings.provider.model
    for index, model in enumerate(models, start=1):
        marker = " *" if model.name == selected_model else ""
        typer.echo(f"{index}. {model.name}{marker}")

    choice = prompt("select model").strip()
    try:
        model_index = int(choice)
    except ValueError:
        typer.echo("Selection must be a number.")
        return

    if model_index < 1 or model_index > len(models):
        typer.echo("Selection is out of range.")
        return

    selected = models[model_index - 1]
    try:
        updated_config = set_provider_model(selected.name, loaded_config.path)
    except ConfigLoadError as error:
        typer.echo(str(error))
        return

    typer.echo(f"Selected model: {updated_config.settings.provider.model}")


def _available_models() -> list[ModelInfo]:
    loaded_config = load_config()
    provider = create_provider(loaded_config.settings.provider)
    return provider.list_models()


def _discover_shell_skills(skills_dir: Path | None) -> list[Skill]:
    return discover_skills(project_local_skills_dir(), project_agents_skills_dir(), skills_dir)


def _show_skills() -> None:
    try:
        loaded_config = load_config()
    except ConfigLoadError as error:
        typer.echo(str(error))
        return

    skills = _discover_shell_skills(loaded_config.settings.skills_dir)
    if not skills:
        typer.echo("No local skills are configured yet.")
        return

    for skill in skills:
        typer.echo(f"{skill.name}: {skill.description}")


def _show_skill(prompt: InputFunc) -> None:
    try:
        loaded_config = load_config()
    except ConfigLoadError as error:
        typer.echo(str(error))
        return

    skills = {skill.name: skill for skill in _discover_shell_skills(loaded_config.settings.skills_dir)}
    if not skills:
        typer.echo("No local skills are configured yet.")
        return

    for name in skills:
        typer.echo(name)

    choice = prompt("skill name").strip()
    skill = skills.get(choice)
    if skill is None:
        typer.echo(f"Unknown skill '{choice}'.")
        return

    typer.echo(skill.body)
