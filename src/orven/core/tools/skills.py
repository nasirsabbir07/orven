from pydantic import BaseModel, Field

from orven.core.skills import Skill
from orven.core.tools.base import BaseTool, ToolContext, ToolResult


class LoadSkillArgs(BaseModel):
    name: str = Field(description="Name of the skill to load, as shown in the skills catalog.")


class LoadSkillTool(BaseTool):
    name = "load_skill"
    description = "Load the full instructions for a named local skill."
    args_model = LoadSkillArgs

    def __init__(self, skills: list[Skill] | None = None) -> None:
        self._skills = {skill.name: skill for skill in skills or []}

    def run(self, args: BaseModel, context: ToolContext) -> ToolResult:
        assert isinstance(args, LoadSkillArgs)
        skill = self._skills.get(args.name)
        if skill is None:
            available = ", ".join(sorted(self._skills)) or "(none)"
            return ToolResult(
                ok=False,
                content=f"Unknown skill '{args.name}'. Available skills: {available}",
            )

        return ToolResult(ok=True, content=skill.body)
