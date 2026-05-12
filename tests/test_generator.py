"""Tests for generator module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from clgen.analyzer import AnalyzedChange
from clgen.generator import _format_changes, generate_changelog


def _make_change(
    category: str = "feature",
    title: str = "Add feature",
    is_breaking: bool = False,
    migration_hint: str | None = None,
    source_commits: list[str] | None = None,
) -> AnalyzedChange:
    return AnalyzedChange(
        category=category,
        title=title,
        is_breaking=is_breaking,
        migration_hint=migration_hint,
        source_commits=source_commits or ["feat: add feature"],
    )


class TestFormatChanges:
    """Test change formatting for prompts."""

    def test_basic_format(self) -> None:
        change = _make_change()
        result = _format_changes([change])
        assert "[feature]" in result
        assert "Add feature" in result

    def test_breaking_format(self) -> None:
        change = _make_change(is_breaking=True, migration_hint="Do X instead")
        result = _format_changes([change])
        assert "[BREAKING]" in result
        assert "Migration: Do X instead" in result

    def test_multiple_changes(self) -> None:
        changes = [_make_change(title="A"), _make_change(title="B")]
        result = _format_changes(changes)
        assert "A" in result
        assert "B" in result


class TestGenerateChangelog:
    """Test generate_changelog with mocked API."""

    def test_empty_changes(self) -> None:
        result = generate_changelog([], "1.0.0")
        assert result.version == "1.0.0"
        assert result.user_version == "No changes in this release."
        assert result.developer_version == "No changes in this release."
        assert result.summary_version == "No changes in this release."

    @patch("clgen.generator._call_llm")
    def test_calls_api_three_times(self, mock_llm: MagicMock) -> None:
        mock_llm.return_value = "Generated content"
        result = generate_changelog([_make_change()], "1.0.0")

        assert mock_llm.call_count == 3
        assert result.user_version == "Generated content"
        assert result.developer_version == "Generated content"
        assert result.summary_version == "Generated content"

    @patch("clgen.generator._call_llm")
    def test_version_and_date_set(self, mock_llm: MagicMock) -> None:
        mock_llm.return_value = "content"
        result = generate_changelog([_make_change()], "2.0.0")

        assert result.version == "2.0.0"
        assert result.date  # Should be today's date

    @patch("clgen.generator._call_llm")
    def test_three_versions_are_independent(self, mock_llm: MagicMock) -> None:
        """Each audience gets a separate API call with different content."""
        mock_llm.side_effect = ["User version", "Dev version", "Summary"]
        result = generate_changelog([_make_change()], "1.0.0")

        assert result.user_version == "User version"
        assert result.developer_version == "Dev version"
        assert result.summary_version == "Summary"

    @patch("clgen.generator._call_llm")
    def test_passes_model_to_llm(self, mock_llm: MagicMock) -> None:
        mock_llm.return_value = "content"
        generate_changelog(
            [_make_change()], "1.0.0", model="openai/gpt-4o"
        )

        for call in mock_llm.call_args_list:
            assert call.args[2] == "openai/gpt-4o"

    @patch("clgen.generator._call_llm")
    def test_breaking_change_in_developer_version(
        self, mock_llm: MagicMock
    ) -> None:
        """Breaking changes should appear in the developer version."""
        mock_llm.return_value = "Breaking: rename send to request"
        change = _make_change(
            category="breaking",
            title="Rename send to request",
            is_breaking=True,
            migration_hint="Use request() instead",
        )
        result = generate_changelog([change], "1.0.0")

        assert "Breaking" in result.developer_version
