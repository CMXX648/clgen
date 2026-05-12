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
clgen

# Dry-run: print to terminal only, no files written
clgen --dry-run

# User-facing changelog only, written to a file
clgen --audience user --output RELEASE.md

# Append to existing CHANGELOG.md (preserves history)
clgen --append

# Specific version range
clgen v1.0.0..HEAD
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
clgen [OPTIONS] [REVISION_RANGE]
```

| Flag | Description | Default |
|------|-------------|---------|
| `REVISION_RANGE` | Git range (e.g. `v1.0.0..HEAD`, `HEAD~10`) | Auto-detect from last tag |
| `--audience`, `-a` | `user`, `developer`, `summary`, or `all` | `all` |
| `--output`, `-o` | Write output to a file | stdout |
| `--append` | Prepend to `CHANGELOG.md`, preserving existing content | off |
| `--dry-run` | Print to stdout only, no file writes | off |
| `--model`, `-m` | LiteLLM model string | Auto-detect from API keys |
| `--version`, `-v` | Print version and exit | |

## Multi-Model Support

clgen uses [litellm](https://github.com/BerriAI/litellm) for LLM calls. You can use Anthropic, OpenAI, DeepSeek, or any other litellm-supported provider.

### Auto-Detection

When `--model` is not specified, clgen automatically scans your environment variables and selects a model based on the first available API key:

| API Key Set | Auto-Selected Model |
|-------------|---------------------|
| `ANTHROPIC_API_KEY` | `anthropic/claude-sonnet-4-20250514` |
| `OPENAI_API_KEY` | `openai/gpt-4o` |
| `DEEPSEEK_API_KEY` | `deepseek/deepseek-chat` |

Priority order: Anthropic > OpenAI > DeepSeek.

### Custom Model

Use `--model` to override the auto-detected model or choose a specific one:

```bash
# Use OpenAI
export OPENAI_API_KEY=sk-...
clgen --model openai/gpt-4o

# Use DeepSeek
export DEEPSEEK_API_KEY=...
clgen --model deepseek/deepseek-chat

# Use any litellm-supported model
clgen --model anthropic/claude-sonnet-4-20250514
clgen --model openai/gpt-4o-mini
clgen --model deepseek/deepseek-coder
```

### API Key Configuration

You can set API keys via environment variables or a `.env` file in your project root:

```bash
# Option 1: Environment variable
export ANTHROPIC_API_KEY=sk-ant-...

# Option 2: .env file (create in project root)
echo 'ANTHROPIC_API_KEY=sk-ant-...' > .env
```

## Development

```bash
# Clone and install
git clone https://github.com/cmxx648/clgen.git
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
