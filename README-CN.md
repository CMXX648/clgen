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
clgen

# 预览模式：仅输出到终端，不写入文件
clgen --dry-run

# 仅生成面向用户的版本，写入文件
clgen --audience user --output RELEASE.md

# 追加到已有 CHANGELOG.md（保留历史内容）
clgen --append

# 指定版本区间
clgen v1.0.0..HEAD
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

**clgen生成的 changelog：**

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
clgen [OPTIONS] [REVISION_RANGE]
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `REVISION_RANGE` | Git 范围（如 `v1.0.0..HEAD`、`HEAD~10`） | 自动检测上一个 tag |
| `--audience`, `-a` | `user`、`developer`、`summary` 或 `all` | `all` |
| `--output`, `-o` | 输出到指定文件 | 标准输出 |
| `--append` | 插入到 `CHANGELOG.md` 顶部，保留已有内容 | 关闭 |
| `--dry-run` | 仅输出到标准输出，不写文件 | 关闭 |
| `--model`, `-m` | LiteLLM 模型字符串 | 根据 API Key 自动检测 |
| `--version`, `-v` | 打印版本号并退出 | |

## 多模型支持

clgen 使用 [litellm](https://github.com/BerriAI/litellm) 调用 LLM。支持 Anthropic、OpenAI、DeepSeek 或其他 litellm 兼容的 provider。

### 自动检测

未指定 `--model` 时，clgen 会自动扫描环境变量，根据已配置的 API Key 选择对应模型：

| 已设置的 API Key | 自动选择的模型 |
|------------------|---------------|
| `ANTHROPIC_API_KEY` | `anthropic/claude-sonnet-4-20250514` |
| `OPENAI_API_KEY` | `openai/gpt-4o` |
| `DEEPSEEK_API_KEY` | `deepseek/deepseek-chat` |

优先级顺序：Anthropic > OpenAI > DeepSeek。

### 自定义模型

使用 `--model` 覆盖自动检测结果，或指定特定模型：

```bash
# 使用 OpenAI
export OPENAI_API_KEY=sk-...
clgen --model openai/gpt-4o

# 使用 DeepSeek
export DEEPSEEK_API_KEY=...
clgen --model deepseek/deepseek-chat

# 使用任意 litellm 支持的模型
clgen --model anthropic/claude-sonnet-4-20250514
clgen --model openai/gpt-4o-mini
clgen --model deepseek/deepseek-coder
```

### API Key 配置

可以通过环境变量或项目根目录的 `.env` 文件设置 API Key：

```bash
# 方式一：环境变量
export ANTHROPIC_API_KEY=sk-ant-...

# 方式二：.env 文件（在项目根目录创建）
echo 'ANTHROPIC_API_KEY=sk-ant-...' > .env
```

## 开发

```bash
# 克隆并安装
git clone https://github.com/cmxx648/clgen.git
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
