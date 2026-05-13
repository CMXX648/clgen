# clgen

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

**基于 AI 的 Git 提交历史更新日志生成器。**

别再花半小时手动整理发版说明了。`clgen` 能读懂你的 Git 日志，利用大模型（LLM）理解变更的语义，并在几秒钟内生成专业的、面向不同受众的更新日志。

[English](README.md) | [简体中文](README-CN.md)

---

## ✨ 见证奇迹

**Before**（原始、杂乱的 Git 日志）:
```text
feat: add user authentication
fix: resolve login timeout (#12)
chore: update dependencies
feat!: rename send() to request()
Merge branch 'dev' into main
```

**After**（由 `clgen` 自动生成）:

#### 👤 用户版本 (User-Facing)
- **新功能**: 增加了安全的身份验证系统。
- **Bug 修复**: 解决了登录请求偶尔超时的问题。

#### 💻 开发者版本 (Developer-Facing)
- **破坏性变更**: `send()` 已重命名为 `request()`。
  - *迁移指南*: 请将所有调用 `send()` 的地方替换为 `request()`。
- **功能实现**: 实现了 `auth` 模块逻辑。

---

## 🚀 核心特性

- **语义化理解**: 利用 LLM（OpenAI, Anthropic, DeepSeek 等）自动区分功能、修复和破坏性变更——即使你没写 Conventional Commits。
- **多受众输出**: 同时生成三个版本：
  - **用户版**: 通俗易懂，强调价值。
  - **开发者版**: 技术细节丰富，包含 API 变更和迁移提示。
  - **摘要版**: 适合社交媒体或公告的 2 句话简介。
- **零配置**: 自动检测最后一个 Tag，开箱即用。
- **安全第一**: 支持 `--dry-run` 预览，防止误写文件。

---

## 💻 操作系统支持

目前，`clgen` 已正式测试并支持以下系统：
- ✅ **Windows**
- ✅ **Linux**
- ⏳ **macOS** (暂未正式验证/支持中)

---

## 🛠 安装

```bash
# 推荐方式 (使用 uv)
uv tool install clgen

# 使用 pip
pip install clgen
```

---

## 📖 快速上手

确保你已设置 API Key（例如 `DEEPSEEK_API_KEY`, `OPENAI_API_KEY` 或 `ANTHROPIC_API_KEY`）。

```bash
# 为所有受众生成日志 (仅输出到终端)
clgen --dry-run

# 追加到 CHANGELOG.md (自动检测范围)
clgen --append

# 指定版本区间
clgen v1.0.0..HEAD

# 指定模型
clgen --model deepseek/deepseek-v4-flash
```

---

## ⚙️ 配置与模型

`clgen` 使用 [litellm](https://github.com/BerriAI/litellm) 以支持全球各种模型。

### 1. API Key 与环境变量

| 厂商 | 环境变量 | 模型参数示例 |
|----------|----------------------|--------------------|
| **DeepSeek (深度求索)** | `DEEPSEEK_API_KEY` | `--model deepseek/deepseek-v4-flash` |
| **OpenAI** | `OPENAI_API_KEY` | `--model openai/gpt-4o` |
| **Anthropic** | `ANTHROPIC_API_KEY` | `--model anthropic/claude-sonnet-4-20250514` |

### 2. 配置策略

你可以通过多种方式配置 API Key：

- **Windows 系统环境变量**: 你可以通过 *系统属性 > 环境变量* 直接设置，`clgen` 会自动读取。
- **.env 文件**: `clgen` 会在以下两个位置查找环境变量：
    1. `%USERPROFILE%\.clgen\.env`: **全局配置** (推荐，跨项目通用)。
    2. `./.env`: **项目局部配置** (会覆盖全局设置)。

---

## ⌨️ 命令行参考

| 参数 | 描述 | 默认值 |
|------|-------------|---------|
| `REVISION_RANGE` | Git 范围 (例如 `v1.0.0..HEAD`) | 自动检测 |
| `-a, --audience` | 受众: `user`, `developer`, `summary`, 或 `all` | `all` |
| `-o, --output` | 输出文件路径 | `CHANGELOG.md` |
| `--append` | 是否追加到现有文件顶部 | `True` |
| `--no-append` | 是否直接覆盖现有文件 | `False` |
| `--dry-run` | 仅打印到终端，不写入文件 | `False` |
| `-m, --model` | LLM 模型标识符 | 自动检测 |

---

## 📄 许可证

MIT
