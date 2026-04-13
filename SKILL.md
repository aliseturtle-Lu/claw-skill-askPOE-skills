---
name: poe-assistant
description: 调用 Poe API 与指定 Bot（如 Claude、GPT、Gemini 等）对诗。用于当用户要求将内容发给 Poe 的 Bot 回答时使用。支持关键词自动匹配选模型。
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

## 关键词触发规则

用户发送消息时，自动根据以下关键词匹配对应的 Bot：

| 触发关键词 | 对应 Bot | 说明 |
|-----------|---------|------|
| `opus`、`最强推理`、`深度推理` | `claude-opus-4.6` | 最强推理，深度复杂任务 |
| `sonnet`、`主力`、`均衡`、`平衡` | `claude-sonnet-4.6` | 平衡之选，高质量对话和编码 |
| `haiku`、`轻量`、`快速`、`省钱` | `claude-haiku-4.5` | 轻量快速，高性价比 |
| `gpt-5-pro`、`GPT5最强`、`GPT最强` | `gpt-5-pro` | GPT-5 最强版，编程能力大幅提升 |
| `gpt-5.4`、`GPT5.4`、`5.4` | `gpt-5.4` | GPT-5.4，1M 上下文旗舰 |
| `gpt-5.4-mini`、`GPT5.4-mini` | `gpt-5.4-mini` | GPT-5.4 轻量版 |
| `nano-banana`、`图片生成`、`生图` | `nano-banana-2` | Google 图片生成 |
| `gemini`、`gemini-3.1-pro`、`多模态` | `gemini-3.1-pro` | Gemini 3.1 Pro，多模态旗舰 |
| `poe`（单独说） | `claude-sonnet-4.6` | 默认主力 Bot |

**匹配优先级**：精确匹配 > 前缀匹配 > 模糊包含
**默认 Bot**：`claude-sonnet-4.6`（不指定时使用）

## 可用 Bot（实测可用）

### 🤖 Anthropic Claude 系列
| Bot 名称 | 说明 | Context |
|---------|------|---------|
| `claude-opus-4.6` | 最强推理，深度复杂任务 | 983K |
| `claude-sonnet-4.6` | 平衡之选，高质量对话和编码 | 983K |
| `claude-haiku-4.5` | 轻量快速，高性价比 | 192K |
| `claude-code` | Poe 内置代码助手 | - |

### 🔵 OpenAI GPT / o 系列
| Bot 名称 | 说明 | Context |
|---------|------|---------|
| `gpt-5-pro` | GPT-5 最强版，编程大幅提升 | 400K |
| `gpt-5.4` | GPT-5.4 旗舰，1M 上下文 | 1.05M |
| `gpt-5.4-mini` | GPT-5.4 轻量版 | 400K |
| `GPT-4o` | GPT-4o 均衡版 | 128K |
| `o3-pro` | OpenAI 推理旗舰 | 200K |

### 🌐 Google Gemini / Imagen 系列
| Bot 名称 | 说明 | Context |
|---------|------|---------|
| `gemini-3.1-pro` | Gemini 3.1 Pro，多模态旗舰 | 1.05M |
| `nano-banana-2` | Google 图片生成 | 65K |

## ⚠️ 注意："unity best bot" / "poe assistant"

- **"unity best bot"**：在 Poe API 模型列表中未找到对应 Bot，可能是 Poe 平台界面推荐的人工编辑 Bot，不在 API 开放接口中。如需访问 Unity 海外商店相关内容，建议通过其他渠道。
- **"poe assistant"**：这是 Skill 本身的名称，不是 Bot ID，不可在 API 调用中使用。

## ⚠️ 最重要的一条规则：原文转发，禁止改写

**从 Poe 返回的内容，必须原封不动地转发给使用者，不得：
- 总结、概括、压缩
- 重新理解后用自己的话输出
- 改写任何一个字

使用方法请求发出后，Poe 返回的原文直接打印出来即可。如果用户要求"不要总结，原封不动拷贝回来"，必须 100% 照做，一字不漏。

## 返回格式
打印 Bot 的回复文本到 stdout。
