"""CLI entry point for clgen."""

from __future__ import annotations

from enum import StrEnum

import typer
from rich.console import Console

from dotenv import load_dotenv

load_dotenv()

from clgen import __version__
from clgen.analyzer import analyze_commits, detect_model
from clgen.generator import generate_changelog
from clgen.git import filter_commits, get_commits
from clgen.renderer import append_to_changelog, render_to_file, render_to_stdout

app = typer.Typer(name="clgen", help="AI-powered changelog generator from git history.")
console = Console()


class Audience(StrEnum):
    """Target audience for changelog output."""

    user = "user"
    developer = "developer"
    summary = "summary"
    all = "all"


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"clgen v{__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Print version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
    revision_range: str | None = typer.Argument(
        None,
        help=(
            "Git revision range (e.g. v1.0.0..HEAD, HEAD~10..HEAD)."
            " Auto-detects from last tag if omitted."
        ),
    ),
    audience: Audience = typer.Option(
        Audience.all,
        "--audience",
        "-a",
        help="Target audience: user, developer, summary, or all.",
    ),
    output: str | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path. If omitted with --append, writes to CHANGELOG.md.",
    ),
    append: bool = typer.Option(
        False,
        "--append",
        help="Prepend entry to CHANGELOG.md (preserves existing content).",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Print to stdout only, do not write any files.",
    ),
    model: str | None = typer.Option(
        None,
        "--model",
        "-m",
        help="LLM model to use for analysis and generation. Auto-detected from API keys if omitted.",
    ),
) -> None:
    """clgen - AI-powered changelog generator from git history."""
    # Auto-detect model from available API keys
    if model is None:
        try:
            model = detect_model()
        except ValueError as e:
            console.print(f"[bold red]Error:[/] {e}")
            raise typer.Exit(code=2)

    # Step 1: Read git log
    with console.status("[bold blue]Reading git log..."):
        try:
            commits = get_commits(".", revision_range)
        except Exception as e:
            console.print(f"[bold red]Error:[/] Failed to read git log: {e}")
            raise typer.Exit(code=1)

    if not commits:
        console.print("[yellow]No commits found in the specified range.[/]")
        raise typer.Exit()

    # Step 2: Filter noise
    commits = filter_commits(commits)
    if not commits:
        console.print(
            "[yellow]All commits were filtered out (merge commits, chores, etc.).[/]"
        )
        raise typer.Exit()

    console.print(f"[dim]Found {len(commits)} relevant commits.[/]")

    # Step 3: AI analysis
    with console.status("[bold blue]Analyzing changes with AI..."):
        try:
            changes = analyze_commits(commits, model=model)
        except ValueError as e:
            console.print(f"[bold red]Error:[/] {e}")
            raise typer.Exit(code=2)
        except Exception as e:
            console.print(f"[bold red]Error:[/] AI analysis failed: {e}")
            raise typer.Exit(code=2)

    # Step 4: Generate content
    with console.status("[bold blue]Generating changelog content..."):
        try:
            changelog = generate_changelog(changes, version="next", model=model)
        except ValueError as e:
            console.print(f"[bold red]Error:[/] {e}")
            raise typer.Exit(code=2)
        except Exception as e:
            console.print(f"[bold red]Error:[/] Content generation failed: {e}")
            raise typer.Exit(code=2)

    # Step 5: Output
    if dry_run:
        render_to_stdout(changelog, audience.value)
    elif append:
        append_to_changelog(changelog, "CHANGELOG.md")
        console.print("[bold green]Changelog prepended to CHANGELOG.md[/]")
    elif output:
        render_to_file(changelog, output, audience.value)
        console.print(f"[bold green]Changelog written to {output}[/]")
    else:
        render_to_stdout(changelog, audience.value)


if __name__ == "__main__":
    app()
