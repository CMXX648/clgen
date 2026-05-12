"""Git log reading and noise filtering."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from git import Repo


@dataclass
class Commit:
    """A single parsed git commit."""

    hash: str
    author: str
    date: datetime
    message: str
    short_message: str
    pr_number: int | None


_PR_PATTERN = re.compile(r"\(#(\d+)\)")


def _parse_pr_number(message: str) -> int | None:
    """Extract PR number from commit message, e.g. 'fix bug (#234)' -> 234."""
    match = _PR_PATTERN.search(message)
    return int(match.group(1)) if match else None


def _find_last_tag(repo: Repo) -> str | None:
    """Find the most recent tag reachable from HEAD."""
    try:
        tags = sorted(
            repo.tags,
            key=lambda t: t.commit.committed_date,
            reverse=True,
        )
        return str(tags[0]) if tags else None
    except (IndexError, AttributeError):
        return None


def get_commits(repo_path: str, revision_range: str | None = None) -> list[Commit]:
    """Read commits from a git repository.

    Args:
        repo_path: Path to the git repository root.
        revision_range: Optional range like ``v1.0.0..HEAD`` or ``HEAD~10..HEAD``.
            If ``None``, auto-detects from last tag to HEAD.

    Returns:
        List of parsed Commit objects, ordered newest-first.
    """
    repo = Repo(repo_path)

    if revision_range is None:
        last_tag = _find_last_tag(repo)
        if last_tag is not None:
            revision_range = f"{last_tag}..HEAD"
        else:
            revision_range = "HEAD"

    raw_commits = list(repo.iter_commits(revision_range))

    return [
        Commit(
            hash=commit.hexsha,
            author=str(commit.author),
            date=datetime.fromtimestamp(commit.committed_date),
            message=commit.message.rstrip("\n"),
            short_message=commit.message.split("\n", 1)[0].rstrip("\n"),
            pr_number=_parse_pr_number(commit.message),
        )
        for commit in raw_commits
    ]


_NOISE_PREFIXES = (
    "chore:",
    "ci:",
    "build:",
    "merge pull request",
    "merge branch",
    "bump version",
    "release v",
)


def filter_commits(commits: list[Commit]) -> list[Commit]:
    """Filter out noise commits that should not appear in changelogs.

    Removes merge commits, chore/ci/build prefixed commits, and version bumps.
    """
    return [
        c for c in commits if not c.short_message.lower().startswith(_NOISE_PREFIXES)
    ]
