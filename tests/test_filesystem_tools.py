import sys
from pathlib import Path

import pytest

from orven.core.tools import ToolContext
from orven.core.tools.filesystem import ListDirTool, ReadFileTool, WriteFileTool


@pytest.mark.parametrize("path", ["../outside.txt", "/etc/passwd"])
def test_read_file_refuses_paths_outside_root(tmp_path: Path, path: str) -> None:
    result = ReadFileTool().execute({"path": path}, ToolContext(root_dir=tmp_path))

    assert result.ok is False
    assert "outside the allowed directory" in result.content


def test_read_file_reads_file_within_root(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("hello")

    result = ReadFileTool().execute({"path": "a.txt"}, ToolContext(root_dir=tmp_path))

    assert result.ok is True
    assert result.content == "hello"


def test_read_file_reports_missing_file(tmp_path: Path) -> None:
    result = ReadFileTool().execute({"path": "missing.txt"}, ToolContext(root_dir=tmp_path))

    assert result.ok is False
    assert "not found" in result.content.lower()


def test_write_file_refuses_new_file_outside_root(tmp_path: Path) -> None:
    result = WriteFileTool().execute(
        {"path": "../escape.txt", "content": "x"}, ToolContext(root_dir=tmp_path)
    )

    assert result.ok is False
    assert not (tmp_path.parent / "escape.txt").exists()


def test_write_file_creates_parent_directories(tmp_path: Path) -> None:
    result = WriteFileTool().execute(
        {"path": "nested/dir/file.txt", "content": "x"}, ToolContext(root_dir=tmp_path)
    )

    assert result.ok is True
    assert (tmp_path / "nested" / "dir" / "file.txt").read_text() == "x"


def test_list_dir_lists_immediate_children(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("x")
    (tmp_path / "sub").mkdir()

    result = ListDirTool().execute({"path": "."}, ToolContext(root_dir=tmp_path))

    assert result.ok is True
    assert "f a.txt" in result.content
    assert "d sub" in result.content


def test_list_dir_refuses_paths_outside_root(tmp_path: Path) -> None:
    result = ListDirTool().execute({"path": ".."}, ToolContext(root_dir=tmp_path))

    assert result.ok is False
    assert "outside the allowed directory" in result.content


@pytest.mark.skipif(sys.platform == "win32", reason="symlink creation requires elevated privileges on Windows")
def test_read_file_follows_symlink_and_still_refuses_escape(tmp_path: Path) -> None:
    outside = tmp_path.parent / "secret.txt"
    outside.write_text("secret")
    (tmp_path / "link.txt").symlink_to(outside)

    result = ReadFileTool().execute({"path": "link.txt"}, ToolContext(root_dir=tmp_path))

    assert result.ok is False
