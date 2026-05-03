# Lissom Skills

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/cuzfrog/lissom-skills?style=for-the-badge)](https://github.com/cuzfrog/lissom-skills/stargazers)
[![CI](https://img.shields.io/github/actions/workflow/status/cuzfrog/lissom-skills/ci.yml?branch=main&style=for-the-badge&label=CI)](https://github.com/cuzfrog/lissom-skills/actions/workflows/ci.yml)
[![GitHub repo size](https://img.shields.io/github/repo-size/cuzfrog/lissom-skills?style=for-the-badge)](https://github.com/cuzfrog/lissom-skills)

[English](README.md) · [简体中文](README.zh.md) · **日本語**

```
┌─┐
│L│░ LISSOM  —  Simple, reliable Claude Code skills & agents
└─┘  SKILLS     for daily dev automation and context protection.
```

---

#### なぜ Lissom なのか？ [GSD](https://github.com/gsd-build/get-shit-done) や SuperPower との違いは？
- **ゼロ依存** — プレーンなファイルのみ。
- **薄いスキルディスパッチャー** — 徹底したコンテキスト保護。
- **冪等性** — 最小限の状態で気軽に再開。
- **厳格な仕様** — 驚きのない開発体験。

#### いつ使うのか？
- アイデアがある。仕様を詰めて実装を自動化したい。

#### いつ使わないのか？
- 簡単なタスク — 1つのエージェントで完結。
- 探索的なタスク — `/explore` を使用。

### 基本ワークフロー
```
           ┌─ interview ─┐
           │             /
 research ─┘ auto ──►   +   ──► plan ──► impl ──► review ──► done
  Specs.md    Research.md /    Plan.md         Review.md     │
   ▲                     /                                   │ critical?
   │                     └──────────── fix cycle (max 3)  ◄──┘
   │                                          │
   └──────────────── fix cycles exhausted ────┘
```

---

## インストール

プロジェクトのディレクトリで以下を実行：

```bash
curl -fsSL https://raw.githubusercontent.com/cuzfrog/lissom-skills/main/scripts/install.sh | bash
```

対応プラットフォーム：
- `.claude/` Claude Code および互換エージェント。
- `.opencode/` [OpenCode](https://opencode.ai)。
- `.qwen/` Qwen Code（近日対応予定）。
- `.gemini/` Gemini CLI（近日対応予定）。

---

## さあ始めよう！

**実行** `/lissom-auto <task_id>` — インタビューを受けて、完了を待つだけ！

1. `.lissom/tasks/<task_id>/Specs.md` 内のタスクを検索
2. 見つからない場合、外部ツール（JIRA MCP など）で特定を試みる

### ベストプラクティス

- `Specs.md` にプロジェクトドキュメントへの参照を含めると、探索を省けます。
- `CLAUDE.md` にテスト方法を明確に定義してください。

---

## 設定

`.lissom/settings.local.json` に設定を記述することで、毎回の入力を省略できます：

```json
{
  "user_attention": "default",
  "fix_threshold": "warning",
  "spec_review_required": "yes"
}
```

| キー | オプション |
|---|---|
| `user_attention` | `default` — 主要な懸念事項をインタビュー；`auto` — 自動運転（ベストエフォート）；`focused` — 網羅的な質問 |
| `fix_threshold` | `warning` — 致命的および警告を修正；`critical` — 致命的のみ；`suggestion` — すべての指摘 |
| `spec_review_required` | `yes` — リサーチ前に仕様をレビュー・改善；`no` — 仕様レビューをスキップ |

---

## アンインストール

カレントプロジェクトの `.claude/` および `.opencode/` ディレクトリからインストール済みファイルをすべて削除：

```bash
curl -fsSL https://raw.githubusercontent.com/cuzfrog/lissom-skills/main/scripts/uninstall.sh | bash
```

このバンドルでインストールされたファイルのみが削除されます。手動で追加したファイルはそのまま残ります。空になったディレクトリは自動的に整理されます。

---

## リンク

- [GitHub](https://github.com/cuzfrog/lissom-skills) — ソースコードとリリース
- [Issues](https://github.com/cuzfrog/lissom-skills/issues) — バグ報告と機能リクエスト
- [License](LICENSE) — MIT

---

## 作者

Cause Chung <cuzfrog@gmail.com>
