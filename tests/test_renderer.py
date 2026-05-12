"""Tests for renderer module."""

from __future__ import annotations

from pathlib import Path

import pytest

from clgen.generator import GeneratedChangelog
from clgen.renderer import (
    _select_content,
    append_to_changelog,
    render_to_file,
)


@pytest.fixture
def changelog() -> GeneratedChangelog:
    return GeneratedChangelog(
        version="1.0.0",
        date="2026-05-12",
        user_version="## What's New\n\n- Added dark mode",
        developer_version="## Features\n\n- Added `toggleTheme()` API",
        summary_version="Release 1.0.0 brings dark mode support.",
    )


class TestSelectContent:
    """Test audience content selection."""

    def test_user_audience(self, changelog: GeneratedChangelog) -> None:
        assert "dark mode" in _select_content(changelog, "user")

    def test_developer_audience(self, changelog: GeneratedChangelog) -> None:
        assert "toggleTheme" in _select_content(changelog, "developer")

    def test_summary_audience(self, changelog: GeneratedChangelog) -> None:
        assert "Release 1.0.0" in _select_content(changelog, "summary")

    def test_all_audience(self, changelog: GeneratedChangelog) -> None:
        content = _select_content(changelog, "all")
        assert "User-Facing Changelog" in content
        assert "Developer Changelog" in content
        assert "Release Summary" in content

    def test_unknown_audience(self, changelog: GeneratedChangelog) -> None:
        with pytest.raises(ValueError, match="Unknown audience"):
            _select_content(changelog, "invalid")


class TestRenderToFile:
    """Test file output."""

    def test_write_new_file(
        self, changelog: GeneratedChangelog, tmp_path: Path
    ) -> None:
        out = tmp_path / "output.md"
        render_to_file(changelog, str(out), "user")
        content = out.read_text(encoding="utf-8")
        assert "# [1.0.0] - 2026-05-12" in content
        assert "dark mode" in content

    def test_write_developer_version(
        self, changelog: GeneratedChangelog, tmp_path: Path
    ) -> None:
        out = tmp_path / "dev.md"
        render_to_file(changelog, str(out), "developer")
        content = out.read_text(encoding="utf-8")
        assert "toggleTheme" in content

    def test_write_all_version(
        self, changelog: GeneratedChangelog, tmp_path: Path
    ) -> None:
        out = tmp_path / "all.md"
        render_to_file(changelog, str(out), "all")
        content = out.read_text(encoding="utf-8")
        assert "User-Facing Changelog" in content
        assert "Developer Changelog" in content
        assert "Release Summary" in content


class TestAppendToChangelog:
    """Test CHANGELOG.md prepend mode."""

    def test_create_new_file(
        self, changelog: GeneratedChangelog, tmp_path: Path
    ) -> None:
        path = tmp_path / "CHANGELOG.md"
        append_to_changelog(changelog, str(path))
        content = path.read_text(encoding="utf-8")
        assert "# [1.0.0] - 2026-05-12" in content
        assert "dark mode" in content

    def test_prepend_to_existing(
        self, changelog: GeneratedChangelog, tmp_path: Path
    ) -> None:
        path = tmp_path / "CHANGELOG.md"
        path.write_text(
            "# Old Changelog\n\n## [0.9.0]\n\nOld stuff\n", encoding="utf-8"
        )

        append_to_changelog(changelog, str(path))
        content = path.read_text(encoding="utf-8")

        # New entry should come first
        assert content.index("1.0.0") < content.index("0.9.0")
        assert "Old stuff" in content

    def test_preserves_full_content(
        self, changelog: GeneratedChangelog, tmp_path: Path
    ) -> None:
        path = tmp_path / "CHANGELOG.md"
        existing = "# Changelog\n\n## [0.9.0]\n\n- Bug fixes\n"
        path.write_text(existing, encoding="utf-8")

        append_to_changelog(changelog, str(path))
        content = path.read_text(encoding="utf-8")

        # Existing content preserved
        assert "Bug fixes" in content
        assert "## [0.9.0]" in content
