# ローカルAIチャット — 社内ファイルを触れるAIアシスタント

**会社のPCの中だけで動く、ファイルを「読む・探す・直す」AI。** ChatGPTのような画面で使えます。
入力した内容やファイルは **外部（インターネット）に送られません**。AIも検索も全部このPC/サーバーの中で完結します。

> ひとことで言うと：**社外に出せないデータでも安心して使える、自前のChatGPT**です。

---

# 👤 はじめての方へ（非エンジニア向け・まずここだけ）

## これは何がうれしいの？

- 世の中のAIサービス（ChatGPTやCopilotなど）は、質問やファイルを **その会社のサーバーに送って** 処理します。
- このツールは **AIまるごと自分のPC/社内サーバーに置く** ので、データが外に出ません。
- しかも、ただ会話するだけでなく **指定したフォルダのファイルを読んだり・検索したり・書き換えたり** できます。

## 仕組み（ざっくり3つの部品）

```
  あなた ──▶  ［チャット画面］ ──▶ ［AI本体］
                    │                （Ollama＝ローカルAI）
                    ▼
              ［ファイル係］ ──▶ 指定フォルダの中だけを操作
              （読む・探す・直す）
```

- **チャット画面**（Open WebUI）… ブラウザで使うChatGPT風の画面
- **AI本体**（Ollama）… ネットにつながず動くAI
- **ファイル係**（MCPサーバー）… AIの代わりにフォルダを触る係。触れる範囲は決めたフォルダの中だけ。

この3つを、下の手順で **まとめて一発で立ち上げられる** ようにしてあります。

---

## 1. 準備するもの（1つだけ）

**Docker Desktop**（無料）をインストールするだけです。
→ https://www.docker.com/products/docker-desktop/

- インストールしたら **Docker Desktop を起動**しておいてください（クジラのアイコンが出ればOK）。
- 目安：メモリ8GB以上のPCを推奨。AIモデルのダウンロードで数GBの通信・空き容量が必要です。

## 2. 起動する

- **Windowsの人**：`start.bat` を **ダブルクリック**。
- **Mac / Linuxの人**：ターミナルでこのフォルダに入って `docker compose up -d`。

しばらく待つと、ブラウザで **http://localhost:3000** が開きます（自動で開かなければ手で開いてください）。
最初に **アカウント作成** の画面が出ます。名前・メール・パスワードを入れて登録してください。
（これは **このPCの中だけの登録** で、どこにも送信されません。最初に登録した人が管理者になります。）

## 3. 最初の1回だけの準備

初回だけ、2つの設定をします。（2回目以降は不要です）

### (A) AIモデルを取り込む
AIの「頭脳」にあたるデータをダウンロードします。
- **Windows**：`pull-model.bat` を **ダブルクリック**（数GB・少し時間がかかります）。
- 手動でやる場合：`docker compose exec ollama ollama pull qwen2.5:7b`

> `qwen2.5:7b` はファイル操作（ツール使用）が得意なモデルです。まずはこれで。

### (B) ファイルを触れるようにする（ツール接続）
チャット画面の **設定（Settings）→ ツール（Tools／外部ツール）** を開き、
**「＋（サーバーを追加）」** から次のアドレスを入力して保存します：

```
http://mcpo:8000
```

> うまくつながらない場合は `http://localhost:8000` を試してください。

これで、AIがファイル係を呼び出せるようになります。

## 4. 使ってみる

チャット画面の上で **モデルに `qwen2.5:7b` を選び**、メッセージ欄の **ツール（レンチ／＋アイコン）をオン**にして、話しかけます。
最初は付属の「サンプル」フォルダで試せます：

- 「**sample プロジェクトのファイル一覧を見せて**」
- 「**hello.py を読んで、greet 関数の挨拶を英語に直して**」
- 「**経費の申請期限は？**」（← 付属の資料を検索して答えます）

うまくいくと、AIが裏でファイルを開いたり書き換えたりして返事します。

