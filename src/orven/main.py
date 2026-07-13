import typer

app = typer.Typer(invoke_without_command=True)
providers_app = typer.Typer(help="Inspect and manage model providers.")
skills_app = typer.Typer(help="Inspect local skills.")
workflows_app = typer.Typer(help="Inspect local workflows.")

HELP_TEXT = """Commands:
  /help      Show this help
  /clear     Clear the current session view
  /exit      Exit Orven

Type a task or question and press Enter to submit it."""


def run_shell() -> None:
    """Run the interactive Orven shell."""
    typer.echo("Orven")
    typer.echo("Type a task, or /help for commands.")

    while True:
        try:
            user_input = typer.prompt("orven").strip()
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
        if command == "hello":
            typer.echo("Hello from Orven!")
            continue

        typer.echo("Orven is ready for this task, but no model provider is configured yet.")
        typer.echo("Next step: add an Ollama or vLLM provider and route prompts through it.")


@app.callback()
def main(ctx: typer.Context) -> None:
    """Orven command-line interface."""
    if ctx.invoked_subcommand is None:
        run_shell()


@app.command()
def run() -> None:
    """Start an interactive Orven session."""
    run_shell()


@app.command()
def hello() -> None:
    """Test command."""
    typer.echo("Hello from Orven!")


@app.command()
def doctor() -> None:
    """Check the local Orven environment."""
    typer.echo("Orven doctor")
    typer.echo("Provider runtime: not configured")


@app.command()
def exit() -> None:
    """Exit Orven."""
    typer.echo("Exiting Orven.")


@providers_app.command("list")
def list_providers() -> None:
    """List configured model providers."""
    typer.echo("No model providers are configured yet.")


@skills_app.command("list")
def list_skills() -> None:
    """List discovered local skills."""
    typer.echo("No local skills are configured yet.")


@workflows_app.command("list")
def list_workflows() -> None:
    """List discovered local workflows."""
    typer.echo("No local workflows are configured yet.")


app.add_typer(providers_app, name="providers")
app.add_typer(skills_app, name="skills")
app.add_typer(workflows_app, name="workflows")

if __name__ == "__main__":
    app()
