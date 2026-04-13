#!/usr/bin/env python3
"""
Poe API Assistant - 调用 Poe 上的任意 Bot (OpenAI 兼容格式)
支持文本、图像、音频、视频生成
"""

import os
import sys
import json
import argparse
import base64
from pathlib import Path
from datetime import datetime

try:
    from openai import OpenAI
except ImportError:
    print("请安装 openai 库: pip install openai")
    sys.exit(1)

# 输出目录
OUTPUT_DIR = Path.home() / ".openclaw" / "workspace" / "poe-output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Poe Chat Completions Strict 模式请求头
POE_FEATURE_HEADER = {"poe-feature": "chat-completions-strict"}

# Preset 文件路径
PRESET_FILE = Path(__file__).parent / "bot_preset.json"


def load_presets():
    """加载 bot_preset.json"""
    if not PRESET_FILE.exists():
        return {}
    with open(PRESET_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {p["name"]: p for p in data.get("presets", [])}


def match_preset(presets: dict, text: str):
    """根据关键词匹配 preset（精确匹配 > 前缀 > 模糊）"""
    text_lower = text.lower()
    for name, preset in presets.items():
        # 精确命中 preset 名称
        if text_lower == name:
            return preset
    for name, preset in presets.items():
        # 前缀或包含
        for kw in preset.get("keywords", []):
            if kw.lower() in text_lower:
                return preset
    return None


def resolve_preset(presets: dict, preset_arg: str = None, message: str = None):
    """解析 preset：优先用显式参数，再从消息中匹配关键词"""
    if preset_arg and preset_arg in presets:
        return presets[preset_arg]
    if message:
        matched = match_preset(presets, message)
        if matched:
            return matched
    return None


def get_api_key():
    """从环境变量或Keychain获取API Key"""
    api_key = os.environ.get("POE_API_KEY")
    if api_key:
        return api_key

    try:
        import subprocess
        result = subprocess.run(
            ["security", "find-generic-password", "-s", "poe-api-key", "-w"],
            capture_output=True, text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass

    return None


def save_media(content: str, media_type: str, prompt: str = "") -> str:
    """保存多媒体内容"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    safe_prompt = "".join(c for c in prompt[:30] if c.isalnum() or c in " _-").strip()
    if not safe_prompt:
        safe_prompt = "output"

    filename = f"{timestamp}_{safe_prompt}"

    if media_type == "image":
        try:
            if "," in content:
                header, b64data = content.split(",", 1)
                ext = "png"
                if "jpeg" in header or "jpg" in header:
                    ext = "jpg"
                elif "gif" in header:
                    ext = "gif"
                elif "webp" in header:
                    ext = "webp"
            else:
                b64data = content
                ext = "png"

            img_data = base64.b64decode(b64data)
            filepath = OUTPUT_DIR / f"{filename}.{ext}"
            filepath.write_bytes(img_data)
            return str(filepath)
        except Exception as e:
            return f"保存图片失败: {e}"

    elif media_type == "audio":
        try:
            audio_data = base64.b64decode(content)
            filepath = OUTPUT_DIR / f"{filename}.mp3"
            filepath.write_bytes(audio_data)
            return str(filepath)
        except Exception as e:
            return f"保存音频失败: {e}"

    elif media_type == "video":
        try:
            video_data = base64.b64decode(content)
            filepath = OUTPUT_DIR / f"{filename}.mp4"
            filepath.write_bytes(video_data)
            return str(filepath)
        except Exception as e:
            return f"保存视频失败: {e}"

    return "不支持的媒体类型"


def send_message(message: str, bot: str = "gpt-4o", api_key: str = None, temperature: float = 0, system_prompt: str = None):
    """发送消息到 Poe Bot (OpenAI 兼容格式)"""

    if not api_key:
        api_key = get_api_key()

    if not api_key:
        print("错误: 未找到 Poe API Key")
        print('请运行: security add-generic-password -s "poe-api-key" -a "poe" -w "your_api_key"')
        sys.exit(1)

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.poe.com/v1"
    )

    print(f"🤖 使用 Bot: {bot}")

    # 构建消息列表，支持 system prompt
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": message})

    # 尝试 Strict 模式（poe-feature: chat-completions-strict）
    strict_mode = True
    try:
        response = client.chat.completions.create(
            model=bot,
            messages=messages,
            max_tokens=4096,
            temperature=temperature,
            extra_headers=POE_FEATURE_HEADER
        )
        strict_mode = True
    except Exception as e:
        # Strict 模式失败时，降级到无 header 请求（grace period 兼容）
        print(f"⚠️ Strict 模式请求失败 ({e})，尝试降级到 legacy 模式...")
        try:
            response = client.chat.completions.create(
                model=bot,
                messages=messages,
                max_tokens=4096,
                temperature=temperature
            )
            strict_mode = False
        except Exception as e2:
            print(f"错误: {e2}")
            sys.exit(1)

    # 读取 x-poe-feature-active 响应头（调试用）
    # 注意：同步 API 的 ChatCompletion 对象可能不直接暴露 headers，
    # 尝试从 _response 属性获取（OpenAI SDK >= 1.0）
    try:
        feature_active = None
        if hasattr(response, '_response') and hasattr(response._response, 'headers'):
            feature_active = response._response.headers.get("x-poe-feature-active")
        elif hasattr(response, 'headers'):
            feature_active = response.headers.get("x-poe-feature-active")
        if feature_active:
            print(f"   [Poe feature handler: {feature_active}]")
    except Exception:
        pass  # header 读取失败不影响主流程

    # 提取文本回复
    text = response.choices[0].message.content

    result = {
        "text": text,
        "attachments": []
    }

    return result


def display_result(result: dict):
    """显示结果"""
    if result.get("text"):
        print(result["text"].strip())

    attachments = result.get("attachments", [])
    if attachments:
        print("\n" + "=" * 50)
        print("📎 已生成的媒体文件:")
        print("=" * 50)
        for att in attachments:
            print(f"  [{att['type'].upper()}] {att['path']}")


def list_bots(client: OpenAI):
    """列出所有可用模型"""
    try:
        models = client.models.list()
        print("可用 Bots / Models：")
        for m in models.data:
            print(f"  - {m.id}")
    except Exception as e:
        print(f"获取模型列表失败: {e}")


def chat_mode(api_key: str = None, temperature: float = 0, system_prompt: str = None):
    """交互式聊天模式"""
    print("🤖 Poe Multi-Bot Assistant 交互模式")
    print("使用 OpenAI 兼容 API")
    print("输入问题后按回车发送，输入 'quit' 或 'exit' 退出")
    print("输入 '/bot <name>' 切换 Bot")
    print("输入 '/bots' 查看所有可用模型")
    print(f"输出目录: {OUTPUT_DIR}")
    print("-" * 50)

    bot = "gpt-4o"

    client = None

    while True:
        try:
            user_input = input("\n你: ").strip()

            if user_input.lower() in ["quit", "exit", "q"]:
                print("再见!")
                break

            if not user_input:
                continue

            if user_input.startswith("/bot "):
                bot = user_input[5:].strip()
                print(f"✅ 已切换到: {bot}")
                continue

            if user_input.strip() == "/bots":
                if not client:
                    client = OpenAI(
                        api_key=api_key,
                        base_url="https://api.poe.com/v1"
                    )
                list_bots(client)
                continue

            print(f"\n🤖 {bot}: ", end="", flush=True)
            result = send_message(user_input, bot, api_key, temperature, system_prompt)
            display_result(result)

        except KeyboardInterrupt:
            print("\n\n再见!")
            break
        except EOFError:
            break


def main():
    presets = load_presets()

    parser = argparse.ArgumentParser(description="Poe Multi-Bot Assistant")
    parser.add_argument("prompt", nargs="?", help="要发送给Poe的问题")
    parser.add_argument("-b", "--bot", default="gpt-4o", help="使用的 Bot (默认: gpt-4o)")
    parser.add_argument("-t", "--temperature", type=float, default=None, help="采样温度 (默认: preset 值或 0)")
    parser.add_argument("-s", "--system", default=None, help="系统提示词（会覆盖 preset）")
    parser.add_argument("-p", "--preset", default=None,
                        help="使用的 Preset 名称（如 expert/programmer/creative/conversational）"
                             "，也可在 prompt 中包含关键词自动匹配")
    parser.add_argument("-i", "--interactive", action="store_true", help="交互式聊天模式")
    parser.add_argument("--list-bots", action="store_true", help="列出所有可用的模型")
    parser.add_argument("--list-presets", action="store_true", help="列出所有 Preset")
    parser.add_argument("--api-key", help="Poe API Key")

    args = parser.parse_args()

    api_key = args.api_key or get_api_key()

    # --list-presets 模式
    if args.list_presets:
        print("可用 Presets：")
        for name, p in presets.items():
            print(f"  [{name}] {p['description']}")
            print(f"    关键词: {', '.join(p['keywords'])}")
            print(f"    temperature: {p['temperature']}")
        return

    # --list-bots 模式
    if args.list_bots:
        client = OpenAI(api_key=api_key, base_url="https://api.poe.com/v1")
        list_bots(client)
        return

    # 解析 preset
    preset = resolve_preset(presets, args.preset, args.prompt)
    temperature = args.temperature if args.temperature is not None else (preset["temperature"] if preset else 0)
    system_prompt = args.system if args.system else (preset["system_prompt"] if preset else None)

    if preset:
        print(f"[Preset] {preset['name']} - {preset['description']}", file=sys.stderr)

    # 交互模式
    if args.interactive or (not args.prompt):
        chat_mode(api_key, temperature, system_prompt)
    else:
        result = send_message(args.prompt, args.bot, api_key, temperature, system_prompt)
        display_result(result)


if __name__ == "__main__":
    main()
