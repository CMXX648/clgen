# clgen

> **[English](README.md)** | **[中文](README-CN.md)**

AI-powered changelog generator from git history.

Reads your git log, uses AI to understand changes semantically, and generates audience-specific changelogs (user-facing, developer, or summary) in Markdown.

## Installation

```bash
# With uv (recommended)
uv tool install clgen

# With pip
pip install clgen
```

## Quick Start

```bash
# Generate changelog from last tag to HEAD (all audiences)
clgen generate

# Dry-run: print to terminal only, no files written
clgen generate --dry-run

# User-facing changelog only, written to a file
clgen generate --audience user --output RELEASE.md

# Append to existing CHANGELOG.md (preserves history)
clgen generate --append

# Specific version range
clgen generate v1.0.0..HEAD
```

## Before / After

**Before** (raw git log):

```
feat: add user authentication
fix: resolve login timeout (#12)
chore: update dependencies
feat!: rename send() to request()
Merge branch 'dev' into main
```

**After** (generated changelog):

```markdown
# [1.0.0] - 2026-05-12

## What's New

- Added user authentication system
- Fixed login timeout issue

## Breaking Changes

- `send()` has been renamed to `request()`
  - Migration: Replace all `send()` calls with `request()`
```

## CLI Reference

```
clgen generate [OPTIONS] [REVISION_RANGE]
```

| Flag | Description | Default |
|------|-------------|---------|
| `REVISION_RANGE` | Git range (e.g. `v1.0.0..HEAD`, `HEAD~10`) | Auto-detect from last tag |
| `--audience`, `-a` | `user`, `developer`, `summary`, or `all` | `all` |
| `--output`, `-o` | Write output to a file | stdout |
| `--append` | Prepend to `CHANGELOG.md`, preserving existing content | off |
| `--dry-run` | Print to stdout only, no file writes | off |
| `--model`, `-m` | LiteLLM model string | `anthropic/claude-sonnet-4-20250514` |
| `--version`, `-v` | Print version and exit | |

## Multi-Model Support

clgen uses [litellm](https://github.com/BerriAI/litellm) for LLM calls. Set the appropriate API key for your provider:

```bash
# Anthropic (default)
export ANTHROPIC_API_KEY=sk-ant-...

# OpenAI
export OPENAI_API_KEY=sk-...

# DeepSeek
export DEEPSEEK_API_KEY=...

# Then use the --model flag
clgen generate --model openai/gpt-4o
clgen generate --model anthropic/claude-sonnet-4-20250514
clgen generate --model deepseek/deepseek-chat
```

## Development

```bash
# Clone and install
git clone https://github.com/yourname/clgen.git
cd clgen
uv sync

# Run tests
uv run pytest

# Lint
uv run ruff check .
uv run ruff format .
```

## License

MIT
