"""
ollama_agent.py — ローカルLLM（Ollama）で unified-mcp のツールを使う「AI社員」ホスト

このファイルが、とも が言っていた「MCPサーバーを Ollama に向けたファイル一式」の中核。
やっていること:

    [あなた] → Ollama(ローカルLLM) → ツール呼び出し → unified_mcp_server のツール
              ↑ 完全ローカル・外部API不要（社内完結）

- 外部クラウド/外部APIは一切呼ばない。LLM は Ollama（ローカル）、埋め込みもローカル。
- unified_mcp_server の @mcp.tool() をそのまま関数として Ollama に渡すので、
  ツールを増やしたら Claude Desktop でも Ollama でも同時に使える。

使い方:
    python ollama_agent.py                     # 対話モード(REPL)
    python ollama_agent.py --once "質問文"      # 1回だけ実行して終了
    OLLAMA_MODEL=qwen2.5:7b python ollama_agent.py

必要な準備:
    1. Ollama を起動: `ollama serve`（デフォルト http://localhost:11434）
    2. tool 対応モデルを取得: `ollama pull qwen2.5:7b`（llama3.1 / mistral-nemo でも可）
    3. `pip install -r requirements.txt`
"""

import os
import sys
import json
import asyncio
import argparse

# unified-mcp サーバー本体（同じリポジトリ内）からツール定義を借りる
from unified_mcp_server import mcp, MCP_ROOT, ENABLE_RAG

try:
    from ollama import AsyncClient
except ImportError:
    print(
        "❌ `ollama` パッケージが未インストールです。\n"
        "   pip install ollama  を実行してください。",
        file=sys.stderr,
    )
    sys.exit(1)


# ========================================================
# 設定（すべて環境変数で上書き可能）
# ========================================================

OLLAMA_HOST  = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")
MAX_TOOL_ITERATIONS = int(os.environ.get("MAX_TOOL_ITERATIONS", "12"))

SYSTEM_PROMPT = f"""あなたは社内ファイルを扱う「AIアシスタント（AI社員）」です。
作業対象フォルダは {MCP_ROOT} 配下（apps=編集対象 / docs=意味検索対象）に限定されています。

ルール:
- ファイルの閲覧・検索・編集は必ず提供ツールを使うこと（推測で答えない）。
- どのツールも project 引数が必要。最初に list_projects() で利用可能なプロジェクト名を確認してから使うこと。
- 大きなファイルは read_file より、find_symbol → read_symbol / read_file_lines で必要箇所だけ読むと効率的。
- 意味検索(RAG)は search_docs、キーワード一致は search_in_files を使い分ける。
- 編集は write_file（全文）より patch_file（差分）を優先。変更後は必要に応じ run_check で検証する。
- 回答は日本語で簡潔に。何をしたか（呼んだツール名）も一言添える。
RAG(意味検索)は {'有効' if ENABLE_RAG else '無効'}。"""


# ========================================================
# MCPツール → Ollama(OpenAI互換) tool スキーマ変換
# ========================================================

async def build_ollama_tools() -> tuple[list[dict], set[str]]:
    """unified_mcp_server の全ツールを Ollama の tools 形式に変換する。"""
    mcp_tools = await mcp.list_tools()
    tools = []
    names = set()
    for t in mcp_tools:
        schema = t.inputSchema or {"type": "object", "properties": {}}
        tools.append({
            "type": "function",
            "function": {
                "name": t.name,
                "description": (t.description or "").strip(),
                "parameters": schema,
            },
        })
        names.add(t.name)
    return tools, names


def _normalize_tool_result(result) -> str:
    """FastMCP.call_tool の戻り値を、バージョン差異を吸収してテキスト化する。"""
    # 新しめの mcp SDK は (content_blocks, structured) のタプルを返す
    if isinstance(result, tuple):
        result = result[0]
    # content_blocks は TextContent 等のリスト
    if isinstance(result, list):
        parts = []
        for block in result:
            text = getattr(block, "text", None)
            if text is not None:
                parts.append(text)
            elif isinstance(block, dict) and "text" in block:
                parts.append(block["text"])
            else:
                parts.append(str(block))
        return "\n".join(parts)
    return str(result)


async def call_mcp_tool(name: str, arguments: dict) -> str:
    """MCPツールを実行して結果テキストを返す。"""
    try:
        result = await mcp.call_tool(name, arguments or {})
        return _normalize_tool_result(result)
    except Exception as e:  # ツール側の想定外例外もLLMに返して自己修正させる
        return f"❌ tool '{name}' の実行でエラー: {e}"


# ========================================================
# 会話ループ（tool-calling）
# ========================================================

async def run_turn(client: "AsyncClient", messages: list[dict], tools: list[dict], names: set[str]) -> str:
    """1ユーザー発話に対し、必要な回数ツールを呼びながら最終回答を得る。"""
    for _ in range(MAX_TOOL_ITERATIONS):
        resp = await client.chat(model=OLLAMA_MODEL, messages=messages, tools=tools)
        msg = resp["message"]

        tool_calls = msg.get("tool_calls") or []
        # assistant のメッセージを履歴へ（tool_calls 情報も含めて渡す）
        messages.append({
            "role": "assistant",
            "content": msg.get("content", "") or "",
            "tool_calls": tool_calls,
        })

        if not tool_calls:
            return msg.get("content", "") or "(空の応答)"

        # 呼ばれた各ツールを実行し、結果を tool ロールで返す
        for tc in tool_calls:
            fn = tc["function"]
            name = fn["name"]
            raw_args = fn.get("arguments", {})
            # arguments は dict のことも JSON文字列のこともある
            if isinstance(raw_args, str):
                try:
                    args = json.loads(raw_args) if raw_args.strip() else {}
                except json.JSONDecodeError:
                    args = {}
            else:
                args = dict(raw_args)

            if name not in names:
                out = f"❌ 未知のツール: {name}"
            else:
                print(f"   🔧 {name}({json.dumps(args, ensure_ascii=False)})", file=sys.stderr)
                out = await call_mcp_tool(name, args)

            messages.append({"role": "tool", "name": name, "content": out})

    return "⚠️ ツール呼び出しが上限に達しました。質問を分割してもう一度試してください。"


async def main_async(once: str | None):
    client = AsyncClient(host=OLLAMA_HOST)
    tools, names = await build_ollama_tools()

    print(f"● Ollama host: {OLLAMA_HOST}  model: {OLLAMA_MODEL}", file=sys.stderr)
    print(f"● workspace  : {MCP_ROOT}", file=sys.stderr)
    print(f"● tools ready: {len(tools)} 個  ({', '.join(sorted(names))})", file=sys.stderr)

    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

    if once is not None:
        messages.append({"role": "user", "content": once})
        answer = await run_turn(client, messages, tools, names)
        print(answer)
        return

    print("\n対話モード（'exit' / 'quit' で終了）\n")
    while True:
        try:
            user = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user:
            continue
        if user.lower() in ("exit", "quit", ":q"):
            break
        messages.append({"role": "user", "content": user})
        answer = await run_turn(client, messages, tools, names)
        print(f"\nai > {answer}\n")


def main():
    parser = argparse.ArgumentParser(description="Ollama × unified-mcp ローカルAIエージェント")
    parser.add_argument("--once", metavar="PROMPT", help="1回だけ実行して終了")
    args = parser.parse_args()
    try:
        asyncio.run(main_async(args.once))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
