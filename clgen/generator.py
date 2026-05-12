"""Multi-audience changelog content generation."""

from __future__ import annotations
from dataclasses import dataclass
import litellm
from clgen.analyzer import AnalyzedChange, validate_api_key

### USER_PROMPT
### 生成给非专业技术人员的内容

_USER_PROMPT = """\
Generate a user-facing changelog for version {version}.

Write in plain, non-technical language.
Focus on what changed and how it affects the user.
Do NOT include code details, function names, or technical migration steps.
Group related changes together. Use bullet points.

Changes:
{changes}

Return ONLY the Markdown text, no explanation.
"""

### DEVELOPER_PROMPT
### 生成给专业技术人员的内容

_DEVELOPER_PROMPT = """\
Generate a developer-facing changelog for version {version}.

Write with full technical detail. Include function/method names,
parameters, and code examples where relevant.
For breaking changes, include the migration hint provided.
Use Markdown headings for categories (Features, Fixes, Breaking Changes, etc.).

Changes:
{changes}

Return ONLY the Markdown text, no explanation.
"""

### SUMMARY_PROMPT
### 生成总结类型的内容

_SUMMARY_PROMPT = """\
Generate a 2-4 sentence release summary for version {version}.

This should be suitable for a tweet, Slack message, or release announcement.
Focus on the most impactful changes. Be concise and engaging.

Changes:
{changes}

Return ONLY the summary text, no explanation.
"""


@dataclass
class GeneratedChangelog:
    """Changelog content for multiple audiences."""

    version: str
    date: str
    user_version: str
    developer_version: str
    summary_version: str


# 格式化改变内容
def _format_changes(changes: list[AnalyzedChange]) -> str:
    """Format AnalyzedChange list into a readable string for prompts."""
    lines = []
    for c in changes:
        breaking = " [BREAKING]" if c.is_breaking else ""
        hint = f"\n  Migration: {c.migration_hint}" if c.migration_hint else ""
        lines.append(
            f"- [{c.category}]{breaking} {c.title}{hint}\n"
            f"  Source: {', '.join(c.source_commits)}"
        )
    return "\n".join(lines)


def _call_llm(system_prompt: str, user_prompt: str, model: str) -> str:
    """Make a single LLM completion call."""
    response = litellm.completion(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content


def generate_changelog(
    changes: list[AnalyzedChange],
    version: str,
    model: str = "anthropic/claude-sonnet-4-20250514",
) -> GeneratedChangelog:
    """Generate multi-audience changelog content.

    Args:
        changes: List of classified AnalyzedChange objects.
        version: Version string (e.g. "1.0.0").
        model: LiteLLM model string (e.g. "anthropic/claude-sonnet-4-20250514",
            "openai/gpt-4o"). See litellm docs for supported providers.

    Returns:
        GeneratedChangelog with user, developer, and summary versions.
    """
    from datetime import date

    if not changes:
        return GeneratedChangelog(
            version=version,
            date=date.today().isoformat(),
            user_version="No changes in this release.",
            developer_version="No changes in this release.",
            summary_version="No changes in this release.",
        )

    validate_api_key(model)

    changes_text = _format_changes(changes)
    today = date.today().isoformat()

    user_content = _call_llm(
        _USER_PROMPT.format(version=version, changes=changes_text),
        "Generate the user-facing changelog.",
        model,
    )
    dev_content = _call_llm(
        _DEVELOPER_PROMPT.format(version=version, changes=changes_text),
        "Generate the developer-facing changelog.",
        model,
    )
    summary_content = _call_llm(
        _SUMMARY_PROMPT.format(version=version, changes=changes_text),
        "Generate the release summary.",
        model,
    )

    return GeneratedChangelog(
        version=version,
        date=today,
        user_version=user_content,
        developer_version=dev_content,
        summary_version=summary_content,
    )
