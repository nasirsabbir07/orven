import typer

from orven.config import ConfigLoadError, load_config
from orven.core.skills import (
    Skill,
    discover_skills,
    project_agents_skills_dir,
    project_local_skills_dir,
)

app = typer.Typer(help="Inspect local skills.")


@app.command("list")
def list_skills() -> None:
    """List discovered local skills."""
    skills = _discover()
    if not skills:
        typer.echo("No local skills are configured yet.")
        return

    for skill in skills:
        typer.echo(f"{skill.name}: {skill.description}")


@app.command("show")
def show_skill(name: str) -> None:
    """Show the full instructions for a local skill."""
    skills_by_name = {skill.name: skill for skill in _discover()}
    skill = skills_by_name.get(name)
    if skill is None:
        typer.echo(f"Unknown skill '{name}'.", err=True)
        raise typer.Exit(code=1)

    typer.echo(skill.body)


def _discover() -> list[Skill]:
    try:
        loaded_config = load_config()
    except ConfigLoadError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error

    return discover_skills(
        project_local_skills_dir(),
        project_agents_skills_dir(),
        loaded_config.settings.skills_dir,
    )
