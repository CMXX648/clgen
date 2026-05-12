"""AI semantic analysis for commit classification."""

from __future__ import annotations

import json
from dataclasses import dataclass, field

import litellm

from clgen.git import Commit

CATEGORIES = ("feature", "fix", "breaking", "perf", "security", "deprecation")

_SYSTEM_PROMPT = """\
You are a changelog analyst. Given a list of git commits,
classify each into exactly one category:
- feature: new functionality
- fix: bug fix
- breaking: backward-incompatible change
- perf: performance improvement
- security: security fix
- deprecation: something being removed or replaced

Also identify if a change is a breaking change. Breaking changes include:
- Function/method renames
- Parameter changes (added required, removed optional)
- API removals
- Return value type changes
Even if the commit message does not contain "!" or "BREAKING CHANGE:".

For breaking changes, provide a migration_hint with specific, actionable steps.

Group related commits that describe the same change into one entry.

Return a JSON array. Each element must have:
- "category": one of the categories above
- "title": concise summary (rewritten by you, not the raw commit message)
- "is_breaking": boolean
- "migration_hint": string or null
- "source_commits": array of commit short_messages that were grouped

Return ONLY the JSON array, no explanation.
"""


@dataclass
class AnalyzedChange:
    """A classified and grouped change from commit analysis."""

    category: str
    title: str
    is_breaking: bool
    migration_hint: str | None
    source_commits: list[str] = field(default_factory=list)


def _build_user_prompt(commits: list[Commit]) -> str:
    """Build the user message with commit list."""
    lines = []
    for c in commits:
        lines.append(f"- [{c.short_message}] (by {c.author})")
    return "Commits to analyze:\n" + "\n".join(lines)


def _parse_response(raw: str) -> list[AnalyzedChange]:
    """Parse LLM JSON response into AnalyzedChange list."""
    data = json.loads(raw)
    results = []
    for item in data:
        results.append(
            AnalyzedChange(
                category=item["category"],
                title=item["title"],
                is_breaking=item.get("is_breaking", False),
                migration_hint=item.get("migration_hint"),
                source_commits=item.get("source_commits", []),
            )
        )
    return results


def analyze_commits(
    commits: list[Commit],
    model: str = "anthropic/claude-sonnet-4-20250514",
) -> list[AnalyzedChange]:
    """Analyze commits using AI to classify and group changes.

    Args:
        commits: List of parsed Commit objects.
        model: LiteLLM model string (e.g. "anthropic/claude-sonnet-4-20250514",
            "openai/gpt-4o"). See litellm docs for supported providers.

    Returns:
        List of AnalyzedChange objects with classifications.
    """
    if not commits:
        return []

    user_prompt = _build_user_prompt(commits)

    response = litellm.completion(
        model=model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
    )

    raw_content = response.choices[0].message.content
    return _parse_response(raw_content)
