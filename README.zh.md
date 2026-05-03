# Lissom Skills

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/cuzfrog/lissom-skills)](https://github.com/cuzfrog/lissom-skills/stargazers)
[![GitHub last commit](https://img.shields.io/github/last-commit/cuzfrog/lissom-skills/main)](https://github.com/cuzfrog/lissom-skills/commits/main)
[![GitHub repo size](https://img.shields.io/github/repo-size/cuzfrog/lissom-skills)](https://github.com/cuzfrog/lissom-skills)
[![CI](https://github.com/cuzfrog/lissom-skills/actions/workflows/ci.yml/badge.svg)](https://github.com/cuzfrog/lissom-skills/actions/workflows/ci.yml)

```
┌─┐
│L│░ LISSOM  —  简单、可靠的 Claude Code 技能与代理
└─┘  SKILLS     用于日常开发自动化和上下文保护。
```

#### 为什么选择 Lissom？与 GSD、SuperPower 有何不同？
- **零依赖** — 纯文件。
- **薄调度层** — 极致的上下文保护。
- **幂等性** — 最小状态，无忧恢复。
- **严谨规范** — 无惊喜的开发体验。

#### 何时使用？
- 我有一个想法，帮我完善规范并自动化实现。

#### 何时不使用？
- 简单任务 — 直接在一个代理中完成。
- 探索性任务 — 使用 `/explore`。

### 基本工作流
```
           ┌─ 访谈 ──┐
           │          /
 research ─┘ auto ──►   +   ──► plan ──► impl ──► review ──► done
  Specs.md    Research.md /    Plan.md         Review.md     │
   ▲                       /                                  │ 关键问题?
   │                       └──────── 修复循环（最多 3 次） ◄──┘
   │                                            │
   └─────────────── 修复循环耗尽 ────────────────┘
```

## 安装

在项目目录中执行：
```bash
curl -fsSL https://raw.githubusercontent.com/cuzfrog/lissom-skills/main/scripts/install.sh | bash
```

支持的平台：
- `.claude/` Claude Code 及兼容代理。
- `.opencode/` OpenCode。
- `.qwen/` Qwen Code（即将支持）。
- `.gemini/` Gemini CLI（即将支持）。

## 开始使用
**运行** `/lissom-auto <task_id>` — 接受访谈，等待任务完成！

1. 工具会在 `.lissom/tasks/<task_id>/Specs.md` 中查找任务
2. 如果未找到，会尝试通过外部工具定位（例如 JIRA MCP）

### 最佳实践
- 在 `Specs.md` 中引用项目文档，可节省探索时间。
- 确保测试方法在 `CLAUDE.md` 中明确定义。

## 配置

在 `.lissom/settings.local.json` 中设置偏好，避免每次运行时被询问：

```json
{
  "user_attention": "default",
  "fix_threshold": "warning",
  "spec_review_required": "yes"
}
```

| 键 | 选项 |
|---|---|
| `user_attention` | `default` — 对主要问题进行访谈；`auto` — 尽量自动处理；`focused` — 详细追问 |
| `fix_threshold` | `warning` — 修复关键和警告问题；`critical` — 仅关键问题；`suggestion` — 全部问题 |
| `spec_review_required` | `yes` — 在研究前评审和完善规范；`no` — 跳过规范评审 |

## 卸载

删除当前项目中 `.claude/` 和 `.opencode/` 目录中的所有已安装文件：

```bash
curl -fsSL https://raw.githubusercontent.com/cuzfrog/lissom-skills/main/scripts/uninstall.sh | bash
```

仅移除该工具包安装的文件，您自行添加的文件不会被删除。空目录会自动清理。

## 作者

Cause Chung <cuzfrog@gmail.com>
