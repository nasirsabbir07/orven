import typer

from orven.cli.commands import config, doctor, general, model, providers, skills, workflows
from orven.cli.shell import run_shell

app = typer.Typer(invoke_without_command=True)


@app.callback()
def main(ctx: typer.Context) -> None:
    """Orven command-line interface."""
    if ctx.invoked_subcommand is None:
        run_shell()


app.command()(general.run)
app.command()(general.ask)
app.command()(general.hello)
app.command()(general.exit)
app.command("config")(config.show_config)
app.command()(doctor.doctor)
app.add_typer(providers.app, name="providers")
app.add_typer(model.app, name="model")
app.add_typer(skills.app, name="skills")
app.add_typer(workflows.app, name="workflows")
