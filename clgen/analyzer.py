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

_DEFAULT_MODELS = {
    "anthropic": "anthropic/claude-sonnet-4-20250514",
    "openai": "openai/gpt-4o",
    "deepseek": "deepseek/deepseek-v4-flash",
}

_PROVIDER_PRIORITY = ["anthropic", "openai", "deepseek"]


def detect_model() -> str:
    """Detect the best available model based on set API keys.

    Scans environment variables and returns the default model for the
    first provider with a configured API key.

    Returns:
        Model string (e.g. "anthropic/claude-sonnet-4-20250514").

    Raises:
        ValueError: If no API keys are found.
    """
    for provider in _PROVIDER_PRIORITY:
        env_var = _MODEL_API_KEY_MAP[provider]
        if os.environ.get(env_var):
            return _DEFAULT_MODELS[provider]

    configured = ", ".join(f"{v}=..." for v in _MODEL_API_KEY_MAP.values())
    raise ValueError(
        "No API keys found. Please set at least one of the following "
        f"environment variables:\n  {configured}\n\n"
        "You can add them to a .env file in your project root."
    )


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
You are a factual changelog analyst. Given a list of git commits,
classify each into exactly one category:
- feature: new functionality
- fix: bug fix
- breaking: backward-incompatible change
- perf: performance improvement
- security: security fix
- deprecation: something being removed or replaced

### STRICT RULES:
1. **NO HALLUCINATION**: Do not invent function names, API signatures, filenames, or environment variables that are not explicitly mentioned in the commit messages.
2. **STICK TO FACTS**: If a commit message is vague (e.g., "add auth"), summarize the intent (e.g., "Implement authentication") without guessing the code implementation.
3. **MIGRATION HINTS**: Only provide a migration_hint if you can infer the specific change from the commit messages. If a breaking change is detected but the solution isn't clear, provide a general but safe warning.

Return a JSON array. Each element must have:
- "category": one of the categories above
- "title": concise, factual summary
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