> **モデル選びのめやす**：まずは `qwen2.5:7b`（軽くてツール操作が安定）。ファイルの読み取り・検索は得意です。
> 複雑な複数手順の編集をもっと安定させたい場合はより大きいモデル（例 `qwen2.5:14b`）も使えますが、
> 大きいモデルは **新しめのGPUドライバが必要**なことがあります（古いと起動時にエラーになる）。
> GUIならモデルは画面上でいつでも切り替えられるので、まず7bで試すのがおすすめです。

## 5. 自分の会社のファイルで使う

`workspace` フォルダが、AIが触れる範囲です。中は2つに分かれています：

| フォルダ | 役割 | 入れるもの |
|---|---|---|
| `workspace/apps/` | **編集してほしいファイル** | プログラム、原稿、設定ファイルなど |
| `workspace/docs/` | **検索したい資料** | 規程、マニュアル、PDF、議事録など |

- それぞれの中に **プロジェクト名のフォルダ**（例：`workspace/apps/keiri/…`）を作って入れてください。
- 別の場所のフォルダをまるごと使いたい場合は、`docker-compose.yml` の `./workspace` を
  そのフォルダのパスに書き換えます（分からなければエンジニアに依頼を）。
- 書き換え前のファイルは自動で `.backups` に退避されますが、**大事なデータは別途バックアップ**を取ってください。

## 6. 終了 / 再開

- **終了**：`stop.bat` をダブルクリック（または `docker compose down`）。
- **再開**：`start.bat`。会話履歴も取り込んだモデルも残っています。

## 7. 困ったとき

| こまりごと | 対処 |
|---|---|
| 画面が開かない | Docker Desktop が起動しているか確認 → もう一度 `start.bat` |
| AIがファイルを触ってくれない | モデルが `qwen2.5:7b` か確認 / 手順3(B)のツール接続ができているか / メッセージ欄でツールをオンに |
| ツール接続がつながらない | URLを `http://localhost:8000` に変えて再登録 |
| 返事が遅い | 初回はモデル読み込みで遅い。PCの性能にも依存します |
| 返事が文字化けする・急に不安定 | 一度 **Ollama を再起動**（大きいモデルがGPUでクラッシュした後などに起きることあり）。その後は軽いモデル(`qwen2.5:7b`)で |
| 大きいモデルが起動時にエラー(CUDA等) | GPUドライバ/Ollamaを最新に更新するか、`qwen2.5:7b` を使う |
| 「経費は？」等で資料が出ない | 会話で「資料を読み込み直して」と頼む（インデックス更新が走ります） |

---

# 🛠 開発者向け（技術詳細）

## アーキテクチャ

```
[ユーザー] → [Open WebUI(GUI)] → [Ollama(ローカルLLM)]
                   │  OpenAPI(tool)
                   ▼
              [mcpo] ──stdio──> [unified_mcp_server.py (MCPサーバー/ツール群)]
                                        │
                                        ▼
                                 workspace/ (apps=編集 / docs=RAG)
```

- **`unified_mcp_server.py`** … ツールを公開する **MCPサーバー**。自分ではLLM APIを呼ばない（埋め込み=RAGもローカル計算）。
- **`mcpo`** … MCPサーバーを **OpenAPI** に変換し、Open WebUI から呼べるようにする橋渡し。
- **`ollama_agent.py`** … GUIを使わず **CLIでツールを回す**開発用ホスト（Open WebUIの代わり）。
- 「どのLLMを使うか」を決めるのは接続する側。**Claude Desktop から使うことも可能**（後述）。

## 起動モードまとめ

| 目的 | コマンド |
|---|---|
| GUI（ブラウザ）で使う | `docker compose up -d` → http://localhost:3000 |
| CLIで使う（開発用） | `docker compose run --rm agent` |
| Dockerなしローカル実行 | 下記「ローカル実行」 |

## ローカル実行（Dockerなし）

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate  /  macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# 前提: ollama serve が起動し、tool対応モデルを pull 済み（例: ollama pull qwen2.5:7b）
python ollama_agent.py                       # 対話
python ollama_agent.py --once "sampleの一覧"   # 単発

