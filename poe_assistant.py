#!/usr/bin/env python3
"""
Poe Assistant - 调用 Poe API 与指定 Bot 对话
用法:
  uv run python poe_assistant.py --bot Gemini-2.5-Pro --message "你好"
"""

import argparse
import subprocess
import json
import time
import sys


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


def send_message(api_key: str, bot_name: str, message: str) -> str:
    """发送消息到 Poe，返回 message_id"""
    import urllib.request

    url = f"https://api.poe.com/bot/{bot_name}/send_message"
    data = f"message={urllib.parse.quote(message)}&bot_view={urllib.parse.quote(bot_name)}".encode()
    req = urllib.request.Request(
        url,
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
    import urllib.request

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
        # response 里有 messages 数组，找 text 类型的
        messages = result.get("messages", [])
        for msg in reversed(messages):
            if msg.get("message_type") == "assistant" and msg.get("content"):
                # 返回纯文本
                parts = msg["content"]
                for part in parts:
                    if part.get("__typename") == "Text":
                        return part["text"]
        time.sleep(1)
    raise TimeoutError(f"等待回复超时（{timeout}秒）")


def main():
    parser = argparse.ArgumentParser(description="Poe Assistant - 调用 Poe Bot 对话")
    parser.add_argument("--bot", default="Gemini-2.5-Pro", help="Bot 名称（如 Gemini-2.5-Pro）")
    parser.add_argument("--message", required=True, help="发给 Bot 的消息")
    args = parser.parse_args()

    api_key = get_api_key()
    print(f"[Poe] 正在发送消息到 {args.bot}...", file=sys.stderr)

    message_id = send_message(api_key, args.bot, args.message)
    reply = wait_for_response(api_key, args.bot, message_id)
    print(reply)


if __name__ == "__main__":
    main()
