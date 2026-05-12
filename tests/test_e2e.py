"""End-to-end tests for the full clgen pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from git import Repo

from clgen.analyzer import analyze_commits
from clgen.generator import generate_changelog
from clgen.git import filter_commits, get_commits
from clgen.renderer import append_to_changelog, render_to_file


def _setup_repo(tmp_path: Path) -> Repo:
    """Create a temp git repo with realistic commits."""
    repo = Repo.init(tmp_path)
    with repo.config_writer() as cfg:
        cfg.set_value("user", "name", "Test User")
        cfg.set_value("user", "email", "test@example.com")

    commits = [
        ("feat: add user authentication", "auth.py"),
        ("fix: resolve login timeout (#12)", "auth.py"),
        ("chore: update dependencies", "package.json"),
        ("docs: update README", "README.md"),
        ("feat!: rename send() to request()", "api.py"),
        ("Merge branch 'dev' into main", None),
    ]
    for msg, filename in commits:
        if filename:
            (tmp_path / filename).write_text(f"content for {msg}")
            repo.index.add([filename])
        else:
            repo.index.add(["auth.py"])
        repo.index.commit(msg)

    return repo


def _mock_analyze_response() -> str:
    """Return a realistic AI analysis response."""
    return json.dumps(
        [
            {
                "category": "feature",
                "title": "Add user authentication system",
                "is_breaking": False,
                "migration_hint": None,
                "source_commits": ["feat: add user authentication"],
            },
            {
                "category": "fix",
                "title": "Fix login timeout issue",
                "is_breaking": False,
                "migration_hint": None,
                "source_commits": ["fix: resolve login timeout (#12)"],
            },
            {
                "category": "breaking",
                "title": "Rename send() to request()",
                "is_breaking": True,
                "migration_hint": "Replace all send() calls with request()",
                "source_commits": ["feat!: rename send() to request()"],
            },
        ]
    )


class TestE2EPipeline:
    """Full pipeline: git -> filter -> analyze -> generate -> render."""

    def test_full_pipeline_dry_run(
        self, tmp_path: Path, capsys: MagicMock
    ) -> None:
        """Complete pipeline with mocked LLM, output to stdout."""
        repo = _setup_repo(tmp_path)

        # Step 1: Get commits
        commits = get_commits(str(repo.working_dir))
        assert len(commits) > 0

        # Step 2: Filter noise
        commits = filter_commits(commits)
        # Should filter out merge and chore, keep feat/fix/docs
        assert all(
            not c.short_message.lower().startswith(
                ("merge", "chore:", "ci:", "build:")
            )
            for c in commits
        )

        # Step 3: Mock AI analysis
        with patch("clgen.analyzer.litellm.completion") as mock_analyze:
            mock_resp = MagicMock()
            mock_resp.choices = [MagicMock()]
            mock_resp.choices[0].message.content = _mock_analyze_response()
            mock_analyze.return_value = mock_resp

            changes = analyze_commits(commits)

        assert len(changes) == 3
        categories = {c.category for c in changes}
        assert "feature" in categories
        assert "fix" in categories
        assert "breaking" in categories

        # Step 4: Mock content generation
        with patch("clgen.generator._call_llm") as mock_gen:
            mock_gen.side_effect = [
                "## What's New\n- Auth system\n- Login fix",
                "## Features\n- Auth system\n## Breaking\n- Rename send",
                "Release adds authentication and fixes login.",
            ]
            changelog = generate_changelog(changes, version="1.0.0")

        assert changelog.version == "1.0.0"
        assert "Auth system" in changelog.user_version
        assert "Rename send" in changelog.developer_version

        # Step 5: Render to file
        out = tmp_path / "CHANGELOG.md"
        render_to_file(changelog, str(out), "all")
        content = out.read_text(encoding="utf-8")
        assert "# [1.0.0]" in content
        assert "Auth system" in content

    def test_full_pipeline_append_mode(self, tmp_path: Path) -> None:
        """Pipeline with --append flag: prepend to existing CHANGELOG.md."""
        repo = _setup_repo(tmp_path)
        changelog_path = tmp_path / "CHANGELOG.md"
        changelog_path.write_text(
            "# Changelog\n\n## [0.9.0]\n\nOld release\n", encoding="utf-8"
        )

        commits = filter_commits(get_commits(str(repo.working_dir)))

        with patch("clgen.analyzer.litellm.completion") as mock_analyze:
            mock_resp = MagicMock()
            mock_resp.choices = [MagicMock()]
            mock_resp.choices[0].message.content = _mock_analyze_response()
            mock_analyze.return_value = mock_resp
            changes = analyze_commits(commits)

        with patch("clgen.generator._call_llm") as mock_gen:
            mock_gen.side_effect = ["User v1", "Dev v1", "Summary v1"]
            changelog = generate_changelog(changes, version="1.0.0")

        append_to_changelog(changelog, str(changelog_path))
        content = changelog_path.read_text(encoding="utf-8")

        # New entry before old
        assert content.index("1.0.0") < content.index("0.9.0")
        assert "Old release" in content

    def test_pipeline_empty_commits(self, tmp_path: Path) -> None:
        """Pipeline handles empty commit range gracefully."""
        repo = Repo.init(tmp_path)
        with repo.config_writer() as cfg:
            cfg.set_value("user", "name", "Test")
            cfg.set_value("user", "email", "t@t.com")
        (tmp_path / "f.txt").write_text("x")
        repo.index.add(["f.txt"])
        repo.index.commit("initial")

        commits = get_commits(str(repo.working_dir), "HEAD..HEAD")
        assert commits == []

        filtered = filter_commits(commits)
        assert filtered == []

    def test_pipeline_file_output(self, tmp_path: Path) -> None:
        """Pipeline writes correct output to specified file."""
        repo = _setup_repo(tmp_path)
        commits = filter_commits(get_commits(str(repo.working_dir)))

        with patch("clgen.analyzer.litellm.completion") as mock_analyze:
            mock_resp = MagicMock()
            mock_resp.choices = [MagicMock()]
            mock_resp.choices[0].message.content = _mock_analyze_response()
            mock_analyze.return_value = mock_resp
            changes = analyze_commits(commits)

        with patch("clgen.generator._call_llm") as mock_gen:
            mock_gen.side_effect = ["User text", "Dev text", "Summary text"]
            changelog = generate_changelog(changes, version="2.0.0")

        out = tmp_path / "release-notes.md"
        render_to_file(changelog, str(out), "developer")
        content = out.read_text(encoding="utf-8")
        assert "# [2.0.0]" in content
        assert "Dev text" in content
