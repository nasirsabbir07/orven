from collections.abc import Iterable

from orven.core.tools.base import BaseTool
from orven.core.tools.filesystem import ListDirTool, ReadFileTool, WriteFileTool
from orven.providers.base import ToolDefinition


class ToolRegistry:
    def __init__(self, tools: Iterable[BaseTool] | None = None) -> None:
        self._tools: dict[str, BaseTool] = {}
        for tool in tools or []:
            self.register(tool)

    def register(self, tool: BaseTool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered.")
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def definitions(self) -> list[ToolDefinition]:
        return [tool.to_definition() for tool in self._tools.values()]

    def __bool__(self) -> bool:
        return bool(self._tools)


def default_tools() -> list[BaseTool]:
    """Tools enabled by default. Additional tools (e.g. run_shell) can be appended here later."""
    return [ReadFileTool(), ListDirTool(), WriteFileTool()]
