"""Tests for git module."""

from __future__ import annotations

from pathlib import Path

import pytest
from git import Repo

from clgen.git import Commit, filter_commits, get_commits


@pytest.fixture
def git_repo(tmp_path: Path) -> Repo:
    """Create a temporary git repository with a few commits."""
    repo = Repo.init(tmp_path)
    # Ensure git author config is available
    with repo.config_writer() as cfg:
        cfg.set_value("user", "name", "Test User")
        cfg.set_value("user", "email", "test@example.com")

    # First commit
    (tmp_path / "file1.txt").write_text("initial")
    repo.index.add(["file1.txt"])
    repo.index.commit("feat: add initial feature")

    # Second commit with PR number
    (tmp_path / "file2.txt").write_text("second")
    repo.index.add(["file2.txt"])
    repo.index.commit("fix: resolve crash (#42)")

    # Third commit
    (tmp_path / "file3.txt").write_text("third")
    repo.index.add(["file3.txt"])
    repo.index.commit("docs: update readme")

    return repo


@pytest.fixture
def git_repo_with_tag(git_repo: Repo, tmp_path: Path) -> Repo:
    """Extend the git_repo fixture with a tag on the first commit."""
    first_commit = list(git_repo.iter_commits(rev="HEAD~2"))[0]
    git_repo.create_tag("v1.0.0", ref=first_commit)
    return git_repo


class TestCommitDataclass:
    """Test Commit dataclass construction."""

    def test_commit_creation(self) -> None:
        c = Commit(
            hash="abc123",
            author="Alice",
            date=__import__("datetime").datetime(2026, 1, 1),
            message="feat: something (#10)",
            short_message="feat: something (#10)",
            pr_number=10,
        )
        assert c.hash == "abc123"
        assert c.pr_number == 10


class TestGetCommits:
    """Test get_commits function."""

    def test_all_commits(self, git_repo: Repo) -> None:
        commits = get_commits(str(git_repo.working_dir))
        assert len(commits) == 3
        assert all(isinstance(c, Commit) for c in commits)

    def test_revision_range(self, git_repo: Repo) -> None:
        commits = get_commits(str(git_repo.working_dir), "HEAD~1..HEAD")
        assert len(commits) == 1
        assert commits[0].short_message == "docs: update readme"

    def test_pr_number_parsing(self, git_repo: Repo) -> None:
        commits = get_commits(str(git_repo.working_dir))
        pr_commits = [c for c in commits if c.pr_number is not None]
        assert len(pr_commits) == 1
        assert pr_commits[0].pr_number == 42

    def test_pr_number_absent(self, git_repo: Repo) -> None:
        commits = get_commits(str(git_repo.working_dir), "HEAD~1..HEAD")
        assert commits[0].pr_number is None

    def test_auto_detect_tag_range(self, git_repo_with_tag: Repo) -> None:
        commits = get_commits(str(git_repo_with_tag.working_dir))
        # Tag is on first commit, so should get 2 commits (2nd and 3rd)
        assert len(commits) == 2

    def test_empty_range(self, git_repo: Repo) -> None:
        """Empty range returns empty list without error."""
        commits = get_commits(str(git_repo.working_dir), "HEAD..HEAD")
        assert commits == []

    def test_no_tag_repo(self, git_repo: Repo) -> None:
        """Without tags, should return all commits from HEAD."""
        # No tags in git_repo, so auto-detect uses HEAD (all commits)
        commits = get_commits(str(git_repo.working_dir))
        assert len(commits) == 3

    def test_invalid_repo_path(self) -> None:
        with pytest.raises(Exception):
            get_commits("/nonexistent/path")

    def test_dates_are_parsed(self, git_repo: Repo) -> None:
        commits = get_commits(str(git_repo.working_dir))
        for c in commits:
            assert isinstance(c.date, __import__("datetime").datetime)


def _make_commit(short_message: str) -> Commit:
    """Helper to create a Commit with only short_message set."""
    return Commit(
        hash="abc",
        author="test",
        date=__import__("datetime").datetime(2026, 1, 1),
        message=short_message,
        short_message=short_message,
        pr_number=None,
    )


class TestFilterCommits:
    """Test filter_commits function."""

    def test_filters_merge_pull_request(self) -> None:
        commits = [_make_commit("Merge pull request #10 from user/branch")]
        assert filter_commits(commits) == []

    def test_filters_merge_branch(self) -> None:
        commits = [_make_commit("Merge branch 'main' into feature")]
        assert filter_commits(commits) == []

    def test_filters_chore(self) -> None:
        commits = [_make_commit("chore: update dependencies")]
        assert filter_commits(commits) == []

    def test_filters_ci(self) -> None:
        commits = [_make_commit("ci: add GitHub Actions workflow")]
        assert filter_commits(commits) == []

    def test_filters_build(self) -> None:
        commits = [_make_commit("build: upgrade webpack")]
        assert filter_commits(commits) == []

    def test_filters_bump_version(self) -> None:
        commits = [_make_commit("bump version to 1.2.0")]
        assert filter_commits(commits) == []

    def test_filters_release_v(self) -> None:
        commits = [_make_commit("release v2.0.0")]
        assert filter_commits(commits) == []

    def test_keeps_meaningful_commits(self) -> None:
        commits = [
            _make_commit("feat: add new API endpoint"),
            _make_commit("fix: resolve memory leak"),
            _make_commit("docs: update README"),
        ]
        result = filter_commits(commits)
        assert len(result) == 3

    def test_mixed_scenario(self) -> None:
        commits = [
            _make_commit("feat: add login"),
            _make_commit("chore: lint"),
            _make_commit("Merge branch 'dev'"),
            _make_commit("fix: typo"),
            _make_commit("bump version 1.0.0"),
            _make_commit("ci: add tests"),
        ]
        result = filter_commits(commits)
        assert len(result) == 2
        assert result[0].short_message == "feat: add login"
        assert result[1].short_message == "fix: typo"

    def test_empty_input(self) -> None:
        assert filter_commits([]) == []

    def test_case_insensitive(self) -> None:
        commits = [_make_commit("CHORE: uppercase")]
        assert filter_commits(commits) == []
