import typer

app = typer.Typer(help="Inspect local skills.")


@app.command("list")
def list_skills() -> None:
    """List discovered local skills."""
    typer.echo("No local skills are configured yet.")
