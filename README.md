# unified-mcp + Ollama ローカルAIエージェント

**社内フォルダを読み書き・検索・編集できる「AI社員」を、外部API・外部クラウドなしで動かす一式。**
LLM は Ollama（ローカル）、意味検索（RAG）の埋め込みもローカル。データは指定フォルダの外に出ません。

Claude Desktop などの MCP クライアントからそのまま使うことも、Ollama で完全ローカルに回すこともできます。

---

## 1. これは何か / 何が「ローカル完結」なのか

このリポジトリは **2つのピース** でできています。

```
 [あなた/社員]
      │  自然言語で依頼
      ▼
 ┌─────────────────────┐        ┌──────────────────────────────┐
 │  LLMホスト           │  tool  │  unified_mcp_server.py        │
 │  ollama_agent.py     │──呼出─▶│  (MCPサーバー: ツールの集合)   │
 │  = Ollama を叩く      │◀─結果─ │  list/read/write/patch/search │
 └─────────────────────┘        │  search_docs(RAG)/symbol/check│
      │                          └──────────────┬───────────────┘
      ▼ ローカルLLM                              ▼
   Ollama(11434)                          workspace/（指定フォルダのみ）
                                            ├─ apps/<project>  … 編集対象
                                            └─ docs/<project>  … RAG対象
```

**重要な設計ポイント（誤解しやすい所）:**

- `unified_mcp_server.py` は **「ツールを公開するMCPサーバー」であって、自分ではどのLLM APIも呼びません。**
  埋め込み（意味検索）も `sentence-transformers` によるローカル計算です。
- 「LLMをどれにするか」を決めるのは **接続してくる側（ホスト）**。
  - **Ollama で完結したい** → 本リポの `ollama_agent.py` を使う（＝このファイル一式）。
  - **Claude Desktop で使いたい** → 同じサーバーをそのまま MCP サーバー登録すればよい（後述）。
  - **M365 Copilot** で使いたい → 消費者版Copilotには挿せない。Copilot Studio（MCP対応）にコネクタ登録する別ルートになる。
- したがって外部API・外部クラウドは経路に一切登場しません。**社内完結**です。

---

## 2. クイックスタート（ローカル / Python）

