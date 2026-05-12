"""AI semantic analysis for commit classification."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

import litellm

from clgen.git import Commit

CATEGORIES = ("feature", "fix", "breaking", "perf", "security", "deprecation")

_MODEL_API_KEY_MAP = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
}


def validate_api_key(model: str) -> None:
    """Validate that the required API key is set for the given model.

    Args:
        model: LiteLLM model string (e.g. "anthropic/claude-sonnet-4-20250514").

    Raises:
        ValueError: If the required API key environment variable is not set.
    """
    provider = model.split("/")[0]
    env_var = _MODEL_API_KEY_MAP.get(provider)
    if env_var and not os.environ.get(env_var):
        raise ValueError(
            f"API key not found. Please set the {env_var} environment variable.\n"
            f"You can add it to a .env file in your project root:\n"
            f"  {env_var}=your-api-key-here"
        )

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

    validate_api_key(model)

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
