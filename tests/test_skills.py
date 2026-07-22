from pathlib import Path

from orven.core.skills import (
    discover_skills,
    format_skill_catalog,
    project_agents_skills_dir,
    project_local_skills_dir,
)


def _write_skill(directory: Path, folder_name: str, *, name: str, description: str, body: str) -> None:
    skill_dir = directory / folder_name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "\n".join(
            [
                "---",
                f"name: {name}",
                f"description: {description}",
                "---",
                body,
            ]
        ),
        encoding="utf-8",
    )


def test_discover_skills_returns_empty_list_for_missing_dir(tmp_path: Path) -> None:
    assert discover_skills(tmp_path / "does-not-exist") == []


def test_discover_skills_parses_frontmatter_and_body(tmp_path: Path) -> None:
    _write_skill(
        tmp_path,
        "review",
        name="code-review",
        description="Reviews code for bugs.",
        body="Check for edge cases and off-by-one errors.",
    )

    skills = discover_skills(tmp_path)

    assert len(skills) == 1
    skill = skills[0]
    assert skill.name == "code-review"
    assert skill.description == "Reviews code for bugs."
    assert skill.body == "Check for edge cases and off-by-one errors."


def test_discover_skills_skips_folders_without_skill_file(tmp_path: Path) -> None:
    (tmp_path / "not-a-skill").mkdir()
    (tmp_path / "not-a-skill" / "README.md").write_text("nothing to see here")

    assert discover_skills(tmp_path) == []


def test_discover_skills_skips_malformed_frontmatter(tmp_path: Path) -> None:
    skill_dir = tmp_path / "broken"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("no frontmatter here at all", encoding="utf-8")

    assert discover_skills(tmp_path) == []


def test_discover_skills_ignores_files_at_top_level(tmp_path: Path) -> None:
    (tmp_path / "SKILL.md").write_text("---\nname: x\n---\nbody", encoding="utf-8")

    assert discover_skills(tmp_path) == []


def test_discover_skills_first_dir_wins_on_name_collision(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    user_dir = tmp_path / "user"
    _write_skill(project_dir, "shared", name="shared", description="project version", body="a")
    _write_skill(user_dir, "shared", name="shared", description="user version", body="b")

    skills = discover_skills(project_dir, user_dir)

    assert len(skills) == 1
    assert skills[0].description == "project version"


def test_discover_skills_merges_multiple_dirs(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    user_dir = tmp_path / "user"
    _write_skill(project_dir, "one", name="one", description="d1", body="b1")
    _write_skill(user_dir, "two", name="two", description="d2", body="b2")

    skills = discover_skills(project_dir, user_dir, None)

    assert {skill.name for skill in skills} == {"one", "two"}


def test_discover_skills_finds_agents_skills_dir(tmp_path: Path) -> None:
    _write_skill(
        tmp_path / ".agents" / "skills",
        "code-review",
        name="code-review",
        description="Reviews code.",
        body="Check for bugs.",
    )

    skills = discover_skills(project_agents_skills_dir(tmp_path))

    assert len(skills) == 1
    assert skills[0].name == "code-review"


def test_discover_skills_orven_dir_wins_over_agents_dir(tmp_path: Path) -> None:
    _write_skill(
        tmp_path / ".orven" / "skills",
        "shared",
        name="shared",
        description="orven version",
        body="a",
    )
    _write_skill(
        tmp_path / ".agents" / "skills",
        "shared",
        name="shared",
        description="agents version",
        body="b",
    )

    skills = discover_skills(
        project_local_skills_dir(tmp_path), project_agents_skills_dir(tmp_path)
    )

    assert len(skills) == 1
    assert skills[0].description == "orven version"


def test_format_skill_catalog_lists_name_and_description(tmp_path: Path) -> None:
    _write_skill(tmp_path, "review", name="code-review", description="Reviews code.", body="b")
    skills = discover_skills(tmp_path)

    catalog = format_skill_catalog(skills)

    assert "code-review: Reviews code." in catalog
