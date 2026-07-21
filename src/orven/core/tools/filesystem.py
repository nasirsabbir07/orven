from pathlib import Path

from pydantic import BaseModel, Field

from orven.core.tools.base import BaseTool, ToolContext, ToolResult

MAX_READ_BYTES = 200_000
MAX_LIST_ENTRIES = 500


def _resolve_safe_path(raw_path: str, root_dir: Path) -> Path | None:
    try:
        candidate = Path(raw_path)
        candidate = candidate if candidate.is_absolute() else root_dir / candidate
        resolved = candidate.resolve()
        root_resolved = root_dir.resolve()
    except (OSError, ValueError):
        return None

    if not resolved.is_relative_to(root_resolved):
        return None

    return resolved


class ReadFileArgs(BaseModel):
    path: str = Field(description="Path to the file to read, relative to the working directory.")


class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Read the text content of a file within the working directory."
    args_model = ReadFileArgs

    def run(self, args: BaseModel, context: ToolContext) -> ToolResult:
        assert isinstance(args, ReadFileArgs)
        resolved = _resolve_safe_path(args.path, context.root_dir)
        if resolved is None:
            return ToolResult(
                ok=False,
                content=f"Refused to read '{args.path}': path is outside the allowed directory.",
            )

        if not resolved.exists():
            return ToolResult(ok=False, content=f"File not found: {args.path}")

        if not resolved.is_file():
            return ToolResult(ok=False, content=f"Not a file: {args.path}")

        try:
            data = resolved.read_bytes()
        except OSError as error:
            return ToolResult(ok=False, content=f"Could not read '{args.path}': {error}")

        truncated = len(data) > MAX_READ_BYTES
        text = data[:MAX_READ_BYTES].decode("utf-8", errors="replace")
        if truncated:
            text += "\n... [truncated]"

        return ToolResult(ok=True, content=text)


class ListDirArgs(BaseModel):
    path: str = Field(
        default=".",
        description="Directory to list, relative to the working directory.",
    )


class ListDirTool(BaseTool):
    name = "list_dir"
    description = "List the immediate contents of a directory within the working directory."
    args_model = ListDirArgs

    def run(self, args: BaseModel, context: ToolContext) -> ToolResult:
        assert isinstance(args, ListDirArgs)
        resolved = _resolve_safe_path(args.path, context.root_dir)
        if resolved is None:
            return ToolResult(
                ok=False,
                content=f"Refused to list '{args.path}': path is outside the allowed directory.",
            )

        if not resolved.exists():
            return ToolResult(ok=False, content=f"Directory not found: {args.path}")

        if not resolved.is_dir():
            return ToolResult(ok=False, content=f"Not a directory: {args.path}")

        try:
            entries = list(resolved.iterdir())
        except OSError as error:
            return ToolResult(ok=False, content=f"Could not list '{args.path}': {error}")

        entries.sort(key=lambda entry: (not entry.is_dir(), entry.name))
        truncated = len(entries) > MAX_LIST_ENTRIES
        entries = entries[:MAX_LIST_ENTRIES]

        lines = [f"{'d' if entry.is_dir() else 'f'} {entry.name}" for entry in entries]
        if truncated:
            lines.append("... [truncated]")

        return ToolResult(ok=True, content="\n".join(lines) if lines else "(empty directory)")


class WriteFileArgs(BaseModel):
    path: str = Field(description="Path to the file to write, relative to the working directory.")
    content: str = Field(description="Text content to write to the file.")


class WriteFileTool(BaseTool):
    name = "write_file"
    description = "Write text content to a file within the working directory, creating it if needed."
    args_model = WriteFileArgs
    requires_confirmation = True

    def run(self, args: BaseModel, context: ToolContext) -> ToolResult:
        assert isinstance(args, WriteFileArgs)
        resolved = _resolve_safe_path(args.path, context.root_dir)
        if resolved is None:
            return ToolResult(
                ok=False,
                content=f"Refused to write '{args.path}': path is outside the allowed directory.",
            )

        try:
            resolved.parent.mkdir(parents=True, exist_ok=True)
            resolved.write_text(args.content, encoding="utf-8")
        except OSError as error:
            return ToolResult(ok=False, content=f"Could not write '{args.path}': {error}")

        return ToolResult(ok=True, content=f"Wrote {len(args.content)} characters to {args.path}")
