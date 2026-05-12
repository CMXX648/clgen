"""Markdown rendering and file output."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown

from clgen.generator import GeneratedChangelog

_DIVIDER = "\n---\n\n"

_AUDIENCE_LABELS = {
    "user": "User-Facing Changelog",
    "developer": "Developer Changelog",
    "summary": "Release Summary",
}


def _select_content(changelog: GeneratedChangelog, audience: str) -> str:
    """Select the appropriate content for the given audience."""
    if audience == "user":
        return changelog.user_version
    elif audience == "developer":
        return changelog.developer_version
    elif audience == "summary":
        return changelog.summary_version
    elif audience == "all":
        parts = []
        for aud in ("user", "developer", "summary"):
            label = _AUDIENCE_LABELS[aud]
            content = getattr(changelog, f"{aud}_version")
            parts.append(f"## {label}\n\n{content}")
        return _DIVIDER.join(parts)
    else:
        raise ValueError(
            f"Unknown audience: {audience}. Use user, developer, summary, or all."
        )


def _format_header(changelog: GeneratedChangelog) -> str:
    """Format the version header."""
    return f"# [{changelog.version}] - {changelog.date}\n\n"


def render_to_stdout(changelog: GeneratedChangelog, audience: str) -> None:
    """Render changelog to terminal using Rich.

    Args:
        changelog: Generated changelog content.
        audience: Target audience (user, developer, summary, all).
    """
    console = Console()
    header = _format_header(changelog)
    content = _select_content(changelog, audience)
    full_md = header + content
    console.print(Markdown(full_md))


def render_to_file(
    changelog: GeneratedChangelog,
    output_path: str,
    audience: str,
) -> None:
    """Write changelog content to a file.

    Args:
        changelog: Generated changelog content.
        output_path: Path to write the file.
        audience: Target audience (user, developer, summary, all).
    """
    header = _format_header(changelog)
    content = _select_content(changelog, audience)
    full_md = header + content
    Path(output_path).write_text(full_md, encoding="utf-8")


def append_to_changelog(
    changelog: GeneratedChangelog,
    changelog_path: str,
) -> None:
    """Prepend changelog entry to an existing or new CHANGELOG.md.

    Inserts the new version at the top, preserving existing content below.

    Args:
        changelog: Generated changelog content.
        changelog_path: Path to the CHANGELOG.md file.
    """
    path = Path(changelog_path)
    header = _format_header(changelog)

    # Build full entry with all three audience versions
    all_content = _select_content(changelog, "all")
    new_entry = header + all_content + "\n\n"

    if path.exists():
        existing = path.read_text(encoding="utf-8")
        path.write_text(new_entry + existing, encoding="utf-8")
    else:
        path.write_text(new_entry, encoding="utf-8")
