"""
Agent orchestration loop.

Implements the core "agent loop":
  1. Accept user query
  2. Send to LLM with tool definitions (function calling)
  3. If the LLM calls a tool -> execute it -> feed result back
  4. Repeat until the LLM produces a final answer
"""

import json
import sys
from typing import List

from openai import OpenAI

from .config import get_settings
from .tools import TOOL_SCHEMAS, TOOL_DISPATCH

SYSTEM_PROMPT = """你是 PDF 助手，一个专门用于阅读、分析和总结 PDF 文档的 AI 智能代理。

你的能力：
1. 你可以逐页读取 PDF 文件，提取其中的文本内容。
2. 你可以在 PDF 中搜索关键词或主题。
3. 你可以获取 PDF 的元数据（页数、文件大小、作者等）。
4. 你可以列出目录中的所有 PDF 文件。

当用户让你总结一个 PDF 时：
1. 首先调用 get_pdf_info 了解文档的大小和范围。
2. 如果文档很短（<=5页），用 read_pdf 一次性读取全部内容。
3. 如果文档很长，分块读取（比如一次读 5-10 页），或者用 search_pdf 找到关键章节。
4. 综合所有信息，生成一份清晰、结构化的总结。

始终要全面深入，必要时多次调用工具。最终用中文回复用户。"""


def run_agent(user_query: str, max_turns: int = 15) -> str:
    """Run the PDF Summary Agent loop."""
    settings = get_settings()
    client = OpenAI(
        api_key=settings["api_key"],
        base_url=settings["base_url"],
    )
    model = settings["model"]

    messages: List[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_query},
    ]

    for turn in range(max_turns):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOL_SCHEMAS,
            temperature=settings["temperature"],
            max_tokens=settings["max_tokens"],
        )

        choice = response.choices[0]
        msg = choice.message

        if not msg.tool_calls:
            return msg.content or "(no response)"

        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in msg.tool_calls
            ],
        })

        for tc in msg.tool_calls:
            func_name = tc.function.name
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}

            handler = TOOL_DISPATCH.get(func_name)
            if not handler:
                result = f"[Error] Unknown tool: {func_name}"
            else:
                try:
                    result = handler(**args)
                except Exception as e:
                    result = f"[Error] Tool {func_name}: {e}"

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result if isinstance(result, str) else json.dumps(result),
            })

    return ("[Warning] Reached maximum turn limit. "
            "Partial results:\n\n" + _truncate_messages(messages))


def _truncate_messages(messages: List[dict]) -> str:
    """Extract key info from accumulated tool results."""
    parts = []
    for m in messages:
        if m["role"] == "tool" and m.get("content"):
            txt = m["content"]
            if len(txt) > 500:
                txt = txt[:500] + "..."
            parts.append(txt)
    return "\n\n".join(parts[-5:]) if parts else "(no data)"


def interactive_session():
    """Run an interactive REPL session with the agent."""
    print("=" * 60)
    print("  PDF 总结助手 - 交互模式")
    print("  输入你的查询，输入 'exit' 退出。")
    print("=" * 60)
    print()

    while True:
        try:
            query = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not query:
            continue
        if query.lower() in ("exit", "quit", "q"):
            print("Goodbye!")
            break

        print("\nAgent is thinking...")
        try:
            result = run_agent(query)
            print(f"\nAssistant:\n{result}\n")
        except Exception as e:
            print(f"\n[Error] {e}\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(run_agent(query))
    else:
        interactive_session()
