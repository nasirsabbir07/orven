import typer

app = typer.Typer(invoke_without_command=True)

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
def hello() -> None:
    """Test command."""
    typer.echo("Hello from Orven!")


@app.command()
def exit() -> None:
    """Exit Orven."""
    typer.echo("Exiting Orven.")


if __name__ == "__main__":
    app()
