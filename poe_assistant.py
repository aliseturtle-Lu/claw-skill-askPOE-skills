#!/usr/bin/env python3
"""
Poe Assistant - 调用 Poe API 与指定 Bot 对话
用法:
  uv run python poe_assistant.py --bot Gemini-2.5-Pro --message "你好"
  uv run python poe_assistant.py --bot claude-sonnet-4.6 --message "你是谁" --system-prompt "你是一个helpful助手" --temperature 0.7
"""

import argparse
import subprocess
import json
import time
import sys
import urllib.parse
import urllib.request


def get_api_key() -> str:
    """从 macOS Keychain 读取 poe-api-key"""
    result = subprocess.run(
        ["security", "find-generic-password", "-a", "poe", "-w"],
        capture_output=True, text=True, timeout=5
    )
    if result.returncode != 0:
        raise RuntimeError(f"无法从 Keychain 读取 API Key: {result.stderr}")
    key = result.stdout.strip()
    if not key:
        raise RuntimeError("Keychain 中的 poe-api-key 为空")
    return key


def send_message(api_key: str, bot_name: str, message: str,
                 system_prompt: str = None, temperature: float = None) -> str:
    """发送消息到 Poe，返回 message_id"""
    # 构建表单数据
    post_data = {
        "message": message,
        "bot_view": bot_name,
    }
    if system_prompt:
        post_data["system_prompt"] = system_prompt
    if temperature is not None:
        post_data["temperature"] = temperature

    data = "&".join(f"{urllib.parse.quote(k)}={urllib.parse.quote(str(v))}" for k, v in post_data.items())
    data = data.encode()

    req = urllib.request.Request(
        f"https://api.poe.com/bot/{bot_name}/send_message",
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.loads(resp.read())
    return body["message_id"]


def get_response(api_key: str, bot_name: str, message_id: str) -> str:
    """轮询获取 Bot 的回复"""
    url = f"https://api.poe.com/bot/{bot_name}/get_message_response?message_id={message_id}"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {api_key}"},
        method="GET"
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.loads(resp.read())
    return body


def wait_for_response(api_key: str, bot_name: str, message_id: str, timeout: int = 60) -> str:
    """轮询直到收到 Bot 的文字回复"""
    start = time.time()
    while time.time() - start < timeout:
        result = get_response(api_key, bot_name, message_id)
        messages = result.get("messages", [])
        for msg in reversed(messages):
            if msg.get("message_type") == "assistant" and msg.get("content"):
                parts = msg["content"]
                for part in parts:
                    if part.get("__typename") == "Text":
                        return part["text"]
        time.sleep(1)
    raise TimeoutError(f"等待回复超时（{timeout}秒）")


def main():
    parser = argparse.ArgumentParser(description="Poe Assistant - 调用 Poe Bot 对话")
    parser.add_argument("--bot", "-b", default="claude-sonnet-4.6",
                        help="Bot 名称（默认: claude-sonnet-4.6）")
    parser.add_argument("--message", "-m", required=True,
                        help="发给 Bot 的消息")
    parser.add_argument("--system-prompt", "-s", default=None,
                        help="系统提示词（system prompt），用于设定 Bot 角色或行为规则")
    parser.add_argument("--temperature", "-t", type=float, default=None,
                        help="采样温度（0.0-2.0），控制随机性。较低=更确定性，较高=更有创造性。默认不指定（使用 Bot 原始设置）")
    parser.add_argument("--timeout", type=int, default=120,
                        help="等待回复的超时时间（秒），默认 120")
    args = parser.parse_args()

    api_key = get_api_key()

    # 构建调用信息
    opts = []
    if args.system_prompt:
        opts.append(f"system_prompt={args.system_prompt[:30]}...")
    if args.temperature is not None:
        opts.append(f"temperature={args.temperature}")
    opt_str = f" [{', '.join(opts)}]" if opts else ""

    print(f"[Poe] 正在发送消息到 {args.bot}{opt_str}...", file=sys.stderr)

    message_id = send_message(
        api_key,
        args.bot,
        args.message,
        system_prompt=args.system_prompt,
        temperature=args.temperature
    )
    reply = wait_for_response(api_key, args.bot, message_id, timeout=args.timeout)
    print(reply)


if __name__ == "__main__":
    main()
