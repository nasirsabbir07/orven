from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, ValidationError

from orven.providers.base import ToolDefinition

ConfirmFunc = Callable[[str], bool]


class ToolContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    root_dir: Path


class ToolResult(BaseModel):
    ok: bool
    content: str
    error: str | None = None


class BaseTool(ABC):
    name: ClassVar[str]
    description: ClassVar[str]
    args_model: ClassVar[type[BaseModel]]
    requires_confirmation: ClassVar[bool] = False

    def parameters_schema(self) -> dict[str, Any]:
        return self.args_model.model_json_schema()

    def to_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=self.parameters_schema(),
        )

    @abstractmethod
    def run(self, args: BaseModel, context: ToolContext) -> ToolResult:
        """Execute the tool with validated arguments."""

    def execute(self, raw_arguments: dict[str, Any], context: ToolContext) -> ToolResult:
        try:
            parsed = self.args_model.model_validate(raw_arguments)
        except ValidationError as error:
            return ToolResult(
                ok=False,
                content=f"Invalid arguments for '{self.name}': {error}",
                error=str(error),
            )

        return self.run(parsed, context)
