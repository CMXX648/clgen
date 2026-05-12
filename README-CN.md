# clgen

> **[English](README.md)** | **[中文](README-CN.md)**


基于 AI 的 Git 提交记录 changelog 生成器。

读取你的 git log，通过 AI 语义理解变更，自动生成面向不同受众（用户 / 开发者 / 摘要）的 Markdown changelog。

## 安装

```bash
# 使用 uv（推荐）
uv tool install clgen

# 使用 pip
pip install clgen
```

## 快速开始

```bash
# 从上一个 tag 到 HEAD 生成 changelog（所有受众）
clgen generate

# 预览模式：仅输出到终端，不写入文件
clgen generate --dry-run

# 仅生成面向用户的版本，写入文件
clgen generate --audience user --output RELEASE.md

# 追加到已有 CHANGELOG.md（保留历史内容）
clgen generate --append

# 指定版本区间
clgen generate v1.0.0..HEAD
```

## 效果对比

**原始 git log：**

```
feat: add user authentication
fix: resolve login timeout (#12)
chore: update dependencies
feat!: rename send() to request()
Merge branch 'dev' into main
```

**生成的 changelog：**

```markdown
# [1.0.0] - 2026-05-12

## 新功能

- 新增用户认证系统
- 修复登录超时问题

## 破坏性变更

- `send()` 已重命名为 `request()`
  - 迁移指南：将所有 `send()` 调用替换为 `request()`
```

## CLI 参考

```
clgen generate [OPTIONS] [REVISION_RANGE]
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `REVISION_RANGE` | Git 范围（如 `v1.0.0..HEAD`、`HEAD~10`） | 自动检测上一个 tag |
| `--audience`, `-a` | `user`、`developer`、`summary` 或 `all` | `all` |
| `--output`, `-o` | 输出到指定文件 | 标准输出 |
| `--append` | 插入到 `CHANGELOG.md` 顶部，保留已有内容 | 关闭 |
| `--dry-run` | 仅输出到标准输出，不写文件 | 关闭 |
| `--model`, `-m` | LiteLLM 模型字符串 | `anthropic/claude-sonnet-4-20250514` |
| `--version`, `-v` | 打印版本号并退出 | |

## 多模型支持

clgen 使用 [litellm](https://github.com/BerriAI/litellm) 调用 LLM。根据你使用的 provider 设置对应的 API Key：

```bash
# Anthropic（默认）
export ANTHROPIC_API_KEY=sk-ant-...

# OpenAI
export OPENAI_API_KEY=sk-...

# DeepSeek
export DEEPSEEK_API_KEY=...

# 然后使用 --model 参数
clgen generate --model openai/gpt-4o
clgen generate --model anthropic/claude-sonnet-4-20250514
clgen generate --model deepseek/deepseek-chat
```

## 开发

```bash
# 克隆并安装
git clone https://github.com/yourname/clgen.git
cd clgen
uv sync

# 运行测试
uv run pytest

# 代码检查
uv run ruff check .
uv run ruff format .
```

## 许可证

MIT
