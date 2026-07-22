from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from pydantic import BaseModel

SKILL_FILE_NAME = "SKILL.md"
PROJECT_SKILLS_DIR_NAME = Path(".orven") / "skills"


class Skill(BaseModel):
    name: str
    description: str
    body: str
    path: Path


def project_local_skills_dir(root: Path | None = None) -> Path:
    return (root or Path.cwd()) / PROJECT_SKILLS_DIR_NAME


def discover_skills(*dirs: Path | None) -> list[Skill]:
    """Discover skills across directories, first match wins on name collision."""
    found: dict[str, Skill] = {}
    for directory in dirs:
        if directory is None:
            continue
        for skill in _discover_in_dir(directory):
            found.setdefault(skill.name, skill)

    return list(found.values())


def format_skill_catalog(skills: Iterable[Skill]) -> str:
    lines = [
        "Available local skills (call load_skill with the exact name to see full instructions):"
    ]
    lines.extend(f"- {skill.name}: {skill.description}" for skill in skills)
    return "\n".join(lines)


def _discover_in_dir(directory: Path) -> list[Skill]:
    if not directory.is_dir():
        return []

    skills: list[Skill] = []
    for entry in sorted(directory.iterdir()):
        if not entry.is_dir():
            continue
        skill_file = entry / SKILL_FILE_NAME
        if not skill_file.is_file():
            continue
        skill = _parse_skill_file(skill_file)
        if skill is not None:
            skills.append(skill)

    return skills


def _parse_skill_file(path: Path) -> Skill | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None

    frontmatter, body = _split_frontmatter(text)
    if frontmatter is None:
        return None

    name = frontmatter.get("name")
    if not name:
        return None

    return Skill(
        name=name,
        description=frontmatter.get("description", ""),
        body=body.strip(),
        path=path,
    )


def _split_frontmatter(text: str) -> tuple[dict[str, str] | None, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text

    fields: dict[str, str] = {}
    end_index: int | None = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = index
            break
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip().strip('"').strip("'")

    if end_index is None:
        return None, text

    body = "\n".join(lines[end_index + 1 :])
    return fields, body
