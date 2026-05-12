"""Tests for analyzer module."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from clgen.analyzer import _parse_response, analyze_commits
from clgen.git import Commit


def _make_commit(short_message: str, author: str = "dev") -> Commit:
    return Commit(
        hash="abc123",
        author=author,
        date=__import__("datetime").datetime(2026, 1, 1),
        message=short_message,
        short_message=short_message,
        pr_number=None,
    )


class TestParseResponse:
    """Test JSON response parsing."""

    def test_parse_single_change(self) -> None:
        raw = json.dumps(
            [
                {
                    "category": "feature",
                    "title": "Add login endpoint",
                    "is_breaking": False,
                    "migration_hint": None,
                    "source_commits": ["feat: add login"],
                }
            ]
        )
        result = _parse_response(raw)
        assert len(result) == 1
        assert result[0].category == "feature"
        assert result[0].is_breaking is False
        assert result[0].migration_hint is None

    def test_parse_breaking_change(self) -> None:
        raw = json.dumps(
            [
                {
                    "category": "breaking",
                    "title": "Rename send() to request()",
                    "is_breaking": True,
                    "migration_hint": "Replace all send() calls with request()",
                    "source_commits": ["refactor: rename send"],
                }
            ]
        )
        result = _parse_response(raw)
        assert result[0].is_breaking is True
        assert result[0].migration_hint == "Replace all send() calls with request()"

    def test_parse_multiple_changes(self) -> None:
        raw = json.dumps(
            [
                {
                    "category": "feature",
                    "title": "New API",
                    "is_breaking": False,
                    "migration_hint": None,
                    "source_commits": ["feat: api"],
                },
                {
                    "category": "fix",
                    "title": "Fix crash",
                    "is_breaking": False,
                    "migration_hint": None,
                    "source_commits": ["fix: crash"],
                },
            ]
        )
        result = _parse_response(raw)
        assert len(result) == 2

    def test_parse_empty_array(self) -> None:
        result = _parse_response("[]")
        assert result == []


class TestAnalyzeCommits:
    """Test analyze_commits with mocked API."""

    def test_empty_commits(self) -> None:
        result = analyze_commits([])
        assert result == []

    @patch("clgen.analyzer.litellm.completion")
    def test_model_passed_to_litellm(self, mock_completion: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "[]"
        mock_completion.return_value = mock_response

        commits = [_make_commit("feat: add feature")]
        analyze_commits(commits, model="openai/gpt-4o")

        mock_completion.assert_called_once()
        call_kwargs = mock_completion.call_args
        assert call_kwargs.kwargs["model"] == "openai/gpt-4o"

    @patch("clgen.analyzer.litellm.completion")
    def test_default_model_is_anthropic(self, mock_completion: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "[]"
        mock_completion.return_value = mock_response

        analyze_commits([_make_commit("feat: test")])

        call_kwargs = mock_completion.call_args
        assert "anthropic" in call_kwargs.kwargs["model"]

    @patch("clgen.analyzer.litellm.completion")
    def test_classifies_feature(self, mock_completion: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(
            [
                {
                    "category": "feature",
                    "title": "Add new feature",
                    "is_breaking": False,
                    "migration_hint": None,
                    "source_commits": ["feat: new feature"],
                }
            ]
        )
        mock_completion.return_value = mock_response

        result = analyze_commits([_make_commit("feat: new feature")])

        assert len(result) == 1
        assert result[0].category == "feature"

    @patch("clgen.analyzer.litellm.completion")
    def test_classifies_breaking_with_hint(self, mock_completion: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(
            [
                {
                    "category": "breaking",
                    "title": "Rename send to request",
                    "is_breaking": True,
                    "migration_hint": "Replace send() with request()",
                    "source_commits": ["refactor: rename send"],
                }
            ]
        )
        mock_completion.return_value = mock_response

        result = analyze_commits([_make_commit("refactor: rename send")])

        assert result[0].is_breaking is True
        assert result[0].migration_hint == "Replace send() with request()"

    @patch("clgen.analyzer.litellm.completion")
    def test_groups_related_commits(self, mock_completion: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(
            [
                {
                    "category": "feature",
                    "title": "Add user authentication",
                    "is_breaking": False,
                    "migration_hint": None,
                    "source_commits": [
                        "feat: auth",
                        "feat: login page",
                        "fix: auth redirect",
                    ],
                }
            ]
        )
        mock_completion.return_value = mock_response

        commits = [
            _make_commit("feat: auth"),
            _make_commit("feat: login page"),
            _make_commit("fix: auth redirect"),
        ]
        result = analyze_commits(commits)

        assert len(result) == 1
        assert len(result[0].source_commits) == 3


class TestBreakingChangeIdentification:
    """Test breaking change detection scenarios for TASK-005."""

    @patch("clgen.analyzer.litellm.completion")
    def test_explicit_breaking_with_marker(self, mock_completion: MagicMock) -> None:
        """Commit with '!' marker is identified as breaking."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(
            [
                {
                    "category": "breaking",
                    "title": "Remove deprecated auth endpoint",
                    "is_breaking": True,
                    "migration_hint": "Use /v2/auth instead of /auth",
                    "source_commits": ["feat!: remove deprecated auth endpoint"],
                }
            ]
        )
        mock_completion.return_value = mock_response

        result = analyze_commits(
            [_make_commit("feat!: remove deprecated auth endpoint")]
        )

        assert result[0].is_breaking is True
        assert result[0].category == "breaking"
        assert result[0].migration_hint is not None

    @patch("clgen.analyzer.litellm.completion")
    def test_implicit_breaking_no_marker(self, mock_completion: MagicMock) -> None:
        """Commit without '!' or 'BREAKING CHANGE:' but with breaking content."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(
            [
                {
                    "category": "breaking",
                    "title": "Rename send() to request()",
                    "is_breaking": True,
                    "migration_hint": "Replace all send() calls with request()",
                    "source_commits": ["refactor: rename send method"],
                }
            ]
        )
        mock_completion.return_value = mock_response

        result = analyze_commits([_make_commit("refactor: rename send method")])

        assert result[0].is_breaking is True
        assert result[0].migration_hint == "Replace all send() calls with request()"

    @patch("clgen.analyzer.litellm.completion")
    def test_non_breaking_commit(self, mock_completion: MagicMock) -> None:
        """Regular feature commit is not breaking."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(
            [
                {
                    "category": "feature",
                    "title": "Add dark mode toggle",
                    "is_breaking": False,
                    "migration_hint": None,
                    "source_commits": ["feat: add dark mode"],
                }
            ]
        )
        mock_completion.return_value = mock_response

        result = analyze_commits([_make_commit("feat: add dark mode")])

        assert result[0].is_breaking is False
        assert result[0].migration_hint is None

    @patch("clgen.analyzer.litellm.completion")
    def test_breaking_hint_is_actionable(self, mock_completion: MagicMock) -> None:
        """Migration hint should contain specific, actionable instructions."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(
            [
                {
                    "category": "breaking",
                    "title": "Change API return type from list to dict",
                    "is_breaking": True,
                    "migration_hint": (
                        "Update code that iterates over the return"
                        " value to use .values() instead"
                    ),
                    "source_commits": ["refactor: change API return type"],
                }
            ]
        )
        mock_completion.return_value = mock_response

        result = analyze_commits([_make_commit("refactor: change API return type")])

        hint = result[0].migration_hint
        assert hint is not None
        assert len(hint) > 10  # Should be specific, not generic
