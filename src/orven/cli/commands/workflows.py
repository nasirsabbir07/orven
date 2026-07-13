import typer

app = typer.Typer(help="Inspect local workflows.")


@app.command("list")
def list_workflows() -> None:
    """List discovered local workflows."""
    typer.echo("No local workflows are configured yet.")
