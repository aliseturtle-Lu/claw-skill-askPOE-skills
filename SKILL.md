---
name: poe-assistant
description: 调用 Poe API 与指定 Bot（如 Claude、GPT、Gemini 等）对诗。用于当用户要求将内容发给 Poe 的 Bot 回答时使用。
---

# Poe Assistant Skill

通过 Poe API（OpenAI 兼容端点 `https://api.poe.com/v1`）发送消息给指定的 Bot，返回 Bot 的回复。

## 脚本位置
`~/.openclaw/workspace/skills/poe-assistant/scripts/poe_assistant.py`

## API Key
已存在 macOS Keychain（`security find-generic-password -a poe -w`）

## 使用方式
```bash
uv run python ~/.openclaw/workspace/skills/poe-assistant/scripts/poe_assistant.py "问题" -b claude-sonnet-4.6
```

## 可用 Bot（实测可用）

### Claude 系列（推荐）
| Bot 名称 | 说明 |
|---------|------|
| `claude-sonnet-4.6` | Claude 3.5 Sonnet，平衡性能 |
| `claude-opus-4.6` | Claude 3.5 Opus，最强推理 |
| `claude-sonnet-4.5` | Claude 3 Sonnet |
| `claude-opus-4.5` | Claude 3 Opus |
| `claude-haiku-4.5` | Claude 3.5 Haiku，轻量快速 |
| `claude-code` | Claude Code |

### 其他模型
| Bot 名称 | 说明 |
|---------|------|
| `gemini-2.5-pro` | Google Gemini 2.5 Pro |
| `gemini-2.5-flash` | Google Gemini 2.5 Flash |
| `GPT-4o` | OpenAI GPT-4o |
| `claude-3-5-sonnet` | Claude 3.5 Sonnet（早期版本） |

## 返回格式
打印 Bot 的回复文本到 stdout。