### 前提
- Python 3.12
- [Ollama](https://ollama.com/) をインストールして起動（`ollama serve`、既定 `http://localhost:11434`）
- tool 対応モデルを1つ取得（例）:
  ```bash
  ollama pull qwen2.5:7b       # tool-calling が安定。llama3.1:8b / mistral-nemo でも可
  ```

### セットアップ
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    /    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                 # 必要なら編集（モデル名・作業フォルダ等）
```

### 動かす
```bash
# 対話モード
python ollama_agent.py

# 1回だけ実行（動作確認）
python ollama_agent.py --once "sample プロジェクトのファイル一覧を見せて"
python ollama_agent.py --once "hello.py の greet 関数を読んで"
```

初回は `refresh_database()` を一度走らせると RAG が使えるようになります（対話中に
「RAGのインデックスを更新して」と頼めば `refresh_database` ツールが呼ばれます）。

---

## 3. クイックスタート（Docker / 完全自己完結）

Ollama ごとコンテナで立てるので、ホストに何も入れなくても動きます。

```bash
# 1) Ollama を起動
docker compose up -d ollama

# 2) モデルを取得（初回のみ・数GB）
docker compose exec ollama ollama pull qwen2.5:7b

# 3) エージェントに接続（対話）
docker compose run --rm agent

#    1回だけ実行する場合:
docker compose run --rm agent python ollama_agent.py --once "sampleのファイル一覧を見せて"
```

自分のデータで使うときは `docker-compose.yml` の `agent.volumes` の
`./workspace` をホスト側の実フォルダに差し替えてください（`apps/` と `docs/` の2階層構成にする）。

> torch(CPU版) を含むためイメージは大きめ（数GB）。GPUを使う場合は `ollama` サービスに
> GPU予約を追加し、`EMBED_MODEL` のGPU利用は別途調整してください。

---

## 4. Claude Desktop から使う場合（Ollama不要）

同じ `unified_mcp_server.py` を MCP サーバーとして登録するだけ。`claude_desktop_config.json` に:

```json
{
  "mcpServers": {
    "unified-mcp": {
      "command": "python",
      "args": ["C:/path/to/MCP-server/unified_mcp_server.py"],
      "env": {
        "WORKSPACE_ROOT": "C:/path/to/your/workspace",
        "ENABLE_RAG": "1"
      }
    }
  }
}
```

この場合ツールを使う「頭脳」は Claude 側になります（ローカルにしたいなら §2/§3）。

---

## 5. 設定（環境変数 / .env）

| 変数 | 既定 | 説明 |
|---|---|---|
| `WORKSPACE_ROOT` | `./workspace` | 触らせるフォルダのルート。直下に `apps/` と `docs/` を置く |
| `CHROMA_DB_DIR` | `<root>/.chroma_db` | ベクタDBの保存先 |
| `ENABLE_RAG` | `1` | `0` で意味検索を無効化（重い依存を読み込まない） |
| `EMBED_MODEL` | `intfloat/multilingual-e5-large` | 埋め込みモデル |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama のエンドポイント |
| `OLLAMA_MODEL` | `qwen2.5:7b` | 使うローカルモデル（tool対応必須） |
| `MAX_TOOL_ITERATIONS` | `12` | 1発話あたりのツール呼び出し上限 |
| `WORKSPACE_CONFIG` | `./workspace_config.json` | 追加設定JSONのパス（任意） |

`workspace_config.json`（任意・`.example` をコピー）で以下を指定できます:
- `apps_only_projects`: RAG不要（appsのみ）のプロジェクト名
- `extra_rag_paths`: `docs/` 以外も追加でRAG対象にするパス

---

## 6. フォルダ構成

```
MCP-server/
├─ unified_mcp_server.py     # MCPサーバー本体（ツール群。Claude Desktopでも使える）
├─ ollama_agent.py           # Ollamaホスト（ローカルLLMでツールを回すエージェント）
├─ workspace/                # 触らせる対象（サンプル同梱。実データに差し替え可）
│  ├─ apps/sample/           #   編集対象プロジェクト（hello.py, mcp_checks.json）
│  └─ docs/sample/           #   RAG対象ドキュメント（welcome.md）
├─ requirements.txt          # コア + RAG 依存
├─ requirements-symbols.txt  # tree-sitter（シンボル解析・任意）
├─ Dockerfile / docker-compose.yml
├─ .env.example / workspace_config.json.example
└─ README.md
```

---

## 7. 提供ツール一覧

`ollama_agent.py` 起動時、これらが自動で Ollama に渡ります（Claude Desktop でも同じ）。

**ファイル操作（apps）**
- `list_projects` / `list_files` … プロジェクト・ファイル一覧
- `read_file` / `read_file_lines` … 読み取り（全文 / 行範囲）
- `write_file` / `patch_file` … 書き込み（全文 / 差分。自動バックアップ）
- `search_in_files` … キーワード grep

**意味検索（docs / RAG）**
- `search_docs` … 自然言語での意味検索
- `read_document` / `read_pages` … 文書全文 / PDFページ範囲
- `list_docs` / `refresh_database` / `check_update_status` … インデックス管理

**コード解析（tree-sitter・任意）**
- `find_symbol` / `find_references` / `read_symbol` / `index_symbols`

**検証**
- `list_checks` / `run_check` … `mcp_checks.json` で定義したコマンド（lint/test/build等）を実行

---

## 8. 拡張のしかた（＝これを土台に増やす）

ツールを1つ足すには、`unified_mcp_server.py` に関数を書いて `@mcp.tool()` を付けるだけ。
**Ollama側・Claude Desktop側の両方に自動で反映されます**（`ollama_agent.py` は起動時に
`mcp.list_tools()` でツールを取得して Ollama に渡すため、ホスト側の改修は不要）。

```python
@mcp.tool()
def word_count(project: str, filepath: str) -> str:
    """指定ファイルの単語数を返す。"""
    root, target = _resolve_apps(project, filepath)  # 既存ヘルパで安全にパス解決
    text, err = extract_text(str(target))
    if err:
        return f"❌ {err}"
    return json.dumps({"words": len(text.split())}, ensure_ascii=False)
```

- 関数の **docstring と型ヒント** がそのままツールの説明・引数スキーマになる（LLMが読む）。
- パスは必ず `_resolve_apps` / `_resolve_docs` を通す（`WORKSPACE_ROOT` の外に出さないため）。
- `.env` 系ファイルは `_is_sensitive_file` で読み取り禁止済み。

---

## 9. セキュリティ / 設計メモ

- **外部送信なし**: LLMも埋め込みもローカル。データは `WORKSPACE_ROOT` の外に出ない。
- **パス閉じ込め**: 全ツールが root 配下に解決を強制（`../` 脱出を拒否）。
- **秘密の保護**: `.env*` は読み取り・検索の対象外。
- **編集の可逆性**: `write_file` / `patch_file` は `.backups/` に自動退避してから書く。
- **任意コマンド実行はしない**: `run_check` はプロジェクト同梱 `mcp_checks.json` に
  事前定義されたコマンドのみ実行（LLMが任意シェルを叩けない）。

---

## 10. トラブルシューティング

| 症状 | 対処 |
|---|---|
| `ollama` パッケージが無い | `pip install -r requirements.txt` |
| モデルが tool を呼ばない | tool対応モデルを使う（`qwen2.5:7b` 推奨）。`ollama list` で取得済み確認 |
| RAG系ツールがエラー | `ENABLE_RAG=1` かつ `pip install chromadb sentence-transformers`。初回は `refresh_database` |
| PDFが読めない | `pip install pymupdf` |
| `find_symbol` が使えない | `pip install -r requirements-symbols.txt`（任意機能） |
| Docker で Ollama に繋がらない | `OLLAMA_HOST=http://ollama:11434`（compose内サービス名）になっているか |

---

_この一式は既存の `unified_mcp_server.py`（特定ディレクトリの編集＋ローカルRAG）を、
ハードコードを排して環境変数化し、Ollama ホストと Docker/README を付けて配布可能にしたもの。_