# GUIを使いたい場合（mcpo単体起動）:
mcpo --port 8000 -- python unified_mcp_server.py
```

## Claude Desktop から使う（Ollama不要）

`claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "unified-mcp": {
      "command": "python",
      "args": ["/absolute/path/to/unified_mcp_server.py"],
      "env": { "WORKSPACE_ROOT": "/path/to/workspace", "ENABLE_RAG": "1" }
    }
  }
}
```

## 設定（環境変数 / .env）

| 変数 | 既定 | 説明 |
|---|---|---|
| `WORKSPACE_ROOT` | `./workspace` | 触らせるフォルダ。直下に `apps/` と `docs/` |
| `CHROMA_DB_DIR` | `<root>/.chroma_db` | ベクタDBの保存先 |
| `ENABLE_RAG` | `1` | `0` で意味検索を無効化（重い依存を読み込まない） |
| `EMBED_MODEL` | `intfloat/multilingual-e5-large` | 埋め込みモデル |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollamaのendpoint（Docker内は `http://ollama:11434`） |
| `OLLAMA_MODEL` | `qwen2.5:7b` | 使うローカルモデル（tool対応必須） |
| `MAX_TOOL_ITERATIONS` | `12` | 1発話あたりのツール呼び出し上限 |
| `WORKSPACE_CONFIG` | `./workspace_config.json` | 追加設定JSON（任意） |

`workspace_config.json`（任意）で `apps_only_projects`（RAG不要プロジェクト）と
`extra_rag_paths`（docs以外の追加RAG対象）を指定できます。

## 提供ツール一覧

- ファイル操作: `list_projects` `list_files` `read_file` `read_file_lines` `write_file` `patch_file` `search_in_files`
- 意味検索(RAG): `search_docs` `read_document` `read_pages` `list_docs` `refresh_database` `check_update_status`
- コード解析(tree-sitter): `find_symbol` `find_references` `read_symbol` `index_symbols`（MATLAB追加のみ `requirements-symbols.txt`）
- 検証: `list_checks` `run_check`（`mcp_checks.json` で定義したコマンドのみ実行可）

## ツールを増やす

`unified_mcp_server.py` に関数を足して `@mcp.tool()` を付けるだけ。docstringと型ヒントがそのまま
LLM向けの説明・引数スキーマになります。**GUI(mcpo経由)・CLI・Claude Desktop の全部に自動反映**されます。

```python
@mcp.tool()
def word_count(project: str, filepath: str) -> str:
    """指定ファイルの単語数を返す。"""
    root, target = _resolve_apps(project, filepath)   # rootの外へ出さない安全解決
    text, err = extract_text(str(target))
    return err or json.dumps({"words": len(text.split())}, ensure_ascii=False)
```

## セキュリティ設計

- **外部送信なし**：LLMも埋め込みもローカル。データは `WORKSPACE_ROOT` の外に出ない。
- **パス閉じ込め**：全ツールが root 配下に解決を強制（`../` 脱出を拒否）。
- **秘密の保護**：`.env*` は読み取り・検索の対象外。
- **編集の可逆性**：`write_file`/`patch_file` は `.backups/` に自動退避してから書く。
- **任意コマンド実行なし**：`run_check` は `mcp_checks.json` の事前定義コマンドのみ。

## フォルダ構成

```
localllm-MCP/
├─ start.bat / start.sh / stop.bat / pull-model.bat   # 非エンジニア向けワンクリック
├─ docker-compose.yml         # ollama + mcpo + open-webui (+ 開発用agent)
├─ Dockerfile
├─ unified_mcp_server.py      # MCPサーバー本体（ツール群）
├─ ollama_agent.py            # CLIホスト（開発用）
├─ workspace/                 # 触らせる対象（サンプル同梱）
│  ├─ apps/sample/            #   編集対象
│  └─ docs/sample/            #   RAG対象
├─ requirements.txt / requirements-symbols.txt
├─ .env.example / workspace_config.json.example
└─ README.md
```

---

_既存の社内向けMCPサーバー（特定フォルダの編集＋ローカルRAG）を、ハードコードを排して環境変数化し、
ローカルLLM(Ollama)・GUI(Open WebUI)・Docker・非エンジニア向け手順を付けて配布可能にしたものです。_
